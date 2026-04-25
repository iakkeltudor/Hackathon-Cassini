namespace Riptide.Application.Dtos;

public sealed class DashboardDto
{
    public LakeDto Lake { get; set; } = new();

    public IndicatorDto? LatestIndicators { get; set; }

    public RiskSummaryDto? RiskSummary { get; set; }

    public IReadOnlyList<TimeseriesPointDto> Timeseries { get; set; } = [];

    public IReadOnlyList<AlertDto> Alerts { get; set; } = [];

    public IReadOnlyList<LayerDto> Layers { get; set; } = [];
}