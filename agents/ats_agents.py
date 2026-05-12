"""
Agent management layer — letta-client SDK
Multi-agent ATS with shared memory blocks + batch processing
"""

from __future__ import annotations
import json
import os
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional, Callable

from letta_client import Letta

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import config


# ── Result dataclass ───────────────────────────────────────────────────────────

@dataclass
class CandidateResult:
    name: str
    resume_text: str
    score: int = 0
    decision: str = "pending"
    justification: str = ""
    email_draft: str = ""
    processing_time: float = 0.0
    error: Optional[str] = None
    agent_thoughts: list[str] = field(default_factory=list)


# ── Client factory ─────────────────────────────────────────────────────────────

def get_client() -> Letta:
    return Letta(base_url=config.LETTA_BASE_URL)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _delete_agent_by_name(client: Letta, name: str):
    try:
        for a in client.agents.list():
            if a.name == name:
                client.agents.delete(a.id)
    except Exception:
        pass


def _fix_agent_endpoint(client: Letta, agent_id: str):
    try:
        client.agents.update(
            agent_id=agent_id,
            llm_config={
                "model":               config.LETTA_LLM_MODEL.split("/")[-1],
                "model_endpoint":      config.LETTA_MODEL_ENDPOINT,
                "model_endpoint_type": "openai",
                "context_window":      config.LETTA_CONTEXT_WINDOW,
            }
        )
    except Exception as e:
        print(f"Warning: could not fix endpoint: {e}")


def _get_or_create_block(client: Letta, label: str, value: str, limit: int = 5000):
    """Get existing shared block by label or create a new one."""
    try:
        blocks = client.blocks.list()
        for b in blocks:
            if getattr(b, "label", None) == label:
                return b
    except Exception:
        pass
    return client.blocks.create(label=label, value=value, limit=limit)


def _update_block(client: Letta, block_id: str, new_value: str):
    try:
        client.blocks.update(block_id=block_id, value=new_value)
    except Exception as e:
        print(f"Warning: block update failed: {e}")


def _read_block(client: Letta, agent_id: str, label: str) -> str:
    try:
        blocks = client.agents.blocks.list(agent_id=agent_id)
        for b in blocks:
            if getattr(b, "label", None) == label:
                return b.value or ""
    except Exception:
        pass
    return ""


# ── Agent setup ────────────────────────────────────────────────────────────────

