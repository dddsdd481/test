using AISelectionAssistant.Core.Abstractions;
using AISelectionAssistant.Core.Clipboard;

namespace AISelectionAssistant.Infrastructure.Clipboard;

public sealed class SafeClipboardService : IClipboardService
{
    public Task<ClipboardSnapshot> CaptureAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult(new ClipboardSnapshot(false, null, DateTimeOffset.UtcNow));
    }

    public Task<string?> TryReadSelectedTextWithRestoreAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult<string?>(null);
    }
}
