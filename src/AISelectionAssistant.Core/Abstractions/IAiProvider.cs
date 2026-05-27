using AISelectionAssistant.Core.AI;

namespace AISelectionAssistant.Core.Abstractions;

public interface IAiProvider
{
    string Id { get; }
    AiProviderCapabilities Capabilities { get; }
    IAsyncEnumerable<AiResponseChunk> StreamAsync(AiRequest request, CancellationToken cancellationToken);
}
