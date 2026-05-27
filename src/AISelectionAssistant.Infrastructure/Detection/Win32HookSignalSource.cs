namespace AISelectionAssistant.Infrastructure.Detection;

public sealed class Win32HookSignalSource
{
    public event EventHandler? SelectionSignalReceived;

    public void Start()
    {
    }

    public void Stop()
    {
    }

    public void RaiseManualSignal()
    {
        SelectionSignalReceived?.Invoke(this, EventArgs.Empty);
    }
}
