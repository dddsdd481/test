using AISelectionAssistant.Core.Conversation;

namespace AISelectionAssistant.Core.AI;

public enum AiRoutingMode
{
    Auto,
    Fast,
    BestQuality,
    Cheapest,
    Privacy
}

public sealed record AiRequest(
    string ActionId,
    string SystemPrompt,
    string SelectedText,
    string? FollowUpPrompt,
    IReadOnlyList<ConversationMessage> History,
    AiRoutingMode RoutingMode,
    string? PreferredModelId,
    bool SensitiveMode);

public sealed record AiResponseChunk(
    string ProviderId,
    string ModelId,
    string Text,
    bool IsFinal = false);

public sealed record AiProviderCapabilities(
    bool SupportsStreaming,
    bool SupportsLongContext,
    bool SupportsCode,
    bool SupportsVision,
    decimal RelativeCost);

public sealed record ProviderFailure(
    string ProviderId,
    ProviderFailureReason Reason,
    string Message,
    bool IsRecoverable);

public enum ProviderFailureReason
{
    MissingApiKey,
    InvalidApiKey,
    QuotaExceeded,
    RateLimited,
    Timeout,
    Outage,
    UnsupportedModel,
    ContentPolicy,
    Unknown
}
