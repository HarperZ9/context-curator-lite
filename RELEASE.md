# Release Checklist

## 0.2.0 Candidate

- [ ] Confirm `README.md`, `LICENSE`, `AUTHORS.md`, `CONTRIBUTING.md`, and
  `CHANGELOG.md` are present.
- [ ] Confirm `--telos-envelope` writes `project-telos-context-envelope.json`
  without absolute paths or raw transcripts.
- [ ] Run `python -m pytest -q`.
- [ ] Run `python -m build`.
- [ ] Run `python -m twine check dist/*`.
- [ ] Run `public-surface-sweeper . --summary`.
- [ ] Create a signed `v0.2.0` tag when signing is configured, or an
  annotated `v0.2.0` tag when it is not.
- [ ] Publish to PyPI only after account ownership, 2FA, and trusted publishing
  configuration are confirmed.

This repository does not auto-publish to a package registry.
