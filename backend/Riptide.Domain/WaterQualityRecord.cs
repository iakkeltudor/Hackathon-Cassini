namespace Riptide.Domain;

public class WaterQualityRecord
{
    public DateTime Date { get; set; }

    public double? StudyTurbidityNtu { get; set; }

    public double? NitrateMgL { get; set; }

    public double? NitriteMgL { get; set; }

    public double? AmmoniumMgL { get; set; }

    public double? CalciumMgL { get; set; }

    public double? MagnesiumMgL { get; set; }

    public double EoChlorophyllA { get; set; }

    public double EoTurbidity { get; set; }

    public double EoSurfaceTemp { get; set; }

    public double EoTotalSuspendedMatter { get; set; }

    public bool IsStudyActual { get; set; }

    public bool IsEoActual { get; set; }

    public bool IsSummer { get; set; }

    public int Month { get; set; }

    public int Quarter { get; set; }

    public double? EoTurbidityLag1 { get; set; }

    public double? EoTurbidityLag2 { get; set; }

    public double RollingEoChlorophyllA7d { get; set; }

    public double RollingEoTurbidity7d { get; set; }

    public double DeltaEoTemp3d { get; set; }

    public double NutrientPressureIndex { get; set; }

    public double BloomPotentialFeature { get; set; }

    public double BloomRiskScore { get; set; }

    public double EutrophicationRiskScore { get; set; }

    public double WaterQualityScore { get; set; }

    public string AlertLevel { get; set; } = "Normal";

    public double PredictedInSituTurbidity { get; set; }
}