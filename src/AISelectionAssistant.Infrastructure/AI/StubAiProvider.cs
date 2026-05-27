using AISelectionAssistant.Core.Abstractions;
using AISelectionAssistant.Core.AI;

namespace AISelectionAssistant.Infrastructure.AI;

public sealed class StubAiProvider : IAiProvider
{
    public string Id => "stub";

    public AiProviderCapabilities Capabilities { get; } = new(
        SupportsStreaming: true,
        SupportsLongContext: false,
        SupportsCode: true,
        SupportsVision: false,
        RelativeCost: 0);

    public async IAsyncEnumerable<AiResponseChunk> StreamAsync(
        AiRequest request,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var response = $"Stub response for '{request.ActionId}'. Configure OpenAI, Gemini, Anthropic, OpenRouter, or a local provider to enable real AI calls.";

        foreach (var token in response.Split(' '))
        {
            cancellationToken.ThrowIfCancellationRequested();
            await Task.Delay(20, cancellationToken);
            yield return new AiResponseChunk(Id, "stub-model", token + " ");
        }

        yield return new AiResponseChunk(Id, "stub-model", string.Empty, true);
    }
}
