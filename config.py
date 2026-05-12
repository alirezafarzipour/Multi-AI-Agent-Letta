"""
Configuration — reads from .env file (copy .env.example to .env and fill in your values)
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Letta Server ───────────────────────────────────────────────────────────────
LETTA_BASE_URL = os.getenv("LETTA_BASE_URL", "http://localhost:8283")

# ── Agent Names ────────────────────────────────────────────────────────────────
EVAL_AGENT_NAME     = os.getenv("EVAL_AGENT_NAME",     "eval_agent")
OUTREACH_AGENT_NAME = os.getenv("OUTREACH_AGENT_NAME", "outreach_agent")

# ── LLM Model ─────────────────────────────────────────────────────────────────
LETTA_LLM_MODEL       = os.getenv("LETTA_LLM_MODEL",       "lmstudio_openai/qwen3-8b@q6_k")
LETTA_EMBEDDING_MODEL = os.getenv("LETTA_EMBEDDING_MODEL",  "letta/letta-free")
LETTA_MODEL_ENDPOINT  = os.getenv("LETTA_MODEL_ENDPOINT",   "http://host.docker.internal:1234/v1")
LETTA_CONTEXT_WINDOW  = int(os.getenv("LETTA_CONTEXT_WINDOW", "8192"))

# ── Company Defaults ───────────────────────────────────────────────────────────
DEFAULT_COMPANY_NAME = os.getenv("DEFAULT_COMPANY_NAME", "YourCompany")
DEFAULT_COMPANY_DESC = os.getenv("DEFAULT_COMPANY_DESC", "A fast-growing tech startup building AI-powered products.")

# ── Scoring ────────────────────────────────────────────────────────────────────
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "6"))