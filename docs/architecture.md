# AI Selection Assistant Architecture

## Product goal

AI Selection Assistant is a premium-feeling Windows productivity app that appears globally when the user selects text in any Windows application. It should feel instant, native, private, and lightweight while supporting modern AI workflows: one-click actions, streaming responses, follow-up memory, provider failover, model switching, custom prompts, and future local model support.

## Recommended technology stack

| Area | Choice | Rationale |
| --- | --- | --- |
| Desktop shell | WPF on .NET 8 | Mature Windows desktop stack, low overhead, reliable transparent/topmost overlays, broad Windows 10/11 support. |
| Architecture | Clean Architecture + MVVM | Keeps Windows hooks, AI providers, storage, and UI replaceable. |
| Global detection | UI Automation + Win32 low-level hooks + clipboard fallback | No single Windows API works everywhere; layered detection is required. |
| Overlay | Borderless transparent WPF windows | Native, fast, rounded Fluent-like UI, good per-monitor DPI control. |
| Local DB | SQLite | Fast local history, search, migrations, portable storage. |
| Secret storage | Windows DPAPI / Credential Manager | Encrypt API keys locally per user/machine. |
| Streaming AI | `HttpClient` + SSE/chunked readers | Provider-neutral streaming without heavy SDK lock-in. |
| Markdown | Markdig + WPF rendering adapter | Robust markdown parser; renderer can be swapped for WebView2 later. |
| OCR | Windows.Media.Ocr or Windows.Graphics.Capture + OCR plugin | Native-first path with optional cloud/local OCR later. |

## High-level system

```text
Windows apps
   │
   ├─ UI Automation text pattern
   ├─ Win32 mouse/keyboard hooks
   └─ Clipboard fallback
          │
          ▼
SelectionDetectionService
          │  SelectedTextSession
          ▼
OverlayCoordinator ────────────────┐
          │                         │
          ▼                         │
FloatingSidebarWindow               │
          │ action clicked          │
          ▼                         │
PromptComposer                      │
          │                         │
          ▼                         │
ConversationService ────────────────┤
          │                         │
          ▼                         │
AiRouterService                     │
          │                         │
          ├─ OpenAI provider        │
          ├─ Gemini provider        │
          ├─ Anthropic provider     │
          ├─ OpenRouter provider    │
          └─ Local model provider   │
          │
          ▼
Streaming response
          │
          ▼
ResponseWindow + Local History Store
```

## Clean architecture layers

### `AISelectionAssistant.Core`

Pure domain and application contracts. No WPF, Win32, HTTP SDK, SQLite, or platform dependencies.

Responsibilities:

- Selection session model.
- Prompt action model.
- Conversation and message model.
- AI provider abstractions.
- Clipboard abstraction.
- Storage abstraction.
- Routing policy abstractions.

### `AISelectionAssistant.Infrastructure`

Adapters for platform and external systems.

Responsibilities:

- Windows UI Automation selection provider.
- Global mouse/keyboard hooks.
- Clipboard fallback with restoration.
- Provider HTTP clients.
- AI routing implementation.
- SQLite repository.
- DPAPI/Credential Manager secret store.
- Markdown conversion service.
- OCR implementation.

### `AISelectionAssistant.App`

WPF shell and composition root.

Responsibilities:

- Dependency injection setup.
- Floating sidebar window.
- Response popup window.
- Settings/preferences UI.
- Tray icon and app lifetime.
- Theme resources.
- View models.

## Runtime modules

### 1. Selection detection

`SelectionDetectionService` aggregates multiple signal sources:

1. `IKeyboardSelectionSignalSource`
   - Tracks Shift+Arrow, Ctrl+A, Ctrl+Shift+Arrow, keyboard focus changes.
2. `IMouseSelectionSignalSource`
   - Tracks drag start/stop, double click, triple click.
3. `IUiAutomationSelectionReader`
   - Attempts direct selection extraction through UIA `TextPattern` / `TextPattern2`.
4. `IClipboardSelectionReader`
   - Safely simulates Ctrl+C when direct extraction fails, then restores clipboard.

The detector emits `SelectedTextSession` only when all conditions pass:

- Non-empty text.
- Minimum text length or word count threshold.
- Active process is not blacklisted.
- Focused UIA element is not password-protected.
- Clipboard fallback did not fail or time out.

### 2. Floating overlay

`OverlayCoordinator` receives a selection session and positions `FloatingSidebarWindow`.

Key decisions:

- Use `WS_EX_TOOLWINDOW` to avoid taskbar entry.
- Use `Topmost=true` and `ShowActivated=false`.
- Use per-monitor DPI-aware coordinates.
- Prefer selection bounding rectangle from UI Automation.
- Fall back to cursor position from Win32.
- Clamp to working area and avoid taskbar/screen edges.
- Collapse to an icon rail when space is constrained.

