# AI Selection Assistant

AI Selection Assistant is a Windows 10/11 desktop application concept and MVP scaffold for a global text-selection AI sidebar. It is designed to detect selected text across Windows applications, display a lightweight floating sidebar, route the selected text to AI providers with failover, and preserve privacy-first local conversation history.

This repository contains:

- A WPF/.NET 8 solution scaffold following clean architecture.
- Production architecture guidance in `docs/architecture.md`.
- A Windows-native detection strategy in `docs/global-text-selection.md`.
- AI router and provider failover guidance in `docs/ai-router.md`.
- Local storage, security, performance, roadmap, and limitation notes.

## Solution layout

```text
AISelectionAssistant.sln
src/
  AISelectionAssistant.App/             WPF shell, overlay, and response windows
  AISelectionAssistant.Core/            Domain models and interfaces
  AISelectionAssistant.Infrastructure/  Windows integration, storage, AI clients
docs/
  architecture.md
  ai-router.md
  global-text-selection.md
  storage-security-performance.md
  roadmap.md
```

## Build

Install the .NET 8 SDK on Windows, then run:

```powershell
dotnet restore AISelectionAssistant.sln
dotnet build AISelectionAssistant.sln
```

The scaffold targets `net8.0-windows` for the WPF app and is intended to run on Windows 10/11.

## Development status

This is an MVP-ready architecture and code scaffold, not a finished production app. The global text selection detector, clipboard fallback, AI router, storage layer, overlay UI, and response UI are intentionally structured as replaceable modules so they can be completed and hardened incrementally.
