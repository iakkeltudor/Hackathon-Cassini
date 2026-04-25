import requests
url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter=Collection/Name eq 'SENTINEL-2' and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON ((23.2 46.7, 23.3 46.7, 23.3 46.8, 23.2 46.8, 23.2 46.7))') and ContentDate/Start ge 2023-08-01T00:00:00.000Z and ContentDate/Start le 2023-08-30T00:00:00.000Z and Attributes/OData.CSC.StringAttribute/any(att:att/Name eq 'productType' and att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')&$top=10"
res = requests.get(url).json()
print("Found", len(res.get('value', [])), "products!")