def setup_agents(
    client: Letta,
    job_description: str,
    company_name: str,
    company_desc: str,
    required_skills: str,
    recruiter_name: str  = "Talent Team",
    recruiter_email: str = "",
    position_title: str  = "",
) -> dict:
    """
    Create eval + outreach agents with shared memory blocks:
      - company   : shared job context (both agents read)
      - candidates: running log of screened candidates (eval writes, outreach reads)
      - decisions : accepted candidates summary (eval writes, outreach reads)
    """
    for name in (config.EVAL_AGENT_NAME, config.OUTREACH_AGENT_NAME):
        _delete_agent_by_name(client, name)

    sign_off = f"{recruiter_name}\n{company_name}"
    if recruiter_email:
        sign_off += f"\n{recruiter_email}"
    position_line = f"the {position_title} position" if position_title else "an exciting opportunity"

    # ── Shared memory blocks ────────────────────────────────────────────────
    company_value = (
        f"Company: {company_name}\n"
        f"About: {company_desc}\n"
        f"Position: {position_title or 'AI/Full-Stack Engineer'}\n"
        f"Job description: {job_description}\n"
        f"Required skills: {required_skills}\n"
        f"Recruiter: {recruiter_name}"
        + (f" <{recruiter_email}>" if recruiter_email else "")
    )
    company_block    = _get_or_create_block(client, "company",    company_value,      limit=3000)
    candidates_block = _get_or_create_block(client, "candidates", "No candidates screened yet.", limit=8000)
    decisions_block  = _get_or_create_block(client, "decisions",  "No decisions made yet.",     limit=5000)

    # ── Eval agent ──────────────────────────────────────────────────────────
    eval_system = (
        f"You are a senior technical recruiter at {company_name}.\n\n"
        "You have access to shared memory blocks:\n"
        "  - 'company'   : job description and required skills (READ ONLY)\n"
        "  - 'candidates': running list of all screened candidates (you UPDATE this after each evaluation)\n"
        "  - 'decisions' : list of accepted candidates (you UPDATE this when you accept someone)\n\n"
        "TASK: When given a candidate's resume:\n"
        "1. Evaluate them ONLY based on their own resume — do NOT compare to previous candidates\n"
        "2. Score 1-10 vs the job requirements in the 'company' block\n"
        "3. Accept if score >= 6\n"
        "4. After evaluating, append a one-line summary to the 'candidates' block:\n"
        "   Format: '[Name] | score/10 | accepted/rejected | one-line reason'\n"
        "5. If accepted, also append to the 'decisions' block:\n"
        "   Format: '[Name] | score/10 | key strengths'\n\n"
        "RESPOND ONLY with valid JSON (no markdown, no explanation):\n"
        '{"decision": "accepted", "score": 8, "justification": "specific reasons based on THIS resume only"}'
    )

    eval_agent = client.agents.create(
        name=config.EVAL_AGENT_NAME,
        model=config.LETTA_LLM_MODEL,
        embedding=config.LETTA_EMBEDDING_MODEL,
        system=eval_system,
        memory_blocks=[
            {"label": "persona",     "value": f"Senior technical recruiter at {company_name}. Objective and thorough."},
            {"label": "human",       "value": "Hiring manager reviewing candidates for the open position."},
            {"label": "company",     "value": company_value},
            {"label": "candidates",  "value": "No candidates screened yet."},
            {"label": "decisions",   "value": "No decisions made yet."},
        ],
    )
    _fix_agent_endpoint(client, eval_agent.id)

    # ── Outreach agent ──────────────────────────────────────────────────────
    outreach_system = (
        f"You are {recruiter_name}, Head of Talent Acquisition at {company_name}.\n\n"
        "You have access to shared memory blocks:\n"
        "  - 'company'  : company and role information\n"
        "  - 'decisions': list of accepted candidates you can reference\n\n"
        f"When given a candidate name and acceptance reason, write a warm personalised email for {position_line}.\n\n"
        "Rules:\n"
        "- Use the candidate's ACTUAL name (never write [candidate name])\n"
        f"- The company is {company_name} (never write [company name])\n"
        f"- The position is: {position_title or job_description[:60]}\n"
        "- Reference specific strengths from the justification provided\n"
        "- 3-4 short paragraphs, genuine tone\n"
        "- Output ONLY the email (Subject: line + body). No explanation, no <think>.\n\n"
        f"Always sign as:\n{sign_off}"
    )

    outreach_agent = client.agents.create(
        name=config.OUTREACH_AGENT_NAME,
        model=config.LETTA_LLM_MODEL,
        embedding=config.LETTA_EMBEDDING_MODEL,
        system=outreach_system,
        memory_blocks=[
            {"label": "persona",    "value": f"{recruiter_name} — Head of Talent Acquisition at {company_name}."},
            {"label": "human",      "value": "Candidate who has been selected for outreach."},
            {"label": "company",    "value": company_value},
            {"label": "decisions",  "value": "No decisions made yet."},
        ],
    )
    _fix_agent_endpoint(client, outreach_agent.id)

    return {
        "eval_agent_id":      eval_agent.id,
        "outreach_agent_id":  outreach_agent.id,
        "company_block_id":   company_block.id,
        "candidates_block_id": candidates_block.id,
        "decisions_block_id": decisions_block.id,
    }


