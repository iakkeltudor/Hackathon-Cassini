using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Riptide.Pipelines.Options;

namespace Riptide.Pipelines;

public static class PipelinesInitializer
{
    public static IServiceCollection AddPipelines(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var storageOptions = new StorageOptions();

        configuration.GetSection("Storage").Bind(storageOptions);

        services.AddSingleton(storageOptions);

        return services;
    }
}