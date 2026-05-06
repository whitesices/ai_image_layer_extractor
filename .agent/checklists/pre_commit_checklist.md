# Pre-Commit Checklist

- [ ] No unrelated refactors.
- [ ] No business code changed for documentation-only tasks.
- [ ] `main.py` and `launcher.py` are preserved.
- [ ] Source mode is not broken.
- [ ] Installer mode is not broken if packaging was touched.
- [ ] Default export contract is backward-compatible.
- [ ] No API keys or secrets added.
- [ ] Optional backends remain optional.
- [ ] New behavior has tests.
- [ ] `python -B -m pytest` passes.
- [ ] Relevant docs or `.agent/memory/` files updated.