def get_candidates_log(client: Letta) -> str:
    """Read the current candidates log from shared memory."""
    try:
        agents = client.agents.list()
        eval_id = next((a.id for a in agents if a.name == config.EVAL_AGENT_NAME), None)
        if eval_id:
            return _read_block(client, eval_id, "candidates")
    except Exception:
        pass
    return ""


def get_decisions_log(client: Letta) -> str:
    """Read the accepted decisions log from shared memory."""
    try:
        agents = client.agents.list()
        eval_id = next((a.id for a in agents if a.name == config.EVAL_AGENT_NAME), None)
        if eval_id:
            return _read_block(client, eval_id, "decisions")
    except Exception:
        pass
    return ""


# ── Think tag splitter ─────────────────────────────────────────────────────────

def _split_think(raw: str) -> tuple[str, str]:
    think_match = re.search(r"<think>(.*?)</think>", raw, re.DOTALL)
    if think_match:
        thought = think_match.group(1).strip()
        answer  = raw[think_match.end():].strip()
        return thought, answer
    return "", raw.strip()


def _extract_text(messages) -> tuple[str, list[str]]:
    text, thoughts = "", []
    for msg in messages:
        mt = getattr(msg, "message_type", "")
        if mt == "reasoning_message" and hasattr(msg, "reasoning"):
            r = msg.reasoning or ""
            if r:
                thoughts.append(r)
        if mt == "assistant_message":
            content = msg.content
            raw = ""
            if isinstance(content, str):
                raw = content
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        raw += block.get("text", "")
            thought, answer = _split_think(raw)
            if thought:
                thoughts.append(thought)
            text = answer
    return text, thoughts


# ── Single candidate screening ─────────────────────────────────────────────────

