# Review Checklist

- [ ] Does the change violate any project guardrail?
- [ ] Does it break Open Image -> selection -> Create Layer -> Export All?
- [ ] Does it break `Export/layers`, `Export/masks`, `project.json`, or `preview.png`?
- [ ] Are masks still full-canvas `uint8` arrays at boundaries?
- [ ] Are bbox coordinates still source-canvas coordinates?
- [ ] Are optional dependencies availability-checked?
- [ ] Does offline mode still work without API keys?
- [ ] Does UI avoid direct concrete model coupling?
- [ ] Are errors user-friendly and non-crashing?
- [ ] Are tests sufficient and passing?
