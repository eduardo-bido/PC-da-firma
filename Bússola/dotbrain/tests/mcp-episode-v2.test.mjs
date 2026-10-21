import test from "node:test";
import assert from "node:assert/strict";
import { episodeV2Metadata, sameEpisodeV2 } from "../src/lib/mcp/tools/episode-v2.ts";

const episode = {
  source_reference: "conversation/abc/message/def",
  occurred_at: null,
  time_precision: "unknown",
  knowledge_kind: "decision",
  epistemic_status: "user_confirmed",
  temporal_status: "current",
  privacy: "standard",
};

test("V2 retains provenance and epistemic state without creating a claim", () => {
  assert.deepEqual(episodeV2Metadata(episode, "same-request"), {
    version: 2,
    source: { system: "chatgpt", reference: episode.source_reference },
    occurred_at: null,
    time_precision: "unknown",
    knowledge_kind: "decision",
    epistemic_status: "user_confirmed",
    temporal_status: "current",
    privacy: "standard",
    promotion_status: "raw_only",
  });
});

test("V2 requires a stable replay key and coherent event date", () => {
  assert.throws(() => episodeV2Metadata(episode), /request_id/);
  assert.throws(() => episodeV2Metadata({...episode, occurred_at: "2026-10-20T12:00:00Z"}, "id"), /Unknown event date/);
  assert.throws(() => episodeV2Metadata({...episode, time_precision: "day", occurred_at: null}, "id"), /occurred_at/);
  assert.throws(() => episodeV2Metadata({...episode, time_precision: "day", occurred_at: "2026-10-20"}, "id"), /ISO timestamp/);
  assert.throws(() => episodeV2Metadata({...episode, time_precision: "day", occurred_at: "2026-02-30T12:00:00Z"}, "id"), /ISO timestamp/);
  assert.equal(episodeV2Metadata({...episode, time_precision: "month", occurred_at: "2026-10"}, "id").occurred_at, "2026-10");
  assert.equal(episodeV2Metadata({...episode, time_precision: "year", occurred_at: "2026"}, "id").occurred_at, "2026");
});

test("restricted input is refused until isolation is implemented", () => {
  assert.throws(() => episodeV2Metadata({...episode, privacy: "restricted"}, "id"), /access controls/);
});

test("replay comparison rejects changed metadata", () => {
  const saved = episodeV2Metadata(episode, "id");
  assert.equal(sameEpisodeV2(saved, episodeV2Metadata(episode, "id")), true);
  assert.equal(sameEpisodeV2(Object.fromEntries(Object.entries(saved).reverse()), saved), true);
  assert.equal(sameEpisodeV2(saved, episodeV2Metadata({...episode, temporal_status: "historical"}, "id")), false);
});
