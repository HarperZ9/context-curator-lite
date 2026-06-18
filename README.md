# Context Curator Lite

> Extract planning fragments and apply heuristic redaction to trim model context.

[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![version](https://img.shields.io/badge/version-0.1.0-informational.svg)
[![CI](https://github.com/HarperZ9/context-curator-lite/actions/workflows/ci.yml/badge.svg)](https://github.com/HarperZ9/context-curator-lite/actions/workflows/ci.yml)
![deps: none](https://img.shields.io/badge/deps-none-success.svg)
[![part of: AI-accountability toolkit](https://img.shields.io/badge/part_of-AI--accountability_toolkit-7a5cff.svg)](https://harperz9.github.io)

`context-curator-lite` extracts planning-like fragments from local text files,
redacts secret-shaped values heuristically, and emits a compact context bundle
for session continuity.

The utility is lightweight by design. It helps a human prepare bounded context;
it is not a security boundary or a replacement for review before sharing.
Generated bundles use relative source references and root hashes instead of
absolute local paths.

## Install

```bash
python -m pip install context-curator-lite
```

## Usage

```bash
context-curator-lite --root . --out-dir ./artifacts
context-curator-lite --root . --out-dir ./artifacts --limit 120 --per-file-limit 8
```

Each run writes three files into `--out-dir`: a dated Markdown summary, a dated
JSONL bundle, and `curated-session-context-manifest.json` (also echoed to
stdout). See [USAGE.md](USAGE.md) for the full CLI/Python reference, worked
examples, and expected output. A runnable demo lives in
[`examples/demo.py`](examples/demo.py).

## Notes

- It is an agent-assisted tool and should be used with human review of the
  generated context.
- Redaction is heuristic and not a security boundary.
- Absolute root paths are omitted from generated bundles by default.

## Release Notes

- 0.1.0: initial package extraction and CLI.

---
**Zain Dana Harper** — small tools with explicit edges.
[Portfolio](https://harperz9.github.io) · [HarperZ9](https://github.com/HarperZ9)
<sub>Built with Claude Code; reviewed, tested, and owned by me.</sub>
