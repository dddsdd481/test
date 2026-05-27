using System.Windows;
using AISelectionAssistant.Core.Abstractions;
using AISelectionAssistant.Infrastructure.AI;
using AISelectionAssistant.Infrastructure.Clipboard;
using AISelectionAssistant.Infrastructure.Detection;
using AISelectionAssistant.Infrastructure.Storage;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace AISelectionAssistant.App;

public partial class App : Application
{
    private IHost? host;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        host = Host.CreateDefaultBuilder()
            .ConfigureServices(services =>
            {
                services.AddSingleton<IClipboardService, SafeClipboardService>();
                services.AddSingleton<ISelectionDetector, SelectionDetectionService>();
                services.AddSingleton<IConversationStore, SqliteConversationStore>();
                services.AddSingleton<IAiProvider, StubAiProvider>();
                services.AddSingleton<IAiRouter, AiRouterService>();
                services.AddSingleton<MainWindow>();
            })
            .Build();

        host.Start();
        host.Services.GetRequiredService<MainWindow>().Show();
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        if (host is not null)
        {
            await host.StopAsync(TimeSpan.FromSeconds(2));
            host.Dispose();
        }

        base.OnExit(e);
    }
}
