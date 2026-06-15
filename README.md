# context-curator-lite

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

## Notes

- It is an agent-assisted tool and should be used with human review of the
  generated context.
- Redaction is heuristic and not a security boundary.
- Absolute root paths are omitted from generated bundles by default.

## Release Notes

- 0.1.0: initial package extraction and CLI.
