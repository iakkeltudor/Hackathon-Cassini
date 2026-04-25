using CsvHelper;
using CsvHelper.Configuration;
using Riptide.Application.Dtos;
using Riptide.Application.Interfaces;
using Riptide.Pipelines.Models;
using Riptide.Pipelines.Options;
using System.Globalization;

namespace Riptide.Pipelines.Services;

public sealed class WaterQualityService : IWaterQualityService
{
    private readonly StorageOptions _storageOptions;
    private readonly SemaphoreSlim _cacheLock = new(1,1);
    private IReadOnlyList<PredictionScoresCsvRow?> _cachedRows;
    private DateTime? _cachedLastWriteUtc;

    public WaterQualityService(StorageOptions storageOptions)
    {
        _storageOptions = storageOptions;
    }

    public async Task<IndicatorDto?> GetLatestIndicatorsAsync(CancellationToken ct = default)
    {
        var latest = await GetLatestRowAsync(ct);

        return latest is null ? null : ToIndicatorDto(latest);
    }

    public async Task<IReadOnlyList<TimeseriesPointDto>> GetTimeseriesAsync(DateTime? fromUtc = null, DateTime? toUtc = null,
        CancellationToken ct = default)
    {
        var rows = await GetRowsAsync(ct: ct);

        var query = rows.AsEnumerable();

        if (fromUtc.HasValue)
        {
            query = query.Where(x => x.Date >= fromUtc.Value);
        }

        if (toUtc.HasValue)
        {
            query = query.Where(x => x.Date <= toUtc.Value);
        }

        return query
            .OrderBy(x => x.Date)
            .Select(ToTimeseriesPointDto)
            .ToList();
    }

    public async Task<RiskSummaryDto?> GetRiskSummaryAsync(CancellationToken ct = default)
    {
        var latest = await GetLatestRowAsync(ct);

        return latest is null ? null : ToRiskSummaryDto(latest);
    }

    public async Task<IReadOnlyList<AlertDto>> GetAlertsAsync(CancellationToken ct = default)
    {
        var rows = await GetRowsAsync(ct);

        return rows
            .Where(ShouldCreateAlert)
            .OrderByDescending(x => x.Date)
            .SelectMany(ToAlerts)
            .ToList();
    }

    public async Task<IReadOnlyList<LayerDto>> GetLayersAsync(CancellationToken ct = default)
    {
        var rows = await GetRowsAsync(ct);

        if (rows.Count == 0) return [];

        var latest = rows.OrderByDescending(x => x.Date).First();

        return
        [
            new LayerDto
            {
                Id = "tarnita-chlorophyll-a",
                Name = "Chlorophyll-a proxy",
                LayerType = "chlorophyll-a",
                CapturedAtUtc = latest.Date,
                SourceFile = "Excel.csv",
                Format = "csv-derived",
                MinValue = rows.Min(x => x.EoChlorophyllA),
                MaxValue = rows.Max(x => x.EoChlorophyllA),
                IsMock = false
            },
            new LayerDto
            {
                Id = "tarnita-turbidity",
                Name = "Turbidity",
                LayerType = "turbidity",
                CapturedAtUtc = latest.Date,
                SourceFile = "Excel.csv",
                Format = "csv-derived",
                MinValue = rows.Min(x => x.EoTurbidity),
                MaxValue = rows.Max(x => x.EoTurbidity),
                IsMock = false
            },
            new LayerDto
            {
                Id = "tarnita-suspended-matter",
                Name = "Total suspended matter proxy",
                LayerType = "total-suspended-matter",
                CapturedAtUtc = latest.Date,
                SourceFile = "Excel.csv",
                Format = "csv-derived",
                MinValue = rows.Min(x => x.EoTotalSuspendedMatter),
                MaxValue = rows.Max(x => x.EoTotalSuspendedMatter),
                IsMock = false
            },
            new LayerDto
            {
                Id = "tarnita-water-quality-risk",
                Name = "Water quality risk",
                LayerType = "water-quality-risk",
                CapturedAtUtc = latest.Date,
                SourceFile = "Excel.csv",
                Format = "csv-derived",
                MinValue = rows.Min(x => x.WaterQualityScore),
                MaxValue = rows.Max(x => x.WaterQualityScore),
                IsMock = false
            }
        ];
    }

