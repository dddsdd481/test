# MVP and Production Roadmap

## MVP roadmap

### Phase 1: App shell

- WPF app shell.
- Tray icon.
- Settings window.
- Light/dark theme resources.
- Dependency injection.

### Phase 2: Selection detection

- Low-level keyboard hook.
- Low-level mouse hook.
- Debounced selection event pipeline.
- UI Automation extraction.
- Clipboard fallback with restoration.
- Password and blacklist filtering.

### Phase 3: Floating sidebar

- Borderless topmost overlay.
- Collapsed icon mode.
- Expanded action list.
- Smart positioning and screen-edge avoidance.
- Auto-hide on outside click and focus changes.

### Phase 4: AI response

- Prompt action composition.
- Provider abstraction.
- One real provider implementation.
- Streaming response popup.
- Copy, regenerate, pin, and model selector UI.

### Phase 5: Local memory

- SQLite database.
- Conversation per selected text session.
- Reopen previous conversations.
- Searchable history.
- Custom prompt CRUD.

### Phase 6: MVP polish

- Installer.
- Auto-start option.
- Diagnostics view.
- Settings export/import.
- Keyboard shortcut Alt + A.

## Production roadmap

### Reliability

- Provider health scoring.
- Full failover matrix.
- Retry and cooldown policies.
- Offline/local model mode.
- Better elevated-window handling guidance.

### UX polish

- Fluent Design resources.
- Animations tuned for perceived speed.
- Compact/expanded sidebar customization.
- Rich markdown and code highlighting.
- Per-app behavior rules.
- Multi-monitor mixed-DPI validation.

### Privacy and enterprise

- Optional encrypted history.
- Enterprise policy templates.
- Managed provider configuration.
- Audit controls without content capture.
- Sensitive app blacklist presets.

### OCR and multimodal

- Screenshot region picker.
- Native OCR integration.
- Image-to-AI prompt flow.
- Optional local OCR models.

### Plugin system

- Prompt action plugins.
- Provider plugins.
- OCR plugins.
- Storage/export plugins.
- Enterprise policy plugin hooks.

## Potential Windows limitations and solutions

| Limitation | Impact | Solution |
| --- | --- | --- |
| Some apps do not expose selected text via UIA | Direct extraction fails | Clipboard fallback with restoration. |
| Password fields and secure desktop block access | No selection available | Respect block; never bypass. |
| Elevated apps cannot be inspected by non-elevated process | Inconsistent detection | Inform user; optional elevated companion only if justified. |
| Electron/browser accessibility varies | UIA inconsistency | Fallback strategy and per-app heuristics. |
| Clipboard formats can be complex | Restoration risk | Snapshot multiple formats and test heavily. |
| Multi-monitor DPI conversion is error-prone | Overlay misplaced | Use per-monitor DPI APIs and integration tests. |
| Global hooks can hurt performance if abused | Input lag | Minimal callbacks and async processing. |

## Step-by-step development plan

1. Build solution structure and DI composition root.
2. Define domain models and interfaces in Core.
3. Implement hook signal sources.
4. Implement UIA selection reader.
5. Implement safe clipboard service.
6. Combine readers in `SelectionDetectionService`.
7. Add detection integration tests with Notepad/manual harness.
8. Implement floating overlay and positioning service.
9. Add prompt action registry and settings.
10. Implement AI provider abstraction and one provider.
11. Add router, failover classifier, and provider health model.
12. Implement streaming response UI.
13. Add SQLite store and migrations.
14. Implement conversation history and search.
15. Implement custom prompt CRUD.
16. Add sensitive mode and blacklist settings.
17. Add OCR as optional user-triggered workflow.
18. Package installer and startup registration.
19. Run accessibility, performance, privacy, and DPI test matrix.
20. Harden diagnostics, logs, and crash handling.
