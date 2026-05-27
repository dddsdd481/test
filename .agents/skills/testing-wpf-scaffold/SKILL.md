---
name: testing-wpf-scaffold
description: Build and visually test the AI Selection Assistant WPF scaffold on Windows. Use when validating desktop UI scaffold changes in this repo.
---

# Testing AI Selection Assistant WPF Scaffold

## Devin Secrets Needed

None for local scaffold validation. Real AI provider testing will need provider-specific API key secrets once providers are wired.

## Environment

- Requires Windows with .NET 8 SDK installed.
- The app project targets `net8.0-windows` and builds as a WPF `WinExe`.

## Build

From the repo root:

```powershell
dotnet build AISelectionAssistant.sln --configuration Release
```

Expected result: build completes with 0 errors.

## Launch

```powershell
Start-Process "src\AISelectionAssistant.App\bin\Release\net8.0-windows\AISelectionAssistant.App.exe"
```

## Visual Assertions

When the main window opens, verify:

- Window/header text includes `AI Selection Assistant`.
- Subtitle includes `Global Windows text selection assistant scaffold`.
- `Sidebar actions` section is visible.
- Six action buttons are visible: `Explain`, `Translate`, `Summarize`, `Rewrite`, `Grammar Fix`, `Ask AI`.
- `Response preview` section is visible and its body starts with `This MVP scaffold wires the app shell`.

## Scope Notes

- Current global text selection detection, floating sidebar auto-display, and real AI calls might be scaffolded but not wired into the primary runtime path.
- Do not claim those features are end-to-end working unless the UI path and provider configuration have been implemented and tested.
