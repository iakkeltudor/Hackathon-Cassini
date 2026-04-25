namespace Riptide.Application.Dtos;

public sealed class LakeDto
{
    public string Id { get; set; } = "tarnita";

    public string Name { get; set; } = "Lacul Tarnita";

    public string County { get; set; } = "Cluj";

    public string Country { get; set; } = "Romania";

    public string WaterBodyType { get; set; } = "Recreational reservoir";

    public double Latitude { get; set; } = 46.705;

    public double Longitude { get; set; } = 23.255;

    public string Description { get; set; } =
        "Pilot lake for water quality monitoring using CSV-derived Sentinel-style indicators and in-situ proxies.";
}