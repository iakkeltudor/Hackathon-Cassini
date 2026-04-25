namespace Riptide.Application.Dtos;

public sealed class RiskSummaryDto
{
    public string LakeId { get; set; } = "tarnita";

    public string LakeName { get; set; } = "Lacul Tarnita";

    public DateTime CalculatedAtUtc { get; set; }

    public double BloomRiskScore { get; set; }

    public double EutrophicationRiskScore { get; set; }

    public double WaterQualityScore { get; set; }

    public string RiskLevel { get; set; } = "Normal";

    public string Explanation { get; set; } = string.Empty;
}