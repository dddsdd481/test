using AISelectionAssistant.Core.Prompts;

namespace AISelectionAssistant.App.Overlay;

public sealed class FloatingSidebarViewModel
{
    public IReadOnlyList<PromptAction> Actions { get; } = BuiltInPromptActions.All;
}
