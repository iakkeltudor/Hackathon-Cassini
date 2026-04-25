namespace Riptide.Application.Dtos;

public sealed class LayerDto
{
    public string Id { get; set; } = Guid.NewGuid().ToString();

    public string Name { get; set; } = string.Empty;

    public string LayerType { get; set; } = string.Empty;

    public DateTime CapturedAtUtc { get; set; }

    public string SourceFile { get; set; } = "tarnita_predictions_scores.csv";

    public string Format { get; set; } = "csv-derived";

    public double? MinValue { get; set; }

    public double? MaxValue { get; set; }

    public bool IsMock { get; set; }    
}