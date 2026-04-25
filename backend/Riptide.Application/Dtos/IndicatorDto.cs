namespace Riptide.Application.Dtos;

public sealed class IndicatorDto
{
    public DateTime Date { get; set; }

    public double ChlorophyllAProxy { get; set; }

    public double Turbidity { get; set; }

    public double TotalSuspendedMatterProxy { get; set; }

    public double SurfaceTemperatureCelsius { get; set; }

    public double? StudyTurbidityNtu { get; set; }

    public double PredictedInSituTurbidity { get; set; }

    public double? NitrateMgL { get; set; }

    public double? NitriteMgL { get; set; }

    public double? AmmoniumMgL { get; set; }

    public double NutrientPressureIndex { get; set; }

    public double BloomRiskScore { get; set; }

    public double EutrophicationRiskScore { get; set; }

    public double WaterQualityScore { get; set; }

    public string AlertLevel { get; set; } = "Normal";

    public bool IsStudyActual { get; set; }

    public bool IsEoActual { get; set; }
}