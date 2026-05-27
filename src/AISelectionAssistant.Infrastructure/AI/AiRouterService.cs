using AISelectionAssistant.Core.Abstractions;
using AISelectionAssistant.Core.AI;

namespace AISelectionAssistant.Infrastructure.AI;

public sealed class AiRouterService(IEnumerable<IAiProvider> providers) : IAiRouter
{
    private readonly IReadOnlyList<IAiProvider> providers = providers.ToList();

    public async IAsyncEnumerable<AiResponseChunk> StreamAsync(
        AiRequest request,
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken)
    {
        var orderedProviders = OrderProviders(request).ToList();
        if (orderedProviders.Count == 0)
        {
            yield return new AiResponseChunk("router", "none", "No AI providers are configured.", true);
            yield break;
        }

        var failures = new List<ProviderFailure>();

        foreach (var provider in orderedProviders)
        {
            var emittedAnyChunk = false;
            AiResponseChunk? terminalFailureChunk = null;

            await using var enumerator = provider.StreamAsync(request, cancellationToken).GetAsyncEnumerator(cancellationToken);

            while (true)
            {
                AiResponseChunk chunk;

                try
                {
                    if (!await enumerator.MoveNextAsync())
                    {
                        break;
                    }

                    chunk = enumerator.Current;
                    emittedAnyChunk = true;
                }
                catch (Exception exception) when (!cancellationToken.IsCancellationRequested)
                {
                    var failure = ProviderErrorClassifier.Classify(provider.Id, exception);
                    failures.Add(failure);

                    if (!failure.IsRecoverable || emittedAnyChunk)
                    {
                        terminalFailureChunk = new AiResponseChunk(
                            provider.Id,
                            "unknown",
                            $"AI provider failed: {failure.Message}",
                            true);
                        break;
                    }

                    break;
                }

                if (terminalFailureChunk is not null)
                {
                    break;
                }

                yield return chunk;

                if (chunk.IsFinal)
                {
                    yield break;
                }
            }

            if (terminalFailureChunk is not null)
            {
                yield return terminalFailureChunk;
                yield break;
            }
        }

        var failureSummary = failures.Count == 0
            ? "No configured AI provider could answer the request."
            : string.Join(Environment.NewLine, failures.Select(failure => $"{failure.ProviderId}: {failure.Message}"));

        yield return new AiResponseChunk("router", "none", failureSummary, true);
    }

    private IEnumerable<IAiProvider> OrderProviders(AiRequest request)
    {
        var candidates = request.SensitiveMode || request.RoutingMode == AiRoutingMode.Privacy
            ? providers.Where(provider => provider.Id.Equals("local", StringComparison.OrdinalIgnoreCase))
            : providers;

        return request.RoutingMode switch
        {
            AiRoutingMode.Fast => candidates.OrderBy(provider => provider.Capabilities.RelativeCost),
            AiRoutingMode.BestQuality => candidates.OrderByDescending(provider => provider.Capabilities.SupportsCode)
                .ThenByDescending(provider => provider.Capabilities.SupportsLongContext),
            AiRoutingMode.Cheapest => candidates.OrderBy(provider => provider.Capabilities.RelativeCost),
            AiRoutingMode.Privacy => candidates,
            _ => candidates.OrderByDescending(provider => provider.Capabilities.SupportsStreaming)
                .ThenBy(provider => provider.Capabilities.RelativeCost)
        };
    }
}
