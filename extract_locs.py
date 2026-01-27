import requests

unique_locations = []

with open('locs.txt', 'r', encoding='utf-8') as f:
    locs = f.readlines()

    for myloc in locs:
        myloc = myloc.strip()
        if myloc not in unique_locations:
            unique_locations.append(myloc)


geonames_username = 'sorinmarti'
base_url = "http://api.geonames.org/searchJSON"

for unique_location in unique_locations:
    print(f"Searching for location: {unique_location}")
    params = {
        "q": unique_location,
        "maxRows": 2,
        "username": "sorinmarti"
    }

    response = requests.get(base_url, params=params)
    first_item = response.json()['geonames'][0]

    data = {
        "location": unique_location,
        "geonames_id": first_item['geonameId'],
        "name": first_item['name'],
        "country": first_item['countryCode'],
        "latitude": first_item['lat'],
        "longitude": first_item['lng']
    }

    print(data)
    print()