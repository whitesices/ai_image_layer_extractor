# Feature Workflow

Use this workflow for new product capabilities.

## 1. Intention

State the user value, target workflow, and the smallest useful outcome.

## 2. Specification

Write behavior, data contracts, UI surfaces, privacy constraints, and compatibility requirements. Link affected docs when relevant.

## 3. Implementation Plan

Identify the modules to change and the order of work. Prefer core/data changes before UI wiring.

## 4. Task Breakdown

Split the feature into independently testable steps:

- data/schema
- core service
- optional backend
- UI integration
- tests
- docs
- packaging compatibility if needed

## 5. Tests First

Add focused unit tests for new pure logic before or alongside implementation. Add smoke tests for UI/launcher flows when behavior is not pure.

## 6. Implementation

Keep edits scoped. Preserve existing public behavior and export contracts.

## 7. Local Validation

Run:

```powershell
python -B -m pytest
```

Use offscreen smoke tests when touching PySide6 or launcher behavior.

## 8. Review

Review for guardrail violations, privacy issues, optional dependency failures, path safety, and export compatibility.

## 9. Documentation

Update README, docs, packaging docs, or task notes only where behavior changed.

## 10. Memory Update

Update `.agent/memory/DECISIONS.md` or relevant memory files with important decisions, compatibility constraints, and validation results.
