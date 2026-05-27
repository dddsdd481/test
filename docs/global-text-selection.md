# Global Text Selection Detection Strategy

## Core challenge

Windows does not provide one universal API for reading selected text in every application. A production assistant must combine direct accessibility APIs, input hooks, focus tracking, and a carefully controlled clipboard fallback.

## Detection layers

### Layer 1: Event signals

Use Win32 hooks to detect that selection may have changed.

Keyboard signals:

- Shift + Arrow
- Ctrl + Shift + Arrow
- Shift + Home / End
- Ctrl + A
- Keyboard focus changes
- Alt + A command shortcut

Mouse signals:

- Left button down/up drag
- Double click word selection
- Triple click paragraph selection
- Drag completion debounce

Implementation:

- Use `SetWindowsHookEx(WH_KEYBOARD_LL)` and `SetWindowsHookEx(WH_MOUSE_LL)`.
- Hook callbacks should only enqueue lightweight events.
- A background detection coordinator debounces and reads selection after user input settles.

Recommended debounce:

- Mouse up after drag: 80-150 ms.
- Double click: 80-120 ms.
- Keyboard selection: 120-200 ms after last selection key event.

### Layer 2: UI Automation direct extraction

After a selection signal:

1. Get active foreground window with `GetForegroundWindow`.
2. Use `AutomationElement.FromHandle`.
3. Try focused element first via `AutomationElement.FocusedElement`.
4. Check `AutomationElement.IsPasswordProperty`.
5. Try `TextPattern`.
6. Try `TextPattern2` when available.
7. Read `GetSelection()`.
8. Filter empty/degenerate ranges.
9. Capture selection bounding rectangles for overlay positioning.

Works well for:

- Microsoft Office.
- Notepad.
- Many WPF/WinUI apps.
- Browsers in accessible text areas.
- Some PDF readers.
- IDE editors depending on accessibility support.

Limitations:

- Chromium rendered content may expose selections inconsistently.
- Electron apps vary by accessibility settings.
- Some PDF and custom-rendered apps expose no useful text patterns.
- Elevated apps may block non-elevated access.

### Layer 3: Clipboard fallback

If UIA fails:

1. Snapshot current clipboard formats.
2. Clear clipboard or capture a sequence token.
3. Send Ctrl+C to the foreground window.
4. Wait briefly for clipboard update.
5. Read text data only.
6. Restore the original clipboard data.
7. Ignore fallback result if it equals prior clipboard and no sequence update occurred.

Safeguards:

- Never persist clipboard snapshots.
- Restore all supported formats, not just text.
- Use timeout guards.
- Avoid fallback when focused element is password-protected.
- Avoid fallback in blacklisted processes.
- Avoid fallback while the app itself owns focus.
- Do not trigger fallback repeatedly for unchanged selection.

Recommended timeout:

- 300-600 ms for clipboard update.
- Abort if foreground window changes during operation.

### Layer 4: OCR fallback

OCR should not be used for normal text selection. It should be a separate user-triggered action for screenshot analysis:

- Alt + A then "OCR screen region".
- Capture region.
- Run native OCR or configured provider.
- Feed extracted text into a new conversation.

## Ignore cases

Do not show sidebar when:

- Selection is empty or whitespace.
- Selection is below minimum threshold, e.g. one punctuation character.
- UIA focused element has `IsPasswordProperty=true`.
- Process is blacklisted.
- Window title or process matches a sensitive app rule.
- User is already interacting with the assistant.
- Clipboard fallback returns stale clipboard text.
- Active window belongs to an elevated process that cannot be safely inspected.

## Positioning strategy

Preferred coordinate sources:

1. UIA selected text range bounding rectangles.
2. Mouse cursor position after drag or double-click.
3. Caret position if available.
4. Foreground window center edge fallback.

Positioning rules:

- Convert physical/logical pixels correctly using per-monitor DPI.
- Place sidebar beside the selection, not covering text.
- Clamp to monitor work area.
- Flip horizontally/vertically near screen edges.
- Use collapsed icon-only mode when available space is tight.
- Hide when foreground window, selection hash, or mouse click context changes.

## Security boundary notes

- A normal user process cannot reliably inspect elevated administrator windows.
- Secure desktop, UAC prompts, password boxes, and some protected apps are intentionally inaccessible.
- The app should surface a clear limitation rather than bypassing Windows security.
- Do not request UIAccess privileges for MVP unless signed installer and secure install path are available.

## Implementation outline

```csharp
public sealed class SelectionDetectionService : ISelectionDetector
{
    public event EventHandler<SelectedTextSession>? SelectionDetected;

    public async Task StartAsync(CancellationToken cancellationToken)
    {
        // Register hook signal sources.
        // Debounce selection events.
        // Try UI Automation.
        // Fall back to clipboard.
        // Emit SelectedTextSession only after safety filters pass.
    }
}
```

## Testing matrix

Validate against:

- Notepad.
- Word.
- Edge/Chrome.
- PDF reader.
- Visual Studio Code.
- Visual Studio.
- Windows Terminal.
- Slack/Teams/Electron app.
- Admin/elevated app.
- Password fields in browser and native apps.
- Multi-monitor mixed-DPI setup.
- Clipboard containing rich text/image/file data before fallback.
