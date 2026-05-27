namespace AISelectionAssistant.Core.Prompts;

public sealed record PromptAction(
    string Id,
    string Name,
    string Template,
    string Icon,
    int SortOrder,
    bool IsBuiltIn);

public static class BuiltInPromptActions
{
    public static IReadOnlyList<PromptAction> All { get; } =
    [
        new("explain", "Explain", "Explain this clearly and simply:\n\n{{selection}}", "?", 10, true),
        new("translate", "Translate", "Translate this into {{language}}:\n\n{{selection}}", "文", 20, true),
        new("summarize", "Summarize", "Summarize this briefly:\n\n{{selection}}", "≡", 30, true),
        new("rewrite", "Rewrite", "Rewrite this professionally:\n\n{{selection}}", "✎", 40, true),
        new("grammar", "Grammar Fix", "Correct grammar and preserve meaning:\n\n{{selection}}", "✓", 50, true),
        new("ask", "Ask AI", "{{prompt}}\n\nSelected text:\n{{selection}}", "AI", 60, true)
    ];
}