def screen_candidate(
    client: Letta,
    name: str,
    resume_text: str,
    progress_callback: Optional[Callable] = None,
    _lock: Optional[threading.Lock] = None,
) -> CandidateResult:
    result   = CandidateResult(name=name, resume_text=resume_text)
    start    = time.time()
    raw_text = ""

    try:
        agents_list = client.agents.list()
        eval_agent_id = outreach_agent_id = None
        for a in agents_list:
            if a.name == config.EVAL_AGENT_NAME:
                eval_agent_id = a.id
            if a.name == config.OUTREACH_AGENT_NAME:
                outreach_agent_id = a.id

        if not eval_agent_id:
            raise RuntimeError("Eval agent not found. Please re-initialize agents.")

        # Reset conversation history (NOT memory blocks) before each candidate
        try:
            client.agents.messages.reset(agent_id=eval_agent_id)
        except Exception:
            pass

        if progress_callback:
            progress_callback(f"🔍 Evaluating {name}…")

        # Use lock for batch mode to avoid concurrent Letta API conflicts
        def _send(agent_id, content):
            if _lock:
                with _lock:
                    return client.agents.messages.create(
                        agent_id=agent_id,
                        messages=[{"role": "user", "content": content}],
                    )
            return client.agents.messages.create(
                agent_id=agent_id,
                messages=[{"role": "user", "content": content}],
            )

        response = _send(
            eval_agent_id,
            f"Candidate: {name}\n\nResume:\n{resume_text[:3000]}"
        )

        raw_text, result.agent_thoughts = _extract_text(response.messages)

        # ── Parse JSON ──────────────────────────────────────────────────────
        cleaned = raw_text.strip()
        if "```" in cleaned:
            parts   = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else cleaned
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        start_i = cleaned.rfind("{")
        end_i   = cleaned.rfind("}") + 1
        if start_i != -1 and end_i > start_i:
            parsed = json.loads(cleaned[start_i:end_i])
            result.decision      = parsed.get("decision", "pending")
            result.score         = int(parsed.get("score", 0))
            result.justification = parsed.get("justification", "")
        else:
            result.justification = cleaned[:400]
            result.decision      = "pending"

        # ── Update shared memory blocks manually ───────────────────────────
        try:
            # Update candidates block
            cands_current = _read_block(client, eval_agent_id, "candidates")
            if cands_current == "No candidates screened yet.":
                cands_current = ""
            new_line = f"{name} | {result.score}/10 | {result.decision} | {result.justification[:80]}"
            client.agents.blocks.update(
                agent_id=eval_agent_id,
                block_label="candidates",
                value=(cands_current + "\n" + new_line).strip(),
            )
            if result.decision == "accepted":
                decs_current = _read_block(client, eval_agent_id, "decisions")
                if decs_current == "No decisions made yet.":
                    decs_current = ""
                dec_line = f"{name} | {result.score}/10 | {result.justification[:80]}"
                client.agents.blocks.update(
                    agent_id=eval_agent_id,
                    block_label="decisions",
                    value=(decs_current + "\n" + dec_line).strip(),
                )
        except Exception as e:
            print(f"Warning: memory update failed: {e}")

        # ── Draft email (both accepted and rejected) ────────────────────────
        if outreach_agent_id and result.decision in ("accepted", "rejected"):
            if progress_callback:
                progress_callback(f"✉️  Drafting email for {name}…")
            try:
                client.agents.messages.reset(agent_id=outreach_agent_id)
            except Exception:
                pass

            if result.decision == "accepted":
                email_prompt = (
                    f"Write a warm outreach email for this ACCEPTED candidate.\n"
                    f"Candidate name: {name}\n"
                    f"Score: {result.score}/10\n"
                    f"Why accepted: {result.justification}\n\n"
                    "Output ONLY the email (Subject: line + body). No explanation."
                )
            else:
                email_prompt = (
                    f"Write a polite and empathetic rejection email for this candidate.\n"
                    f"Candidate name: {name}\n"
                    f"Score: {result.score}/10\n"
                    f"Reason for rejection: {result.justification}\n\n"
                    "Rules:\n"
                    "- Thank them sincerely for their time and application\n"
                    "- Express genuine regret\n"
                    "- Mention 1-2 specific strengths you noticed\n"
                    "- Encourage them to apply for future roles\n"
                    "- Keep it warm and professional (NOT cold or corporate)\n"
                    "Output ONLY the email (Subject: line + body). No explanation."
                )

            out_resp = _send(outreach_agent_id, email_prompt)
            email_text, email_thoughts = _extract_text(out_resp.messages)
            result.email_draft    = email_text
            result.agent_thoughts += email_thoughts

    except json.JSONDecodeError:
        result.justification = raw_text[:400] if raw_text else "JSON parse error."
        result.decision      = "pending"
    except Exception as e:
        result.error    = str(e)
        result.decision = "error"

    result.processing_time = round(time.time() - start, 1)
    return result


# ── Batch screening ────────────────────────────────────────────────────────────

def screen_batch(
    client: Letta,
    candidates: list[tuple[str, str]],
    progress_callback: Optional[Callable] = None,
    max_workers: int = 3,
) -> list[CandidateResult]:
    """
    Screen multiple candidates in parallel (up to max_workers at a time).
    Uses a shared lock to prevent concurrent Letta API write conflicts.

    Args:
        candidates  : list of (name, resume_text) tuples
        max_workers : how many candidates to process simultaneously
    """
    results = [None] * len(candidates)
    lock    = threading.Lock()

    def _process(idx_name_resume):
        idx, name, resume_text = idx_name_resume
        result = screen_candidate(
            client, name, resume_text,
            progress_callback=progress_callback,
            _lock=lock,
        )
        results[idx] = result
        return idx, result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process, (i, name, text)): i
            for i, (name, text) in enumerate(candidates)
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                idx = futures[future]
                name = candidates[idx][0]
                results[idx] = CandidateResult(
                    name=name,
                    resume_text=candidates[idx][1],
                    decision="error",
                    error=str(e),
                )

    return [r for r in results if r is not None]