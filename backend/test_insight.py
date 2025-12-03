import requests
import json

def test_territorial_insight():
    url = "http://localhost:8001/territorial-insight"
    payload = {
        "lat": 4.5709,
        "lng": -74.2973,
        "location_name": "Colombia"
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_territorial_insight()
