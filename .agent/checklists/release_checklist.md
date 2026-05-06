# Release Checklist

- [ ] Version values are consistent in `version.py`, Inno Setup, README, and packaging docs.
- [ ] `python -B -m pytest` passes.
- [ ] `python launcher.py --smoke-test` passes.
- [ ] `packaging/scripts/build_all.ps1` succeeds.
- [ ] Packaged EXE smoke test passes.
- [ ] Installer exists in `release/`.
- [ ] Silent install/uninstall smoke test passes when feasible.
- [ ] User data directory is preserved after uninstall.
- [ ] API keys and model weights are not bundled.
- [ ] Release notes list known limitations and optional dependencies.
