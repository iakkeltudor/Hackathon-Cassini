using Microsoft.AspNetCore.Mvc;
using Riptide.Application.Dtos;
using Riptide.Application.Interfaces;

namespace Riptide.API.Controllers;

[ApiController]
public sealed class LakeController : ControllerBase
{
    private readonly IWaterQualityService _waterQualityService;

    public LakeController(IWaterQualityService waterQualityService)
    {
        _waterQualityService = waterQualityService;
    }

    [HttpGet("/lake")]
    public IActionResult GetLake() => Ok(new LakeDto());

    [HttpGet("/indicators/latest")]
    public async Task<IActionResult> GetLatestIndicators(CancellationToken cancellationToken)
    {
        var result = await _waterQualityService.GetLatestIndicatorsAsync(cancellationToken);

        return result is null ? NotFound("No indicator data was found.") : Ok(result);
    }

    [HttpGet("/indicators/timeseries")]
    public async Task<IActionResult> GetTimeseries(
        [FromQuery] DateTime? fromUtc,
        [FromQuery] DateTime? toUtc,
        CancellationToken cancellationToken)
    {
        var result = await _waterQualityService.GetTimeseriesAsync(
            fromUtc,
            toUtc,
            cancellationToken);

        return Ok(result);
    }

    [HttpGet("/risk/summary")]
    public async Task<IActionResult> GetRiskSummary(CancellationToken cancellationToken)
    {
        var result = await _waterQualityService.GetRiskSummaryAsync(cancellationToken);

        return result is null ? NotFound("No risk summary data was found.") : Ok(result);
    }

    [HttpGet("/alerts")]
    public async Task<IActionResult> GetAlerts(CancellationToken cancellationToken)
    {
        var result = await _waterQualityService.GetAlertsAsync(cancellationToken);

        return Ok(result);
    }

    [HttpGet("/layers")]
    public async Task<IActionResult> GetLayers(CancellationToken cancellationToken)
    {
        var result = await _waterQualityService.GetLayersAsync(cancellationToken);

        return Ok(result);
    }

    [HttpGet("/dashboard")]
    public async Task<IActionResult> GetDashboard(CancellationToken cancellationToken)
    {
        var result = await _waterQualityService.GetDashboardAsync(cancellationToken);

        return Ok(result);
    }
}