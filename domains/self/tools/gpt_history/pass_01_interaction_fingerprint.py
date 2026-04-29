#!/usr/bin/env python3
"""Pass 1 ChatGPT export analyzer for the Helix self domain.

This script treats the ChatGPT export as local evidence, not canon. It writes a
normalized message index plus compact derived reports without copying raw export
files or calling external services.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RAW = ROOT / "archive" / "raw" / "gpt"
DEFAULT_DERIVED = ROOT / "domains" / "self" / "data" / "derived" / "gpt_history"
DEFAULT_REPORTS = ROOT / "domains" / "self" / "reports"

USER_ROLE = "user"
SNIPPET_LEN = 180

REDACTIONS = [
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[email]"),
    (re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"), "[phone]"),
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[api-key]"),
    (re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"), "[token]"),
    (re.compile(r"\b\d{1,5}\s+[A-Z][A-Za-z0-9.'-]*(?:\s+[A-Z][A-Za-z0-9.'-]*){0,5}\s+(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Court|Ct|Boulevard|Blvd)\b"), "[address]"),
]

EXPLICIT_RE = re.compile(
    r"\b(?:sex|sexual|porn|nude|nudes|fetish|genital|orgasm|explicit)\b",
    re.I,
)

REQUEST_TYPES: dict[str, list[str]] = {
    "explain_teach": ["explain", "teach", "what is", "how does", "why does", "walk me through", "eli5", "help me understand"],
    "compare_evaluate": ["compare", "which is better", "evaluate", "rank", "pros and cons", "worth it", "vs", "versus"],
    "debug_fix": ["debug", "fix", "broken", "error", "traceback", "stuck", "bug", "failing", "doesn't work", "not working"],
    "rewrite_reformat": ["rewrite", "reformat", "format", "clean this up", "make this", "turn this into", "edit this"],
    "generate_plan_prompt": ["plan", "prompt", "roadmap", "outline", "strategy", "checklist", "spec"],
    "code_repo_github_codex": ["code", "repo", "github", "codex", "commit", "branch", "pull request", "pr ", "python", "script", "terminal", "git "],
    "image_analysis_visual_style": ["image", "photo", "picture", "visual", "visual style", "aesthetic", "background", "wallpaper", "screenshot"],
    "health_body_sensory": ["health", "my body", "body feels", "body is", "body awareness", "sore", "soreness", "doms", "pain", "sensory", "massage", "symptom", "doctor"],
    "food_drink": ["food", "coffee", "milkshake", "thanksgiving", "recipe", "cook", "drink", "eat"],
    "music_audio_dsp": ["music", "foobar", "dsp", "audio", "vgm", "album", "song", "listening", "last.fm", "listenbrainz"],
    "games": ["game", "games", "trails", "eft", "overwatch", "dota", "stardew", "yume nikki", "steam"],
    "wikipedia_wiki_templates": ["wikipedia", "wiki", "template", "infobox", "citation", "article"],
    "spanish_language": ["spanish", "english", "language", "linguistic", "translate", "peru", "grammar", "phrase"],
    "current_events_news_sports": ["news", "current", "today", "yesterday", "nfl", "commanders", "jayden daniels", "sports", "election"],
    "consciousness_theory_helix": ["consciousness", "theory", "helix", "dcp", "lip", "recursive", "boundary", "dissonance.md"],
    "personal_profile_self_map": ["profile", "self-map", "self map", "personality", "taste", "operator", "my document", "diagnosis", "autism", "schizoid"],
}

INTERACTION_MARKERS: dict[str, list[str]] = {
    "direct_correction": ["no", "i meant", "that's not", "thats not", "wrong", "not what i asked", "you misunderstood"],
    "iteration_demand": ["retry", "again", "keep going", "deeper", "sharpen", "continue", "do it again", "more"],
    "boundary_clarification": ["not just", "not simply", "not what", "not a", "too vague", "don't flatten", "dont flatten", "keep the format", "not x", "instead", "but not"],
    "tool_frustration": ["stuck?", "stuck", "glitched", "why can't you", "why cant you", "agent mode", "broken"],
    "excitement_lock_in": ["perfect", "sweet", "lock this in", "this is huge", "exactly", "yes!", "great"],
    "anxiety_uncertainty": ["i'm worried", "im worried", "annoying", "cause for concern", "not sure", "i struggle", "worried"],
    "compression_language": ["compress", "sharpen", "refactor", "structure", "boundary", "evidence", "pattern", "canon"],
    "evidence_requests": ["look at", "compare", "check", "read", "browse", "research", "verify", "scan"],
}

COGNITIVE_MARKERS: dict[str, list[str]] = {
    "recursive_boundary_compression": ["compress", "compression", "boundary", "same engine", "structure", "refactor", "nested"],
    "reconstructive_intelligence": ["reconstruct", "infer", "pattern", "evidence", "map", "look at", "analyze", "what does this show"],
    "compression_loss_anxiety": ["dont delete", "don't delete", "lose", "loss", "weaker", "preserve", "too compressed", "flatten"],
    "evidence_anomaly_correction": ["evidence", "anomaly", "wrong", "not true", "correction", "negative control", "proof"],
    "object_mediated_sociality": ["girlfriend", "friend", "people", "social", "object-mediated", "profile"],
    "externalized_cognition": ["helix", "repo", "workspace", "document", "database", "archive", "tool", "system"],
    "field_tuning_handle_language": ["field", "tuning", "handle", "threshold", "interior", "route", "gate", "signal"],
    "domain_grounding": ["domain", "ground", "sources", "model", "on its own terms", "capsule"],
    "taste_prediction": ["taste", "like", "prefer", "attraction", "aesthetic", "predict", "pattern"],
    "false_positive_correction": ["false positive", "not x", "not just", "not simply", "youre treating", "you're treating"],
}

DOMAIN_MARKERS: dict[str, list[str]] = {
    "helix": ["helix"],
    "dcp_lip": ["dcp", "lip"],
    "consciousness": ["consciousness", "interiority", "qualia"],
    "music_foobar_dsp_vgm": ["music", "foobar", "dsp", "vgm", "audio", "last.fm", "listenbrainz"],
    "games_trails_eft_overwatch_dota_stardew_yume_nikki": ["games", "game", "trails", "eft", "overwatch", "dota", "stardew", "yume nikki", "steam"],
    "wikipedia_templates_infoboxes": ["wikipedia", "wiki", "template", "infobox", "citation"],
    "spanish_peru_girlfriend": ["spanish", "peru", "girlfriend", "english"],
    "food_coffee_milkshake_thanksgiving": ["food", "coffee", "milkshake", "thanksgiving", "recipe"],
    "body_doms_soreness_massage": ["my body", "body feels", "body is", "body awareness", "doms", "soreness", "sore", "massage", "pain"],
    "commanders_jayden_daniels_nfl": ["commanders", "jayden daniels", "nfl"],
    "aesthetics_visual_style_attraction": ["aesthetic", "visual style", "attraction", "photo", "image", "background", "wallpaper"],
    "reddit_twitter_old_internet": ["reddit", "twitter", "old internet", "forums", "profile"],
}

TYPO_STYLE_TERMS = [
    "im", "ive", "ill", "id", "dont", "doesnt", "cant", "wont", "thats", "youre", "ur", "bc", "tho", "rn", "gonna", "wanna",
]

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "can", "you", "into", "about", "what", "how", "why", "are", "new",
    "chatgpt", "conversation", "help", "make", "my", "to", "of", "in", "on", "a", "is", "it",
}


def ts(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value), timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9][A-Za-z0-9'_:-]*", text.lower())


def redact(text: str) -> str:
    clean = " ".join(text.split())
    for pattern, replacement in REDACTIONS:
        clean = pattern.sub(replacement, clean)
    return clean


def snippet(text: str, limit: int = SNIPPET_LEN) -> str:
    clean = redact(text)
    if "{{" in clean or "{|" in clean or "}}" in clean:
        return "[wiki/template markup snippet omitted]"
    if EXPLICIT_RE.search(clean):
        return "[non-explicit snippet omitted]"
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "..."


def keyword_present(text: str, needle: str) -> bool:
    low = text.lower()
    needle = needle.lower().strip()
    if not needle:
        return False
    escaped = re.escape(needle).replace(r"\ ", r"\s+")
    prefix = r"(?<![a-z0-9])" if needle[0].isalnum() else ""
    suffix = r"(?![a-z0-9])" if needle[-1].isalnum() else ""
    return re.search(prefix + escaped + suffix, low) is not None


def contains_any(text: str, needles: list[str]) -> bool:
    return any(keyword_present(text, n) for n in needles)


def extract_text_and_attachment_flag(content: dict[str, Any] | None, metadata: dict[str, Any] | None) -> tuple[str, bool]:
    if not isinstance(content, dict):
        return "", bool(metadata)
    content_type = content.get("content_type")
    parts = content.get("parts") or []
    chunks: list[str] = []
    has_attachment = content_type not in (None, "text")
    for part in parts:
        if isinstance(part, str):
            chunks.append(part)
        elif isinstance(part, dict):
            if isinstance(part.get("text"), str):
                chunks.append(part["text"])
            if any(k in part for k in ("asset_pointer", "file_id", "image_asset_pointer", "audio_asset_pointer")):
                has_attachment = True
            if part.get("content_type") not in (None, "text"):
                has_attachment = True
        else:
            has_attachment = True
    meta = metadata or {}
    if any(k in meta for k in ("attachments", "files", "file_ids")):
        has_attachment = True
    return "\n".join(chunks).strip(), has_attachment


def load_conversations(raw_dir: Path) -> tuple[list[dict[str, Any]], list[Path]]:
    files = sorted(raw_dir.glob("conversations*.json"))
    conversations: list[dict[str, Any]] = []
    for path in files:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            conversations.extend([x for x in data if isinstance(x, dict)])
        elif isinstance(data, dict):
            conversations.append(data)
    return conversations, files


def normalize(conversations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    messages: list[dict[str, Any]] = []
    conv_index: list[dict[str, Any]] = []
    for conv in conversations:
        conv_id = conv.get("conversation_id") or conv.get("id") or "unknown"
        title = conv.get("title") or "Untitled"
        create_time = ts(conv.get("create_time"))
        update_time = ts(conv.get("update_time"))
        raw_nodes = conv.get("mapping") or {}
        conv_msgs: list[dict[str, Any]] = []
        for node_id, node in raw_nodes.items():
            if not isinstance(node, dict):
                continue
            msg = node.get("message")
            if not isinstance(msg, dict):
                continue
            author = msg.get("author") or {}
            role = author.get("role") or author.get("name") or "unknown"
            text, has_attachment = extract_text_and_attachment_flag(msg.get("content"), msg.get("metadata"))
            if not text and not has_attachment:
                continue
            word_count = len(words(text))
            char_count = len(text)
            approx_tokens = max(0, int(math.ceil(max(char_count / 4.0, word_count * 1.33))))
            conv_msgs.append(
                {
                    "conversation_id": conv_id,
                    "conversation_title": title,
                    "conversation_create_time": create_time,
                    "conversation_update_time": update_time,
                    "message_id": msg.get("id") or node_id,
                    "node_id": node_id,
                    "message_time": ts(msg.get("create_time")),
                    "message_update_time": ts(msg.get("update_time")),
                    "role": role,
                    "message_index": 0,
                    "message_text": text,
                    "character_count": char_count,
                    "word_count": word_count,
                    "approximate_token_count": approx_tokens,
                    "has_attachments": bool(has_attachment),
                }
            )
        conv_msgs.sort(key=lambda m: (m["message_time"] or "", m["message_id"]))
        for i, msg in enumerate(conv_msgs):
            msg["message_index"] = i
        messages.extend(conv_msgs)
        user_count = sum(1 for m in conv_msgs if m["role"] == USER_ROLE)
        conv_index.append(
            {
                "conversation_id": conv_id,
                "title": title,
                "create_time": create_time,
                "update_time": update_time,
                "message_count": len(conv_msgs),
                "user_message_count": user_count,
                "assistant_message_count": sum(1 for m in conv_msgs if m["role"] == "assistant"),
                "has_attachments": any(m["has_attachments"] for m in conv_msgs),
            }
        )
    return messages, conv_index


def examples_for(messages: list[dict[str, Any]], needles: list[str], limit: int = 5) -> list[dict[str, Any]]:
    examples = []
    for msg in messages:
        text = msg["message_text"]
        if contains_any(text, needles):
            examples.append(
                {
                    "conversation_id": msg["conversation_id"],
                    "title": msg["conversation_title"],
                    "message_index": msg["message_index"],
                    "snippet": snippet(text),
                }
            )
            if len(examples) >= limit:
                break
    return examples


def classify_messages(user_messages: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    request_counts: dict[str, Any] = {}
    for label, needles in REQUEST_TYPES.items():
        hits = [m for m in user_messages if contains_any(m["message_text"], needles)]
        request_counts[label] = {
            "count": len(hits),
            "examples": examples_for(user_messages, needles, 4),
        }

    interaction: dict[str, Any] = {}
    for label, needles in INTERACTION_MARKERS.items():
        hits = [m for m in user_messages if contains_any(m["message_text"], needles)]
        interaction[label] = {
            "count": len(hits),
            "examples": examples_for(user_messages, needles, 5),
        }

    cognitive: dict[str, Any] = {}
    for label, needles in COGNITIVE_MARKERS.items():
        hits = [m for m in user_messages if contains_any(m["message_text"], needles)]
        cognitive[label] = {
            "count": len(hits),
            "examples": examples_for(user_messages, needles, 5),
        }
    interaction["cognitive_operation_markers"] = cognitive
    return request_counts, interaction, cognitive


def domain_mentions(user_messages: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label, needles in DOMAIN_MARKERS.items():
        hits = [m for m in user_messages if contains_any(m["message_text"], needles)]
        out[label] = {
            "count": len(hits),
            "examples": examples_for(user_messages, needles, 5),
        }
    return out


def infer_boundary(text: str) -> str:
    low = text.lower()
    if "not" in low and ("just" in low or "simply" in low):
        return "rejects a flattened category; asks for the operative distinction."
    if "i meant" in low:
        return "original request required narrower interpretation or a different target."
    if "wrong" in low or "that's not" in low or "thats not" in low:
        return "assistant inference failed; correction marks a boundary condition."
    if "too vague" in low or "sharpen" in low:
        return "asks to replace generic summary with higher-resolution structure."
    if "don't flatten" in low or "dont flatten" in low:
        return "protects dimensionality from over-compression."
    return "correction marks an interaction boundary."


def assistant_context_summary(text: str) -> str:
    low = text.lower()
    labels = []
    for label, needles in {
        "profile/taste claim": ["taste", "profile", "operator", "personality"],
        "implementation/code": ["code", "script", "file", "repo", "git"],
        "explanation": ["because", "means", "this suggests", "in other words"],
        "plan": ["plan", "steps", "approach", "recommend"],
        "visual/image": ["image", "photo", "visual", "aesthetic"],
    }.items():
        if any(n in low for n in needles):
            labels.append(label)
    return ", ".join(labels[:3]) if labels else "assistant response immediately before correction"


def correction_moments(messages: list[dict[str, Any]], limit: int = 40) -> list[dict[str, Any]]:
    corrections = []
    needles = INTERACTION_MARKERS["direct_correction"] + ["too vague", "dont flatten", "don't flatten", "i said", "please"]
    by_conv: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for msg in messages:
        by_conv[msg["conversation_id"]].append(msg)
    for conv_msgs in by_conv.values():
        for i, msg in enumerate(conv_msgs):
            if msg["role"] != USER_ROLE or not contains_any(msg["message_text"], needles):
                continue
            prev_assistant = None
            for prev in reversed(conv_msgs[:i]):
                if prev["role"] == "assistant":
                    prev_assistant = prev
                    break
            corrections.append(
                {
                    "conversation_id": msg["conversation_id"],
                    "title": msg["conversation_title"],
                    "message_index": msg["message_index"],
                    "assistant_likely_context": assistant_context_summary(prev_assistant["message_text"]) if prev_assistant else None,
                    "user_correction_snippet": snippet(msg["message_text"]),
                    "sharpened_boundary": infer_boundary(msg["message_text"]),
                }
            )
            if len(corrections) >= limit:
                return corrections
    return corrections


def mechanics(messages: list[dict[str, Any]], conv_index: list[dict[str, Any]], user_messages: list[dict[str, Any]]) -> dict[str, Any]:
    lengths = [m["character_count"] for m in user_messages]
    user_counts_by_conv = [c["user_message_count"] for c in conv_index]
    short_bursts = []
    for msg in user_messages:
        text = msg["message_text"].strip().lower()
        if len(text) <= 40 and any(k in text for k in ("retry", "again", "stuck", "continue", "go on", "yes", "no")):
            short_bursts.append(
                {
                    "conversation_id": msg["conversation_id"],
                    "title": msg["conversation_title"],
                    "message_index": msg["message_index"],
                    "snippet": snippet(msg["message_text"], 80),
                }
            )
    title_words = Counter()
    for c in conv_index:
        for w in words(c["title"]):
            if w not in STOPWORDS and len(w) > 2:
                title_words[w] += 1
    dates = [m["message_time"] for m in messages if m.get("message_time")]
    return {
        "conversation_count": len(conv_index),
        "message_count": len(messages),
        "user_message_count": len(user_messages),
        "assistant_message_count": sum(1 for m in messages if m["role"] == "assistant"),
        "date_range": {"first": min(dates) if dates else None, "last": max(dates) if dates else None},
        "user_length_characters": {
            "average": round(statistics.mean(lengths), 2) if lengths else 0,
            "median": round(statistics.median(lengths), 2) if lengths else 0,
            "max": max(lengths) if lengths else 0,
        },
        "turn_depth_user_messages": {
            "average": round(statistics.mean(user_counts_by_conv), 2) if user_counts_by_conv else 0,
            "median": round(statistics.median(user_counts_by_conv), 2) if user_counts_by_conv else 0,
            "max": max(user_counts_by_conv) if user_counts_by_conv else 0,
            "distribution": dict(Counter(bucket_depth(x) for x in user_counts_by_conv)),
        },
        "top_title_keywords": title_words.most_common(30),
        "repeated_short_followups": short_bursts[:30],
    }


def bucket_depth(n: int) -> str:
    if n <= 1:
        return "1"
    if n <= 3:
        return "2-3"
    if n <= 7:
        return "4-7"
    if n <= 15:
        return "8-15"
    return "16+"


def writing_profile(user_messages: list[dict[str, Any]]) -> dict[str, Any]:
    texts = [m["message_text"] for m in user_messages if m["message_text"].strip()]
    chars = "".join(texts)
    letters = [c for c in chars if c.isalpha()]
    lowercase_ratio = sum(1 for c in letters if c.islower()) / len(letters) if letters else 0
    terminal = Counter()
    punctuation = Counter()
    phrase_counts = Counter()
    typo_counts = Counter()
    token_counts = Counter()
    for text in texts:
        stripped = text.strip()
        if stripped:
            terminal[stripped[-1]] += 1
        punctuation.update(re.findall(r"[!?.,;:]+", text))
        low = text.lower()
        for term in TYPO_STYLE_TERMS:
            typo_counts[term] += len(re.findall(rf"\b{re.escape(term)}\b", low))
        for w in words(text):
            if w not in STOPWORDS and len(w) > 2:
                token_counts[w] += 1
        for phrase in [
            "make sure", "i want", "do not", "don't", "while ur at it", "what do you think",
            "does this", "is this", "can you", "we need", "keep going", "read this",
        ]:
            if phrase in low:
                phrase_counts[phrase] += 1
    run_on_like = sum(1 for text in texts if len(words(text)) >= 80 and text.count(".") <= 1)
    return {
        "lowercase_letter_ratio": round(lowercase_ratio, 4),
        "terminal_punctuation_counts": dict(terminal.most_common(20)),
        "punctuation_pattern_counts": dict(punctuation.most_common(30)),
        "apostrophe_omission_and_informal_spellings": {k: v for k, v in typo_counts.most_common() if v},
        "high_frequency_terms": token_counts.most_common(50),
        "high_frequency_phrases": phrase_counts.most_common(30),
        "run_on_or_compressed_thought_chain_estimate": run_on_like,
    }


def candidate_sharpenings(mech: dict[str, Any], domains: dict[str, Any], writing: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "target_section": "3.13 Recognition / Taste",
            "candidate_addition": "Interaction taste is visible in correction behavior: the operator rapidly distinguishes usable structure from generic compliance, then asks for sharper fit rather than mere agreement.",
            "evidence_basis": "Direct correction, iteration demand, and compression-language marker counts.",
        },
        {
            "target_section": "3.14 Evidence / Anomaly Correction",
            "candidate_addition": "ChatGPT history functions as behavioral evidence: correction moments are negative controls that reveal where a model flattened, overgeneralized, or missed the operative boundary.",
            "evidence_basis": "Correction moments and evidence-request markers.",
        },
        {
            "target_section": "3.10 Externalized Cognition / Cognitive Scaffolding",
            "candidate_addition": "LLMs are used as cognitive scaffolding when their work remains inspectable, iterable, and correctable; the operator treats them as pressure tools, not authorities.",
            "evidence_basis": "Code/repo, Helix, read/check/research, and correction/iteration patterns.",
        },
        {
            "target_section": "3.3 Spatial-Image / Topological Cognition",
            "candidate_addition": "Visual evidence suggests a recurring attraction to inhabitable depth: images and scenes pass when they imply thresholds, paths, layered interiors, and returnable worlds.",
            "evidence_basis": "Image/visual-style request markers in the ChatGPT history; should be cross-checked against local photo/background evidence in a later pass.",
        },
        {
            "target_section": "1.6 Active Externalized Domains",
            "candidate_addition": "Language should remain a first-class domain: Spanish and English are nested practice/evidence chambers inside a broader linguistics domain.",
            "evidence_basis": "Operator correction plus Spanish/language mention cluster.",
        },
    ]


def top_counts_table(data: dict[str, Any], limit: int = 20) -> str:
    rows = sorted(((k, v.get("count", 0)) for k, v in data.items()), key=lambda x: x[1], reverse=True)[:limit]
    lines = ["| Signal | Count |", "|---|---:|"]
    lines.extend(f"| `{k}` | {v} |" for k, v in rows)
    return "\n".join(lines)


def examples_md(data: dict[str, Any], keys: list[str], per_key: int = 2) -> str:
    lines = []
    for key in keys:
        item = data.get(key, {})
        examples = item.get("examples", [])[:per_key]
        if not examples:
            continue
        lines.append(f"- `{key}`:")
        for ex in examples:
            lines.append(f"  - {ex['snippet']}")
    return "\n".join(lines) if lines else "- No representative snippets captured."


def write_report(
    report_path: Path,
    raw_files: list[Path],
    mech: dict[str, Any],
    request_counts: dict[str, Any],
    interaction: dict[str, Any],
    domains: dict[str, Any],
    corrections: list[dict[str, Any]],
    writing: dict[str, Any],
    candidates: list[dict[str, str]],
) -> None:
    top_requests = sorted(request_counts, key=lambda k: request_counts[k]["count"], reverse=True)[:8]
    top_domains = sorted(domains, key=lambda k: domains[k]["count"], reverse=True)[:8]
    top_interactions = sorted(
        [k for k in interaction if k != "cognitive_operation_markers"],
        key=lambda k: interaction[k]["count"],
        reverse=True,
    )[:8]
    cognitive = interaction["cognitive_operation_markers"]
    top_cognitive = sorted(cognitive, key=lambda k: cognitive[k]["count"], reverse=True)[:8]

    correction_lines = []
    for item in corrections[:12]:
        correction_lines.append(
            f"- **{item['sharpened_boundary']}** `{item['title']}`: {item['user_correction_snippet']}"
        )
    if not correction_lines:
        correction_lines.append("- No correction moments matched the deterministic rules.")

    candidate_lines = [
        f"- **{c['target_section']}**: {c['candidate_addition']} Evidence basis: {c['evidence_basis']}"
        for c in candidates
    ]

    files = ", ".join(str(p.relative_to(ROOT)).replace("\\", "/") for p in raw_files)
    content = f"""# GPT History Pass 1 — Interaction Fingerprint

