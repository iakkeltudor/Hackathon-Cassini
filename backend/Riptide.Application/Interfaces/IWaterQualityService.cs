using Riptide.Application.Dtos;

namespace Riptide.Application.Interfaces;

public interface IWaterQualityService
{
    Task<IndicatorDto?> GetLatestIndicatorsAsync(CancellationToken cancellationToken = default);

    Task<IReadOnlyList<TimeseriesPointDto>> GetTimeseriesAsync(
        DateTime? fromUtc = null,
        DateTime? toUtc = null,
        CancellationToken cancellationToken = default);

    Task<RiskSummaryDto?> GetRiskSummaryAsync(CancellationToken cancellationToken = default);

    Task<IReadOnlyList<AlertDto>> GetAlertsAsync(CancellationToken cancellationToken = default);

    Task<IReadOnlyList<LayerDto>> GetLayersAsync(CancellationToken cancellationToken = default);

    Task<DashboardDto> GetDashboardAsync(CancellationToken cancellationToken = default);
}