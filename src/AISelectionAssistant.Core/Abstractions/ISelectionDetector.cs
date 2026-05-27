using AISelectionAssistant.Core.Detection;

namespace AISelectionAssistant.Core.Abstractions;

public interface ISelectionDetector
{
    event EventHandler<SelectedTextSession>? SelectionDetected;
    Task StartAsync(CancellationToken cancellationToken);
    Task StopAsync(CancellationToken cancellationToken);
}
