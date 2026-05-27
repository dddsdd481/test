namespace AISelectionAssistant.Core.Conversation;

public sealed record SelectionConversation(
    Guid Id,
    string SelectedTextHash,
    string SelectedTextPreview,
    string? SourceProcess,
    string? SourceWindowTitle,
    DateTimeOffset CreatedAtUtc,
    DateTimeOffset UpdatedAtUtc,
    bool IsPinned);

public sealed record ConversationMessage(
    Guid Id,
    Guid ConversationId,
    ConversationRole Role,
    string Content,
    string? ProviderId,
    string? ModelId,
    DateTimeOffset CreatedAtUtc);

public enum ConversationRole
{
    User,
    Assistant,
    System
}