### 3. Prompt/action system

Built-in actions are just versioned prompt templates:

- Explain
- Translate
- Summarize
- Rewrite
- Grammar Fix
- Ask AI
- Custom Prompt

Custom prompts should be stored locally with:

- Stable ID.
- Name.
- Template text.
- Icon.
- Sort order.
- Optional target language/model preference.
- Enabled/disabled state.

### 4. Conversation memory per selected text

Each selection creates or reopens a `SelectionConversation` keyed by:

- Normalized hash of selected text.
- Source app process name.
- Optional source document/window title.
- Timestamp and session metadata.

The system should not assume identical selected text always means the same context. Use text hash for lookup suggestions, then store individual sessions with source metadata.

### 5. AI router

`AiRouterService` receives:

- Prompt/action.
- Selected text.
- Conversation history.
- User routing mode.
- User provider preferences.

It selects candidate providers by policy and tries them in order. Failover is automatic for quota, rate limit, timeout, outage, and recoverable provider errors. See `docs/ai-router.md`.

## Folder structure

```text
src/
  AISelectionAssistant.Core/
    Abstractions/
      IClock.cs
      IConversationStore.cs
      ISelectionDetector.cs
      IAiProvider.cs
      IClipboardService.cs
    AI/
      AiRequest.cs
      AiResponseChunk.cs
      AiRoutingMode.cs
      ProviderFailure.cs
    Clipboard/
      ClipboardSnapshot.cs
    Conversation/
      ConversationModels.cs
    Detection/
      SelectedTextSession.cs
      SelectionSource.cs
    Prompts/
      PromptAction.cs
      BuiltInPromptActions.cs

  AISelectionAssistant.Infrastructure/
    AI/
      AiRouterService.cs
      ProviderErrorClassifier.cs
      OpenAiProvider.cs
      GeminiProvider.cs
      AnthropicProvider.cs
      OpenRouterProvider.cs
    Clipboard/
      SafeClipboardService.cs
    Detection/
      SelectionDetectionService.cs
      UiAutomationSelectionReader.cs
      Win32HookSignalSource.cs
    Storage/
      SqliteConversationStore.cs
      DatabaseSchema.sql

  AISelectionAssistant.App/
    Overlay/
      FloatingSidebarWindow.xaml
      FloatingSidebarViewModel.cs
      OverlayCoordinator.cs
    Response/
      ResponseWindow.xaml
      ResponseViewModel.cs
    Settings/
      SettingsWindow.xaml
```

## UI wireframes

### Collapsed sidebar

```text
     ┌─────┐
     │ AI  │
     └─────┘
```

Tiny rounded pill beside the selected text or cursor. Hover or click expands.

### Expanded sidebar

```text
┌─────────────────────────────┐
│ AI Selection Assistant      │
├─────────────────────────────┤
│  Explain      Translate     │
│  Summarize    Rewrite       │
│  Grammar Fix  Ask AI        │
│  Custom...    Settings      │
└─────────────────────────────┘
```

### Response popup

```text
┌──────────────────────────────────────────────┐
│ Explain                         GPT-4o  Pin  │
├──────────────────────────────────────────────┤
│ Streaming markdown response...               │
│                                              │
├──────────────────────────────────────────────┤
│ Copy   Regenerate   Switch model             │
│ Ask a follow-up...                    Send   │
└──────────────────────────────────────────────┘
```

## MVP implementation plan

1. WPF shell, tray icon, and settings skeleton.
2. Global mouse/keyboard hooks for selection signals.
3. UI Automation selected text extraction.
4. Safe clipboard fallback with restoration.
5. Floating sidebar with built-in actions.
6. AI router with OpenAI + Anthropic + Gemini + OpenRouter provider interfaces.
7. One real provider implementation behind configurable API key storage.
8. Streaming response window.
9. SQLite conversation history.
10. Basic custom prompts.
11. Blacklist and sensitive-mode settings.
12. Installer and auto-start option.

## Production architecture decisions

- Treat UIA as the preferred read path, not the only read path.
- Treat clipboard fallback as a last resort and restore clipboard on a best-effort basis.
- Never store raw clipboard snapshots.
- Run hooks and UI Automation work off the UI thread.
- Use bounded debounce windows after selection events.
- Make provider clients stateless and retry-safe.
- Store API keys through DPAPI or Windows Credential Manager, not plain settings JSON.
- Keep global hooks minimal; never perform network or storage work in hook callbacks.
- Design all feature modules as plugin-ready services registered through DI.
