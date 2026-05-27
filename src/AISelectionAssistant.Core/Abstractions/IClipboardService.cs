using AISelectionAssistant.Core.Clipboard;

namespace AISelectionAssistant.Core.Abstractions;

public interface IClipboardService
{
    Task<ClipboardSnapshot> CaptureAsync(CancellationToken cancellationToken);
    Task<string?> TryReadSelectedTextWithRestoreAsync(CancellationToken cancellationToken);
}
