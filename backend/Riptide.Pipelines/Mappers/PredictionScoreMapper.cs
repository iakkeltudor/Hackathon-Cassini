using Riptide.Domain;
using Riptide.Pipelines.Models;

namespace Riptide.Pipelines.Mappers;

public static class PredictionScoreMapper
{
    public static WaterQualityRecord ToDomain(this PredictionScoresCsvRow row)
    {
        return new WaterQualityRecord
        {
            Date = row.Date,
            StudyTurbidityNtu = row.StudyTurbidityNtu,
            NitrateMgL = row.NitrateMgL,
            NitriteMgL = row.NitriteMgL,
            AmmoniumMgL = row.AmmoniumMgL,
            CalciumMgL = row.CalciumMgL,
            MagnesiumMgL = row.MagnesiumMgL,
            EoChlorophyllA = row.EoChlorophyllA,
            EoTurbidity = row.EoTurbidity,
            EoSurfaceTemp = row.EoSurfaceTemp,
            EoTotalSuspendedMatter = row.EoTotalSuspendedMatter,
            IsStudyActual = row.IsStudyActual,
            IsEoActual = row.IsEoActual,
            IsSummer = row.IsSummer,
            Month = row.Month,
            Quarter = row.Quarter,
            EoTurbidityLag1 = row.EoTurbidityLag1,
            EoTurbidityLag2 = row.EoTurbidityLag2,
            RollingEoChlorophyllA7d = row.RollingEoChlorophyllA7d,
            RollingEoTurbidity7d = row.RollingEoTurbidity7d,
            DeltaEoTemp3d = row.DeltaEoTemp3d,
            NutrientPressureIndex = row.NutrientPressureIndex,
            BloomPotentialFeature = row.BloomPotentialFeature,
            BloomRiskScore = row.BloomRiskScore,
            EutrophicationRiskScore = row.EutrophicationRiskScore,
            WaterQualityScore = row.WaterQualityScore,
            AlertLevel = row.AlertLevel,
            PredictedInSituTurbidity = row.PredictedInSituTurbidity
        };
    }
}