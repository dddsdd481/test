namespace AISelectionAssistant.Core.Detection;

public sealed record SelectedTextSession(
    Guid Id,
    string Text,
    string TextHash,
    SelectionSource Source,
    string? SourceProcess,
    string? SourceWindowTitle,
    SelectionBounds? Bounds,
    DateTimeOffset CreatedAtUtc);

public sealed record SelectionBounds(
    double Left,
    double Top,
    double Width,
    double Height);

public enum SelectionSource
{
    UiAutomation,
    ClipboardFallback,
    Ocr,
    Manual
}
