from pathlib import Path

from context_curator_lite import curator


def test_classify_uses_keywords() -> None:
    assert curator.classify("next action on this repo") == "next-action"
    assert curator.classify("architecture plan overview") == "idea"


def _write_files(root: Path) -> Path:
    (root / "notes.md").write_text(
        "todo: next action for repo context handoff\n",
        encoding="utf-8",
    )
    (root / "facts.json").write_text('{"root":"scan","status":"ok"}', encoding="utf-8")
    return root


def test_run_writes_bundle(tmp_path: Path) -> None:
    _write_files(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    code = curator.main([str(tmp_path)], str(out), limit=100, per_file_limit=3)
    assert code == 0
    manifest_path = out / "curated-session-context-manifest.json"
    assert manifest_path.exists()
    manifest = manifest_path.read_text(encoding="utf-8")
    assert "generated" in manifest
    assert "absolute_paths_included" in manifest
    assert str(tmp_path) not in manifest

    jsonl_files = list(out.glob("curated-session-context-*.jsonl"))
    assert jsonl_files
    bundle = jsonl_files[0].read_text(encoding="utf-8")
    assert '"source": "notes.md"' in bundle
    assert str(tmp_path) not in bundle


def test_scrub_replaces_secret_patterns() -> None:
    text = "token=ghp_" + ("A" * 36)
    assert "ghp_" not in curator.scrub(text)
