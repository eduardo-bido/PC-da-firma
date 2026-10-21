export interface EpisodeV2 {
  source_reference: string;
  occurred_at: string | null;
  time_precision: "day" | "month" | "year" | "unknown";
  knowledge_kind: "fact" | "decision" | "intention" | "outcome" | "preference" | "hypothesis" | "observation";
  epistemic_status: "user_confirmed" | "quoted" | "reported" | "inferred" | "unknown";
  temporal_status: "current" | "historical" | "future" | "uncertain";
  privacy: "standard";
}

/** Metadata is stored alongside the immutable original, never as a graph claim. */
export function episodeV2Metadata(episode: EpisodeV2, requestId?: string) {
  if (!requestId) throw new Error("V2 capture requires a stable request_id");
  const reference = episode.source_reference.trim();
  if (!reference || reference !== episode.source_reference) {
    throw new Error("source_reference must be a non-empty stable reference");
  }
  if (episode.privacy !== "standard") {
    throw new Error("Restricted memories require access controls before capture");
  }
  if (episode.time_precision === "unknown" && episode.occurred_at !== null) {
    throw new Error("Unknown event date must be null");
  }
  if (episode.time_precision !== "unknown" && episode.occurred_at === null) {
    throw new Error("A dated event needs occurred_at");
  }
  if (episode.occurred_at !== null) {
    const value = episode.occurred_at;
    if (episode.time_precision === "year" && !/^\d{4}$/.test(value)) {
      throw new Error("Year precision requires YYYY");
    }
    if (episode.time_precision === "month" && !/^\d{4}-(0[1-9]|1[0-2])$/.test(value)) {
      throw new Error("Month precision requires YYYY-MM");
    }
    if (episode.time_precision === "day") {
      const parts = /^(\d{4})-(\d{2})-(\d{2})T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.exec(value);
      const dayCount = parts ? new Date(Date.UTC(Number(parts[1]), Number(parts[2]), 0)).getUTCDate() : 0;
      if (!parts || Number(parts[2]) < 1 || Number(parts[2]) > 12 ||
        Number(parts[3]) < 1 || Number(parts[3]) > dayCount || Number.isNaN(new Date(value).getTime())) {
        throw new Error("Day precision requires an ISO timestamp with timezone");
      }
    }
  }
  return {
    version: 2,
    source: { system: "chatgpt", reference },
    occurred_at: episode.occurred_at,
    time_precision: episode.time_precision,
    knowledge_kind: episode.knowledge_kind,
    epistemic_status: episode.epistemic_status,
    temporal_status: episode.temporal_status,
    privacy: episode.privacy,
    promotion_status: "raw_only",
  } as const;
}

export function sameEpisodeV2(left: unknown, right: unknown): boolean {
  const canonical = (value: unknown): unknown => {
    if (Array.isArray(value)) return value.map(canonical);
    if (value && typeof value === "object") {
      return Object.fromEntries(Object.entries(value)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, item]) => [key, canonical(item)]));
    }
    return value;
  };
  return JSON.stringify(canonical(left)) === JSON.stringify(canonical(right));
}
