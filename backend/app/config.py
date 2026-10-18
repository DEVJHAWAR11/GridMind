from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fast_model: str = "openai/gpt-oss-20b"
    tavily_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    redis_url: str = ""  # optional: enables cross-instance live updates
    frontend_origin: str = "http://localhost:5173"

    # Worker / throughput
    run_worker: bool = True  # False = API-only instance (worker can be split out)
    cell_timeout_s: int = 120
    max_concurrency: int = 3  # cells processed in parallel per instance
    poll_interval_s: float = 3.0
    stale_lock_s: int = 180  # a running cell with an older lock is reclaimed
    retry_backoff_s: float = 5.0  # doubles per failed attempt
    max_cell_attempts: int = 3  # worker-level retries (crashes / transient failures)
    max_agent_attempts: int = 2  # search/answer refinement loops inside one run
    answer_reasoning: str = "medium"  # gpt-oss reasoning effort for the answer call (low/medium/high)

    # Upstream rate limits (free tiers): requests per minute, per instance
    llm_rpm: int = 25
    search_rpm: int = 40
    cache_ttl_s: int = 3600
    # Spend guards (stay under free-tier quotas; counted per instance)
    groq_daily_cap: int = 800  # main-model calls/day (free tier ~1000 RPD)
    groq_fast_daily_cap: int = 5000  # fast-model calls/day (free tier ~14,400 RPD)
    tavily_monthly_cap: int = 900  # searches/month (free tier 1000 credits)

    # Abuse / cost guards
    max_rows: int = 50
    max_columns: int = 10
    runs_per_minute: int = 10  # per client IP


@lru_cache
def get_settings() -> Settings:
    return Settings()