    public async Task<DashboardDto> GetDashboardAsync(CancellationToken ct = default)
    {
        var latest = await GetLatestIndicatorsAsync(ct);
        var risk = await GetRiskSummaryAsync(ct);
        var timeseries = await GetTimeseriesAsync(ct: ct);
        var alerts = await GetAlertsAsync(ct);
        var layers = await GetLayersAsync(ct);

        return new DashboardDto
        {
            Lake = new LakeDto(),
            LatestIndicators = latest,
            RiskSummary = risk,
            Timeseries = timeseries,
            Alerts = alerts,
            Layers = layers
        };
    }

    #region PRIVATES

    private async Task<PredictionScoresCsvRow?> GetLatestRowAsync(CancellationToken ct)
    {
        var rows = await GetRowsAsync(ct);

        return rows
            .OrderByDescending(x => x.Date)
            .FirstOrDefault();
    }

    private async Task<IReadOnlyList<PredictionScoresCsvRow>> GetRowsAsync(CancellationToken ct)
    {
        var filePath = ResolveCsvPath();

        if (!File.Exists(filePath)) throw new FileNotFoundException("CSV File not found");

        var lastWriteUtc = File.GetLastWriteTime(filePath);

        if (_cachedRows is not null && _cachedLastWriteUtc == lastWriteUtc)
        {
            return _cachedRows;
        }

        await _cacheLock.WaitAsync(ct);

        try
        {
            if (_cachedRows is not null && _cachedLastWriteUtc == lastWriteUtc) return _cachedRows;

            var rows = await ReadCsvAsync(filePath, ct);

            _cachedRows = rows
                .OrderBy(x => x.Date)
                .ToList();

            _cachedLastWriteUtc = lastWriteUtc;

            return _cachedRows;
        }
        finally
        {
            _cacheLock.Release();
        }
    }

