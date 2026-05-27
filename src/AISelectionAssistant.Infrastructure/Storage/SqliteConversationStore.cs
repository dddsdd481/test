using AISelectionAssistant.Core.Abstractions;
using AISelectionAssistant.Core.Conversation;

namespace AISelectionAssistant.Infrastructure.Storage;

public sealed class SqliteConversationStore : IConversationStore
{
    private readonly List<SelectionConversation> conversations = [];
    private readonly List<ConversationMessage> messages = [];

    public Task<SelectionConversation?> FindLatestBySelectedTextHashAsync(string selectedTextHash, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        var conversation = conversations
            .Where(item => item.SelectedTextHash == selectedTextHash)
            .OrderByDescending(item => item.UpdatedAtUtc)
            .FirstOrDefault();

        return Task.FromResult(conversation);
    }

    public Task SaveConversationAsync(SelectionConversation conversation, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        conversations.RemoveAll(item => item.Id == conversation.Id);
        conversations.Add(conversation);
        return Task.CompletedTask;
    }

    public Task AddMessageAsync(ConversationMessage message, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        messages.Add(message);
        return Task.CompletedTask;
    }
}
