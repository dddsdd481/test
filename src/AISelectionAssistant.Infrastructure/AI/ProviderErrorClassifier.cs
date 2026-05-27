using AISelectionAssistant.Core.AI;

namespace AISelectionAssistant.Infrastructure.AI;

public static class ProviderErrorClassifier
{
    public static ProviderFailure Classify(string providerId, Exception exception)
    {
        var message = exception.Message;

        if (message.Contains("quota", StringComparison.OrdinalIgnoreCase))
        {
            return new ProviderFailure(providerId, ProviderFailureReason.QuotaExceeded, message, true);
        }

        if (message.Contains("rate", StringComparison.OrdinalIgnoreCase) ||
            message.Contains("429", StringComparison.OrdinalIgnoreCase))
        {
            return new ProviderFailure(providerId, ProviderFailureReason.RateLimited, message, true);
        }

        if (exception is TimeoutException || message.Contains("timeout", StringComparison.OrdinalIgnoreCase))
        {
            return new ProviderFailure(providerId, ProviderFailureReason.Timeout, message, true);
        }

        if (message.Contains("api key", StringComparison.OrdinalIgnoreCase) ||
            message.Contains("unauthorized", StringComparison.OrdinalIgnoreCase))
        {
            return new ProviderFailure(providerId, ProviderFailureReason.InvalidApiKey, message, false);
        }

        return new ProviderFailure(providerId, ProviderFailureReason.Unknown, message, true);
    }
}
