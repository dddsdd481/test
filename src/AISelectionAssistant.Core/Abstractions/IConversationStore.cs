using AISelectionAssistant.Core.Conversation;

namespace AISelectionAssistant.Core.Abstractions;

public interface IConversationStore
{
    Task<SelectionConversation?> FindLatestBySelectedTextHashAsync(string selectedTextHash, CancellationToken cancellationToken);
    Task SaveConversationAsync(SelectionConversation conversation, CancellationToken cancellationToken);
    Task AddMessageAsync(ConversationMessage message, CancellationToken cancellationToken);
}
