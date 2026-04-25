using CsvHelper.Configuration.Attributes;

namespace Riptide.Pipelines.Models;

public sealed class PredictionScoresCsvRow
{
    [Name("Date")]
    public DateTime Date { get; set; }

    [Name("Study_Turbidity_NTU")]
    public double? StudyTurbidityNtu { get; set; }

    [Name("Nitrate_mgL")]
    public double? NitrateMgL { get; set; }

    [Name("Nitrite_mgL")]
    public double? NitriteMgL { get; set; }

    [Name("Ammonium_mgL")]
    public double? AmmoniumMgL { get; set; }

    [Name("Calcium_mgL")]
    public double? CalciumMgL { get; set; }

    [Name("Magnesium_mgL")]
    public double? MagnesiumMgL { get; set; }

    [Name("EO_Chlorophyll_A")]
    public double EoChlorophyllA { get; set; }

    [Name("EO_Turbidity")]
    public double EoTurbidity { get; set; }

    [Name("EO_Surface_Temp")]
    public double EoSurfaceTemp { get; set; }

    [Name("EO_Total_Suspended_Matter")]
    public double EoTotalSuspendedMatter { get; set; }

    [Name("Is_Study_Actual")]
    public int IsStudyActualRaw { get; set; }

    [Name("Is_EO_Actual")]
    public int IsEoActualRaw { get; set; }

    [Name("Is_Summer")]
    public int IsSummerRaw { get; set; }

    [Name("Month")]
    public int Month { get; set; }

    [Name("Quarter")]
    public int Quarter { get; set; }

    [Name("EO_Turbidity_Lag1")]
    public double? EoTurbidityLag1 { get; set; }

    [Name("EO_Turbidity_Lag2")]
    public double? EoTurbidityLag2 { get; set; }

    [Name("Rolling_EO_Chl_A_7d")]
    public double RollingEoChlorophyllA7d { get; set; }

    [Name("Rolling_EO_Turbidity_7d")]
    public double RollingEoTurbidity7d { get; set; }

    [Name("Delta_EO_Temp_3d")]
    public double DeltaEoTemp3d { get; set; }

    [Name("Nutrient_Pressure_Index")]
    public double NutrientPressureIndex { get; set; }

    [Name("Bloom_Potential_Feature")]
    public double BloomPotentialFeature { get; set; }

    [Name("Bloom_Risk_Score")]
    public double BloomRiskScore { get; set; }

    [Name("Eutrophication_Risk_Score")]
    public double EutrophicationRiskScore { get; set; }

    [Name("Water_Quality_Score")]
    public double WaterQualityScore { get; set; }

    [Name("Alert_Level")]
    public string AlertLevel { get; set; } = string.Empty;

    [Name("Predicted_InSitu_Turbidity")]
    public double PredictedInSituTurbidity { get; set; }

    public bool IsStudyActual => IsStudyActualRaw == 1;

    public bool IsEoActual => IsEoActualRaw == 1;

    public bool IsSummer => IsSummerRaw == 1;
}