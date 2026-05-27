using AISelectionAssistant.Core.Detection;

namespace AISelectionAssistant.App.Overlay;

public sealed class OverlayCoordinator
{
    public (double Left, double Top) GetSidebarPosition(SelectedTextSession session, double sidebarWidth, double sidebarHeight)
    {
        if (session.Bounds is null)
        {
            return (24, 24);
        }

        var left = session.Bounds.Left + session.Bounds.Width + 12;
        var top = session.Bounds.Top;
        return (Math.Max(0, left), Math.Max(0, top));
    }
}
