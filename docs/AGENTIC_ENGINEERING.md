# Agentic Engineering

This repository uses `.agent/` as the operating system for sustainable Codex-driven development.

## Start Every Task Here

1. Read `.agent/specs/000_project_guardrails.md`.
2. Read the relevant workflow in `.agent/workflows/`.
3. Choose the appropriate role guide in `.agent/agents/`.
4. Use `.agent/tasks/task_template.md` for task handoff.
5. Update `.agent/memory/` when a durable decision is made.

## Workflows

- Feature work: `.agent/workflows/feature_workflow.md`
- Bug fixes: `.agent/workflows/bugfix_workflow.md`
- Packaging: `.agent/workflows/packaging_workflow.md`
- Releases: `.agent/workflows/release_workflow.md`

## Agent Roles

- Product Spec Agent: defines product behavior and acceptance criteria.
- Architecture Agent: defines boundaries, interfaces, and migration plans.
- Core Pipeline Agent: implements image, mask, export, and command pipelines.
- UI Agent: implements PySide6 user interaction and wiring.
- Test Agent: adds regression and validation coverage.
- Packaging Agent: maintains launcher, PyInstaller, Inno Setup, and dependencies.
- Review Agent: checks regressions, privacy, optional dependency safety, and export compatibility.

## Guardrail Summary

Do not break:

- `main.py` source mode.
- `launcher.py` packaged mode.
- manual Open Image -> selection -> Create Layer -> Export All workflow.
- `Export/layers`, `Export/masks`, `project.json`, and `preview.png`.
- offline mode without API keys.
- optional backend fallback behavior.

LLMs only produce structured plans. Pixel changes must run through local pipelines.

## Validation

Every task must run:

```powershell
python -B -m pytest
```

For launcher or packaging work, also run:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python launcher.py --smoke-test
```

For release work, use:

```powershell
.\packaging\scripts\build_all.ps1
```

## Memory Discipline

Use `.agent/memory/` for durable facts:

- `PROJECT_MEMORY.md`: project status and capabilities.
- `ARCHITECTURE_MEMORY.md`: module boundaries and design decisions.
- `EXPORT_CONTRACT_MEMORY.md`: export compatibility rules.
- `DECISIONS.md`: dated decisions and validation outcomes.

Do not store secrets, API keys, private user image paths, or machine-specific credentials in memory files.
