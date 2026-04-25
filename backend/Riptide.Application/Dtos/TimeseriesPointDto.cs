namespace Riptide.Application.Dtos;

public sealed class TimeseriesPointDto
{
    public DateTime Date { get; set; }

    public double ChlorophyllAProxy { get; set; }

    public double Turbidity { get; set; }

    public double TotalSuspendedMatterProxy { get; set; }

    public double SurfaceTemperatureCelsius { get; set; }

    public double BloomRiskScore { get; set; }

    public double EutrophicationRiskScore { get; set; }

    public double WaterQualityScore { get; set; }

    public double PredictedInSituTurbidity { get; set; }

    public string AlertLevel { get; set; } = "Normal";
}