using AISelectionAssistant.Core.Detection;

namespace AISelectionAssistant.Infrastructure.Detection;

public sealed class UiAutomationSelectionReader
{
    public Task<SelectedTextSession?> TryReadAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return Task.FromResult<SelectedTextSession?>(null);
    }
}