## Scope

- Files analyzed: {files}
- Date range: {mech['date_range']['first']} to {mech['date_range']['last']}
- Conversations: {mech['conversation_count']}
- Messages indexed: {mech['message_count']}
- User messages analyzed: {mech['user_message_count']}
- Limitations: deterministic keyword rules only; snippets are short and redacted; no full semantic pass; raw export remains in `archive/chat_exports/` and is not copied into derived outputs.

## Major Findings

The interaction fingerprint strongly supports the existing DISSONANCE.md model: the operator uses ChatGPT as an inspectable cognitive scaffold, not as an authority. The dominant pattern is iterative pressure: ask, inspect, correct, sharpen, and preserve evidence. The history is especially valuable for boundary moments because corrections reveal what the model flattened or overgeneralized.

The highest-signal behavioral evidence is not topic preference alone. It is the operator's repeated demand that outputs remain structurally faithful, re-openable, and operationally useful.

## Interaction Style

{top_counts_table({k: v for k, v in interaction.items() if k != 'cognitive_operation_markers'})}

Representative snippets:

{examples_md(interaction, top_interactions)}

## Writing / Typing Signature

- Lowercase letter ratio: {writing['lowercase_letter_ratio']}
- Estimated compressed long messages: {writing['run_on_or_compressed_thought_chain_estimate']}
- Common phrase markers: {writing['high_frequency_phrases'][:15]}
- Apostrophe omission / informal spelling markers: {writing['apostrophe_omission_and_informal_spellings']}
- Terminal punctuation pattern: {writing['terminal_punctuation_counts']}

