namespace Riptide.Application.Dtos;

public sealed class AlertDto
{
    public string Id { get; set; } = Guid.NewGuid().ToString();

    public DateTime Date { get; set; }

    public string Severity { get; set; } = "Low";

    public string Parameter { get; set; } = string.Empty;

    public string Message { get; set; } = string.Empty;

    public double Value { get; set; }

    public double Threshold { get; set; }

    public bool IsAcknowledged { get; set; }
}