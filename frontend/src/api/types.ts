export type KeywordStatus = "candidate" | "approved" | "rejected" | "published";

export interface Keyword {
  id: number;
  site_id: number;
  keyword: string;
  rationale: string | null;
  volume: number | null;
  difficulty: number | null;
  relevance_score: number | null;
  opportunity_score: number | null;
  status: KeywordStatus;
  created_at: string;
}

export interface Site {
  id: number;
  url: string;
  name: string;
  profile: Record<string, unknown> | null;
  subreddits: string | null;
  created_at: string;
}

export type ArticleStatus = "draft" | "review" | "published";
export type ArticleType = "how_to" | "informational" | "comparison";

export interface Article {
  id: number;
  site_id: number;
  keyword_id: number | null;
  title: string;
  slug: string;
  article_type: ArticleType;
  status: ArticleStatus;
  created_at: string;
}

export type Severity = "critical" | "high" | "medium" | "low";

export interface AuditFinding {
  id: number;
  site_id: number;
  page: string;
  severity: Severity;
  description: string;
  first_seen: string;
  resolved_at: string | null;
}

export type GeoProvider = "chatgpt" | "claude" | "gemini" | "perplexity";

export interface GeoMention {
  id: number;
  site_id: number;
  query: string;
  provider: GeoProvider;
  mentioned: boolean;
  context_snippet: string | null;
  competitors_mentioned: string[] | null;
  checked_at: string;
}

export type RedditOpportunityStatus = "new" | "replied" | "skipped";

export interface RedditOpportunity {
  id: number;
  site_id: number;
  thread_url: string;
  subreddit: string;
  matched_keyword: string;
  draft_reply: string | null;
  status: RedditOpportunityStatus;
  created_at: string;
}