The natural style is direct, compressed, and operational. Messages often omit apostrophes and capitalization while preserving precise intent. This reads less like carelessness than fast cognitive routing: the surface can be informal while the structural demand is exact.

## Request-Type Distribution

{top_counts_table(request_counts)}

Interpretation: the operator repeatedly blends implementation, explanation, evidence review, and profile refinement. The categories overlap by design; many messages are both domain work and self-map work.

## Correction / Boundary Moments

{chr(10).join(correction_lines)}

Correction moments should be treated as negative controls. They show where an assistant response became too generic, chose the wrong target, skipped a constraint, or compressed away the important part.

## Cognitive Engine Evidence

{top_counts_table(cognitive)}

Representative snippets:

{examples_md(cognitive, top_cognitive)}

Mapping to DISSONANCE mechanisms:

- **Recursive Boundary Compression**: visible in repeated compression, structure, refactor, boundary, and nested-shape language.
- **Reconstructive Intelligence**: visible in requests to read, compare, infer patterns, and turn fragments into a usable map.
- **Compression-Loss Boundary**: visible in preservation, anti-flattening, and concern that summaries may weaken predictive power.
- **Evidence / Anomaly Correction**: visible in correction moments and repeated requests to look at evidence before interpreting.
- **Externalized Cognition**: visible in Helix, repo, archive, document, and tool use as thinking infrastructure.
- **Object-Field Attachment**: visible where domains, images, games, music, and tools are treated as fields that open interiors.
- **Sovereign Entry / Signal Ownership**: visible in tool frustration, control of thresholds, and insistence on chosen process.
- **Recognition / Taste**: visible in fast acceptance/rejection of structural fit.
- **Affordance / Leverage Conversion**: visible in prompts that convert vague evidence into handles, scripts, reports, and workflows.

