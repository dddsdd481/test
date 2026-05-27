namespace AISelectionAssistant.Core.Clipboard;

public sealed record ClipboardSnapshot(
    bool HasText,
    string? Text,
    DateTimeOffset CapturedAtUtc);
