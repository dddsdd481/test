using System.Collections.ObjectModel;

namespace AISelectionAssistant.App.Response;

public sealed class ResponseViewModel
{
    public ObservableCollection<string> ResponseChunks { get; } = [];
}