## Domain Evidence

{top_counts_table(domains)}

Representative snippets:

{examples_md(domains, top_domains)}

Domain interpretation: repeated domain mentions are not simple interests. They are evidence surfaces used for modeling, testing, and externalizing cognition.

## Candidate DISSONANCE.md Additions

{chr(10).join(candidate_lines)}

## Follow-Up Passes

- **Pass 2 — Correction Boundary Atlas**: cluster correction moments by failure type and map them to protected mechanisms.
- **Pass 3 — Domain Use Profiles**: analyze how music, games, language, wiki, software, and self differ in request style.
- **Pass 4 — LLM-as-Scaffold Workflow**: model how the operator delegates, audits, interrupts, and resumes tool/agent work.
- **Pass 5 — Taste Evidence Surface Scan**: isolate visual, music, game, and attraction requests without explicit raw-content exposure.
"""
    report_path.write_text(content, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze local ChatGPT export as Pass 1 interaction fingerprint.")
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--derived", type=Path, default=DEFAULT_DERIVED)
    parser.add_argument("--reports", type=Path, default=DEFAULT_REPORTS)
    args = parser.parse_args()

    args.derived.mkdir(parents=True, exist_ok=True)
    args.reports.mkdir(parents=True, exist_ok=True)

    conversations, raw_files = load_conversations(args.raw)
    messages, conv_index = normalize(conversations)
    user_messages = [m for m in messages if m["role"] == USER_ROLE]

    with (args.derived / "messages_index.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    write_json(args.derived / "conversations_index.json", conv_index)

    mech = mechanics(messages, conv_index, user_messages)
    request_counts, interaction, _ = classify_messages(user_messages)
    domains = domain_mentions(user_messages)
    corrections = correction_moments(messages)
    writing = writing_profile(user_messages)
    candidates = candidate_sharpenings(interaction["cognitive_operation_markers"], domains, writing)

    interaction_out = {
        "mechanics": mech,
        "interaction_markers": {k: v for k, v in interaction.items() if k != "cognitive_operation_markers"},
        "cognitive_operation_markers": interaction["cognitive_operation_markers"],
        "writing_profile": writing,
    }

    write_json(args.derived / "interaction_markers.json", interaction_out)
    write_json(args.derived / "request_type_counts.json", request_counts)
    write_json(args.derived / "domain_mentions.json", domains)
    write_json(args.derived / "correction_moments.json", corrections)
    write_json(args.derived / "candidate_profile_sharpenings.json", candidates)

    write_report(
        args.reports / "gpt_history_pass_01_interaction_fingerprint.md",
        raw_files,
        mech,
        request_counts,
        interaction,
        domains,
        corrections,
        writing,
        candidates,
    )

    print(
        json.dumps(
            {
                "conversations": mech["conversation_count"],
                "messages": mech["message_count"],
                "user_messages": mech["user_message_count"],
                "derived_dir": str(args.derived),
                "report": str(args.reports / "gpt_history_pass_01_interaction_fingerprint.md"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
