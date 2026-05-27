using AISelectionAssistant.Core.AI;

namespace AISelectionAssistant.Core.Abstractions;

public interface IAiRouter
{
    IAsyncEnumerable<AiResponseChunk> StreamAsync(AiRequest request, CancellationToken cancellationToken);
}
