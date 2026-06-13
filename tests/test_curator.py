from pathlib import Path

from context_curator_lite import curator


def test_classify_uses_keywords() -> None:
    assert curator.classify("next action on this repo") == "next-action"
    assert curator.classify("architecture plan overview") == "idea"


def _write_files(root: Path) -> Path:
    (root / "notes.md").write_text("todo: next action\n", encoding="utf-8")
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


def test_scrub_replaces_secret_patterns() -> None:
    text = "token=ghp_" + ("A" * 36)
    assert "ghp_" not in curator.scrub(text)