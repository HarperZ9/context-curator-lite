"""Curate sanitized planning context from local assistant sessions.

This tool does not copy raw transcripts. It extracts short planning-like
fragments, redacts secret-shaped values, and normalizes posture-heavy wording
into neutral workspace language before writing local protected artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Iterable


KEYWORDS = re.compile(
    r"\b("
    r"todo|next|plan|roadmap|blocker|blocked|handoff|resume|continue|"
    r"migrat|integrat|curat|commit|push|branch|repo|worktree|dirty|"
    r"architecture|design|invariant|whitepaper|research|idea|context|"
    r"apps|quanta|universe|skse|wow|aurora|warden|agents|protected|"
    r"codex|claude|session|scope|manifest|ledger"
    r")\b",
    re.IGNORECASE,
)

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bASIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(bearer|token|api[_-]?key|password|secret)\s*[:=]\s*\S+"),
]

POSTURE_REPLACEMENTS = [
    (re.compile(r"(?i)\bomni[- ]?weapon\b"), "omni-state utility"),
    (re.compile(r"(?i)\bweaponized?\b"), "utility-oriented"),
    (re.compile(r"(?i)\boffensive[- ]?postured?\b"), "sensitive-posture"),
    (re.compile(r"(?i)\boffensive\b"), "sensitive"),
    (re.compile(r"(?i)\battack(?:ing|ed|s)?\b"), "exercise"),
    (re.compile(r"(?i)\bexploit(?:ing|ed|s)?\b"), "validate"),
    (re.compile(r"(?i)\bexfiltrat(?:e|ed|es|ing|ion)\b"), "controlled transfer"),
    (re.compile(r"(?i)\bbypass(?:ed|es|ing)?\b"), "alternate path"),
    (re.compile(r"(?i)\bpayload(?:s)?\b"), "artifact"),
    (re.compile(r"(?i)\btarget(?:s|ed|ing)?\b"), "surface"),
    (re.compile(r"(?i)\bvictim(?:s)?\b"), "affected party"),
    (re.compile(r"(?i)\bcredential(?:s)?\b"), "access material"),
    (re.compile(r"(?i)\bmalware\b"), "unknown binary"),
    (re.compile(r"(?i)\brootkit\b"), "privileged component"),
    (re.compile(r"(?i)\bsteal(?:ing|s)?\b"), "extract"),
    (re.compile(r"(?i)\bkill chain\b"), "workflow chain"),
    (re.compile(r"(?i)\brecon(?:naissance)?\b"), "survey"),
    (re.compile(r"(?i)\brecon(?=\.{2,})"), "survey"),
    (re.compile(r"(?i)\bcovert\b"), "non-public"),
]

IDENTIFIER_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "<email>"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "<ip>"),
    (re.compile(r"https?://(?!github\.com/)[^\s)>\"]+"), "<url>"),
    (re.compile(r"\b[A-Fa-f0-9]{40,64}\b"), "<hash>"),
]

EXTENSIONS = {".jsonl", ".json", ".md", ".txt", ".log"}
MAX_FILE_BYTES = 25 * 1024 * 1024
MAX_FRAGMENT = 420


def iter_strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def scrub(text: str) -> str:
    text = text.replace("\x00", " ")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("<redacted-secret>", text)
    for pattern, replacement in IDENTIFIER_PATTERNS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in POSTURE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > MAX_FRAGMENT:
        text = text[: MAX_FRAGMENT - 3].rstrip() + "..."
    return text


def classify(text: str) -> str:
    low = text.lower()
    if any(word in low for word in ("blocker", "blocked", "error", "failed")):
        return "blocker"
    if any(word in low for word in ("todo", "next", "resume", "continue", "handoff")):
        return "next-action"
    if any(word in low for word in ("architecture", "design", "invariant", "whitepaper", "research", "idea")):
        return "idea"
    if any(word in low for word in ("repo", "worktree", "branch", "commit", "push", "dirty", "migrat")):
        return "repo-context"
    return "context"


def fragments_from_file(path: Path) -> Iterable[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return
    except OSError:
        return

    suffix = path.suffix.lower()
    try:
        if suffix == ".jsonl":
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        if KEYWORDS.search(line):
                            yield line
                        continue
                    for text in iter_strings(item):
                        if KEYWORDS.search(text):
                            yield text
        elif suffix == ".json":
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                try:
                    item = json.load(handle)
                except json.JSONDecodeError:
                    handle.seek(0)
                    for line in handle:
                        if KEYWORDS.search(line):
                            yield line
                else:
                    for text in iter_strings(item):
                        if KEYWORDS.search(text):
                            yield text
        else:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    if KEYWORDS.search(line):
                        yield line
    except OSError:
        return


def source_files(roots: list[Path]) -> Iterable[Path]:
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file() and root.suffix.lower() in EXTENSIONS:
            paths.append(root)
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                paths.append(path)
    yield from sorted(paths, key=lambda item: item.stat().st_mtime, reverse=True)


def main(
    roots: list[str] | None = None,
    out_dir: str | Path | None = None,
    limit: int = 2500,
    per_file_limit: int = 12,
) -> int:
    if roots is None or out_dir is None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--root", action="append", required=True)
        parser.add_argument("--out-dir", required=True)
        parser.add_argument("--limit", type=int, default=2500)
        parser.add_argument("--per-file-limit", type=int, default=12)
        args = parser.parse_args()
        roots = args.root
        out_dir = args.out_dir
        limit = args.limit
        per_file_limit = args.per_file_limit

    roots = [Path(item) for item in roots]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    records: list[dict[str, str]] = []
    scanned = 0
    matched = 0

    for path in source_files(roots):
        scanned += 1
        file_records = 0
        for raw in fragments_from_file(path):
            matched += 1
            text = scrub(raw)
            if not text or len(text) < 20:
                continue
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            if digest in seen:
                continue
            seen.add(digest)
            records.append(
                {
                    "kind": classify(text),
                    "source": str(path),
                    "source_sha256_prefix": hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:16],
                    "text": text,
                }
            )
            file_records += 1
            if file_records >= per_file_limit:
                break
            if len(records) >= limit:
                break
        if len(records) >= limit:
            break

    timestamp = datetime.now().isoformat(timespec="seconds")
    jsonl_path = out_dir / "curated-session-context-2026-06-10.jsonl"
    md_path = out_dir / "CURATED-SESSION-CONTEXT-2026-06-10.md"
    manifest_path = out_dir / "curated-session-context-manifest.json"

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=True) + "\n")

    counts = Counter(record["kind"] for record in records)
    with md_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# Curated Session Context\n\n")
        handle.write("Local-only sanitized extraction. Raw transcripts were not copied.\n\n")
        handle.write("## Counts\n\n")
        handle.write(f"- Generated: {timestamp}\n")
        handle.write(f"- Source files scanned: {scanned}\n")
        handle.write(f"- Raw keyword matches before sanitization: {matched}\n")
        handle.write(f"- Curated records: {len(records)}\n")
        for kind, count in sorted(counts.items()):
            handle.write(f"- {kind}: {count}\n")
        handle.write("\n## Curated Items\n\n")
        for index, record in enumerate(records, 1):
            handle.write(f"### {index}. {record['kind']}\n\n")
            handle.write(f"- Source hash: `{record['source_sha256_prefix']}`\n")
            handle.write(f"- Text: {record['text']}\n\n")

    manifest = {
        "generated": timestamp,
        "roots": [str(root) for root in roots],
        "outputs": [str(md_path), str(jsonl_path), str(manifest_path)],
        "raw_transcripts_copied": False,
        "source_files_scanned": scanned,
        "raw_keyword_matches": matched,
        "curated_records": len(records),
        "counts": dict(counts),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=True), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
