using Riptide.Application.Dtos;
using Riptide.Domain;

namespace Riptide.Pipelines.Mappers;

public static class DtoMapper
{
    public static IndicatorDto ToIndicatorDto(this WaterQualityRecord record)
    {
        return new IndicatorDto
        {
            Date = record.Date,
            ChlorophyllAProxy = record.EoChlorophyllA,
            Turbidity = record.EoTurbidity,
            TotalSuspendedMatterProxy = record.EoTotalSuspendedMatter,
            SurfaceTemperatureCelsius = record.EoSurfaceTemp,
            StudyTurbidityNtu = record.StudyTurbidityNtu,
            PredictedInSituTurbidity = record.PredictedInSituTurbidity,
            NitrateMgL = record.NitrateMgL,
            NitriteMgL = record.NitriteMgL,
            AmmoniumMgL = record.AmmoniumMgL,
            NutrientPressureIndex = record.NutrientPressureIndex,
            BloomRiskScore = record.BloomRiskScore,
            EutrophicationRiskScore = record.EutrophicationRiskScore,
            WaterQualityScore = record.WaterQualityScore,
            AlertLevel = record.AlertLevel,
            IsStudyActual = record.IsStudyActual,
            IsEoActual = record.IsEoActual
        };
    }

    public static TimeseriesPointDto ToTimeseriesPointDto(this WaterQualityRecord record)
    {
        return new TimeseriesPointDto
        {
            Date = record.Date,
            ChlorophyllAProxy = record.EoChlorophyllA,
            Turbidity = record.EoTurbidity,
            TotalSuspendedMatterProxy = record.EoTotalSuspendedMatter,
            SurfaceTemperatureCelsius = record.EoSurfaceTemp,
            BloomRiskScore = record.BloomRiskScore,
            EutrophicationRiskScore = record.EutrophicationRiskScore,
            WaterQualityScore = record.WaterQualityScore,
            PredictedInSituTurbidity = record.PredictedInSituTurbidity,
            AlertLevel = record.AlertLevel
        };
    }

    public static RiskSummaryDto ToRiskSummaryDto(this WaterQualityRecord record)
    {
        return new RiskSummaryDto
        {
            LakeId = "tarnita",
            LakeName = "Lacul Tarnița",
            CalculatedAtUtc = record.Date,
            BloomRiskScore = record.BloomRiskScore,
            EutrophicationRiskScore = record.EutrophicationRiskScore,
            WaterQualityScore = record.WaterQualityScore,
            RiskLevel = record.AlertLevel,
            Explanation = BuildExplanation(record)
        };
    }

    private static string BuildExplanation(WaterQualityRecord record)
    {
        return record.AlertLevel switch
        {
            "Normal" => "The latest CSV-derived indicators show normal water quality conditions for the MVP thresholds.",
            "Low" => "Minor water quality pressure detected, but the overall risk remains low.",
            "Medium" => "Moderate pressure detected from bloom, eutrophication, turbidity or nutrient-related features.",
            "High" => "High water quality pressure detected. Field validation is recommended.",
            "Critical" => "Critical water quality pressure detected. Immediate validation and investigation are recommended.",
            _ => $"Risk level reported as {record.AlertLevel}."
        };
    }
}