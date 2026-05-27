using System.Security.Cryptography;
using System.Text;
using AISelectionAssistant.Core.Abstractions;
using AISelectionAssistant.Core.Detection;

namespace AISelectionAssistant.Infrastructure.Detection;

public sealed class SelectionDetectionService(IClipboardService clipboardService) : ISelectionDetector
{
    public event EventHandler<SelectedTextSession>? SelectionDetected;

    public Task StartAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.CompletedTask;
    }

    public Task StopAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.CompletedTask;
    }

    public async Task DetectManualSelectionAsync(string selectedText, CancellationToken cancellationToken)
    {
        var normalized = selectedText.Trim();
        if (normalized.Length < 2)
        {
            var fallbackText = await clipboardService.TryReadSelectedTextWithRestoreAsync(cancellationToken);
            normalized = fallbackText?.Trim() ?? string.Empty;
        }

        if (normalized.Length < 2)
        {
            return;
        }

        SelectionDetected?.Invoke(
            this,
            new SelectedTextSession(
                Guid.NewGuid(),
                normalized,
                HashText(normalized),
                SelectionSource.Manual,
                null,
                null,
                null,
                DateTimeOffset.UtcNow));
    }

    private static string HashText(string text)
    {
        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(text));
        return Convert.ToHexString(bytes).ToLowerInvariant();
    }
}
