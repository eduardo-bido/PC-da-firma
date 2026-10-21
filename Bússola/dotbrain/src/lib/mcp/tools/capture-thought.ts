import { defineTool, ToolError } from "@lovable.dev/mcp-js";
import { z } from "zod";
import { supabaseForUser } from "../supabase";
import { sliceIntoBlocks } from "../../longform.server";
import { episodeV2Metadata, sameEpisodeV2 } from "./episode-v2";

/**
 * A capture creates one immutable raw episode first. Enrichment is queued,
 * not claimed as completed. Source-of-truth remains public.thoughts.
 * No service-role credentials are needed; all writes run under OAuth + RLS.
 */
export default defineTool({
  name: "capture_thought",
  title: "Save context to Dot",
  description:
    "Store a user-authorized decision, observation, plan, preference or conversation summary in Dot's original memory. " +
    "Retain its exact wording. Create only when the user requests or has explicitly authorized capture. " +
    "Enrichment into facts, entities and graph relations happens asynchronously; do not claim immediate inference.",
  inputSchema: {
    content: z.string().trim().min(1).max(20000).describe(
      "Original factual content, concise structured summary, or user-provided text to remember. " +
      "Do not invent events, moods, achievements, or dates.",
    ),
    processing_mode: z.enum(["semantic_only", "full"]).default("semantic_only").describe(
      "semantic_only (default) stores searchable embeddings without expensive LLM entity/task/calendar/finance extraction. " +
      "full explicitly requests graph extraction and may create suggestions.",
    ),
    request_id: z.string().uuid().optional().describe(
      "Optional UUID for this intended capture. Reuse it ONLY when retrying the same capture after a timeout.",
    ),
    episode: z.strictObject({
      source_reference: z.string().min(1).max(500),
      occurred_at: z.string().max(40).nullable(),
      time_precision: z.enum(["day", "month", "year", "unknown"]),
      knowledge_kind: z.enum(["fact", "decision", "intention", "outcome", "preference", "hypothesis", "observation"]),
      epistemic_status: z.enum(["user_confirmed", "quoted", "reported", "inferred", "unknown"]),
      temporal_status: z.enum(["current", "historical", "future", "uncertain"]),
      privacy: z.literal("standard"),
    }).optional().describe(
      "V2 raw episode metadata. Requires request_id and semantic_only. Restricted content is not accepted until access controls exist. No graph promotion or external action occurs."
    ),
  },
  annotations: { readOnlyHint: false, destructiveHint: false, openWorldHint: false },
  handler: async ({ content, request_id, processing_mode, episode }, ctx) => {
    if (!ctx.isAuthenticated()) throw new ToolError("Not authenticated");
    const userId = ctx.getUserId();
    if (!userId) throw new ToolError("Missing authenticated user");
    const supabase = supabaseForUser(ctx);
    const source = "chatgpt";
    if (episode && processing_mode !== "semantic_only") {
      throw new ToolError("V2 episodes support semantic_only processing only");
    }
    let episodeMetadata: ReturnType<typeof episodeV2Metadata> | undefined;
    try {
      episodeMetadata = episode ? episodeV2Metadata(episode, request_id) : undefined;
    } catch (error) {
      throw new ToolError(error instanceof Error ? error.message : "Invalid V2 episode");
    }

    const { data: inserted, error: insertError } = await supabase.from("thoughts").insert({
      ...(request_id ? { id: request_id } : {}),
      user_id: userId,
      content,
      source,
      doc_map: { bussola: { processing_mode, ...(episodeMetadata ? { episode_v2: episodeMetadata } : {}) } },
    }).select("id, source, created_at").single();

    let thought = inserted;
    let replayed = false;
    if (insertError?.code === "23505" && request_id) {
      const previous = await supabase.from("thoughts")
        .select("id, content, source, created_at, doc_map")
        .eq("user_id", userId)
        .eq("id", request_id)
        .maybeSingle();
      if (previous.error || !previous.data) throw new ToolError("Could not verify a repeated capture");
      if (previous.data.content !== content || previous.data.source !== source ||
        (previous.data.doc_map as any)?.bussola?.processing_mode !== processing_mode ||
        !sameEpisodeV2((previous.data.doc_map as any)?.bussola?.episode_v2, episodeMetadata)) {
        throw new ToolError("request_id belongs to a different memory; provide a new UUID");
      }
      thought = previous.data;
      replayed = true;
    } else if (insertError) {
      throw new ToolError("Could not save the thought");
    }
    if (!thought) throw new ToolError("Could not identify the saved thought");

    // Repairable on retries: upsert on the existing (thought_id, pos) unique index.
    const pieces = sliceIntoBlocks(content);
    const blockRows = pieces.map((part, pos) => ({
      thought_id: thought.id,
      user_id: userId,
      pos,
      content: part,
      relevance: 0.5,
    }));
    const blocksUpsert = await supabase.from("thought_blocks")
      .upsert(blockRows, { onConflict: "thought_id,pos", ignoreDuplicates: true });
    if (blocksUpsert.error) throw new ToolError(
      "Memory saved, but block preparation failed. Retry with the same request_id.",
    );

    const { data: blocks, error: blocksError } = await supabase.from("thought_blocks")
      .select("id, pos")
      .eq("user_id", userId)
      .eq("thought_id", thought.id)
      .order("pos", { ascending: true });
    if (blocksError || !blocks || blocks.length !== pieces.length) {
      throw new ToolError("Memory saved, but blocks were incomplete. Retry using the same request_id.");
    }

    // Avoid unnecessary requeueing when the thought is retried. Do not touch
    // existing jobs (pending/processing/done/error), which preserve audit data.
    const blockIds = blocks.map((b) => b.id);
    const { data: existingJobs, error: queueLookupError } = await supabase.from("block_queue")
      .select("block_id")
      .eq("user_id", userId)
      .in("block_id", blockIds);
    if (queueLookupError) throw new ToolError(
      "Memory saved, but processing queue could not be verified. Retry with the same request_id.",
    );
    const scheduled = new Set((existingJobs ?? []).map((r) => r.block_id));
    const newJobs = blockIds.filter((id) => !scheduled.has(id)).map((block_id) => ({
      block_id, user_id: userId, status: "pending",
    }));
    if (newJobs.length) {
      // block_queue is SELECT-only under user RLS by design.
      // Enqueue through a server-only writer AFTER verifying OAuth ownership.
      const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
      const queued = await supabaseAdmin.from("block_queue").insert(newJobs);
      if (queued.error) throw new ToolError(
        "Memory saved, but processing could not be queued. Retry with the same request_id.",
      );
    }

    const payload = {
      saved: true,
      thought_id: thought.id,
      source: thought.source,
      created_at: thought.created_at,
      blocks: blocks.length,
      newly_queued: newJobs.length,
      replayed,
      processing_mode,
      episode_version: episodeMetadata?.version ?? null,
      processing_status: "queued_or_previously_scheduled",
      note: processing_mode === "semantic_only"
        ? "Original text saved. The fast worker generates embeddings but will not extract facts, entities, tasks or calendar events."
        : "Original text saved. Full extraction of facts, entities and suggestions requires processing queued blocks.",
    };
    return {
      content: [{ type: "text", text: JSON.stringify(payload) }],
      structuredContent: payload,
    };
  },
});