    private string ResolveCsvPath()
    {
        return Path.IsPathRooted(_storageOptions.CsvPath) ? 
            _storageOptions.CsvPath : 
            Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, _storageOptions.CsvPath));
    }

    private static async Task<IReadOnlyList<PredictionScoresCsvRow>> ReadCsvAsync(string filePath, CancellationToken ct)
    {
        await using var stream = File.OpenRead(filePath);
        using var reader = new StreamReader(stream);

        var config = new CsvConfiguration(CultureInfo.InvariantCulture)
        {
            HasHeaderRecord = true,
            MissingFieldFound = null,
            HeaderValidated = null,
            BadDataFound = null,
            TrimOptions = TrimOptions.Trim
        };

        using var csv = new CsvReader(reader, config);
        var rows = new List<PredictionScoresCsvRow>();

        await foreach (var row in csv.GetRecordsAsync<PredictionScoresCsvRow>(ct))
        {
            rows.Add(row);
        }

        return rows;
    }

    private static bool ShouldCreateAlert(PredictionScoresCsvRow row)
    {
        return row.AlertLevel is "Medium" or "High" or "Critical"
               || row.BloomRiskScore >= 60
               || row.EutrophicationRiskScore >= 60
               || row.WaterQualityScore < 60;
    }

    private static IReadOnlyList<AlertDto> ToAlerts(PredictionScoresCsvRow row)
    {
        var alerts = new List<AlertDto>();

        if (row.BloomRiskScore >= 60)
        {
            alerts.Add(new AlertDto
            {
                Date = row.Date,
                Severity = GetSeverityFromRisk(row.BloomRiskScore),
                Parameter = "Bloom risk",
                Message = "Elevated bloom risk detected for Tarnita",
                Value = row.BloomRiskScore,
                Threshold = 60
            });
        }

        if (row.EutrophicationRiskScore >= 60)
        {
            alerts.Add(new AlertDto
            {
                Date = row.Date,
                Severity = GetSeverityFromRisk(row.EutrophicationRiskScore),
                Parameter = "Eutrophication risk",
                Message = "Elevated eutrophication risk detected for Lacul Tarnița.",
                Value = row.EutrophicationRiskScore,
                Threshold = 60
            });
        }

        if (row.WaterQualityScore < 60)
        {
            alerts.Add(new AlertDto
            {
                Date = row.Date,
                Severity = row.WaterQualityScore < 40 ? "High" : "Medium",
                Parameter = "Water quality score",
                Message = "Water quality score dropped below the acceptable MVP threshold.",
                Value = row.WaterQualityScore,
                Threshold = 60
            });
        }

        if (alerts.Count == 0 && row.AlertLevel is "Medium" or "High" or "Critical")
        {
            alerts.Add(new AlertDto
            {
                Date = row.Date,
                Severity = row.AlertLevel,
                Parameter = "Overall risk",
                Message = $"Overall water quality alert level is {row.AlertLevel}.",
                Value = row.WaterQualityScore,
                Threshold = 60
            });
        }

        return alerts;
    }

    private static string GetSeverityFromRisk(double value)
    {
        return value switch
        {
            >= 85 => "Critical",
            >= 70 => "High",
            >= 60 => "Medium",
            _ => "Low"
        };
    }

    //internal mappers

    private static IndicatorDto ToIndicatorDto(PredictionScoresCsvRow row)
    {
        return new IndicatorDto
        {
            Date = row.Date,
            ChlorophyllAProxy = row.EoChlorophyllA,
            Turbidity = row.EoTurbidity,
            TotalSuspendedMatterProxy = row.EoTotalSuspendedMatter,
            SurfaceTemperatureCelsius = row.EoSurfaceTemp,
            StudyTurbidityNtu = row.StudyTurbidityNtu,
            PredictedInSituTurbidity = row.PredictedInSituTurbidity,
            NitrateMgL = row.NitrateMgL,
            NitriteMgL = row.NitriteMgL,
            AmmoniumMgL = row.AmmoniumMgL,
            NutrientPressureIndex = row.NutrientPressureIndex,
            BloomRiskScore = row.BloomRiskScore,
            EutrophicationRiskScore = row.EutrophicationRiskScore,
            WaterQualityScore = row.WaterQualityScore,
            AlertLevel = row.AlertLevel,
            IsStudyActual = row.IsStudyActual,
            IsEoActual = row.IsEoActual
        };
    }

    private static TimeseriesPointDto ToTimeseriesPointDto(PredictionScoresCsvRow row)
    {
        return new TimeseriesPointDto
        {
            Date = row.Date,
            ChlorophyllAProxy = row.EoChlorophyllA,
            Turbidity = row.EoTurbidity,
            TotalSuspendedMatterProxy = row.EoTotalSuspendedMatter,
            SurfaceTemperatureCelsius = row.EoSurfaceTemp,
            BloomRiskScore = row.BloomRiskScore,
            EutrophicationRiskScore = row.EutrophicationRiskScore,
            WaterQualityScore = row.WaterQualityScore,
            PredictedInSituTurbidity = row.PredictedInSituTurbidity,
            AlertLevel = row.AlertLevel
        };
    }

    private static RiskSummaryDto ToRiskSummaryDto(PredictionScoresCsvRow row)
    {
        return new RiskSummaryDto
        {
            LakeId = "tarnita",
            LakeName = "Lacul Tarnița",
            CalculatedAtUtc = row.Date,
            BloomRiskScore = row.BloomRiskScore,
            EutrophicationRiskScore = row.EutrophicationRiskScore,
            WaterQualityScore = row.WaterQualityScore,
            RiskLevel = row.AlertLevel,
            Explanation = BuildRiskExplanation(row)
        };
    }

    private static string BuildRiskExplanation(PredictionScoresCsvRow row)
    {
        return row.AlertLevel switch
        {
            "Normal" => "The latest water quality indicators are within normal MVP thresholds.",
            "Low" => "Low water quality pressure detected for Lacul Tarnița.",
            "Medium" => "Moderate pressure detected from bloom, eutrophication, turbidity or nutrient-related features.",
            "High" => "High water quality pressure detected. Field validation is recommended.",
            "Critical" => "Critical water quality pressure detected. Immediate validation and investigation are recommended.",
            _ => $"Risk level reported as {row.AlertLevel}."
        };
    }

    #endregion
}