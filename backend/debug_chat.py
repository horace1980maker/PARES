import requests
import json

URL = "http://localhost:8001/chat"
PAYLOAD = {
    "organizacion": "TIERRA VIVA",
    "mensaje": "¿Dónde se ubican los ecosistemas principales?",
    "pais": "Ecuador"
}

try:
    print(f"Sending request to {URL}...")
    response = requests.post(URL, json=PAYLOAD)
    print(f"Status Code: {response.status_code}")
    print("Raw Response:")
    print(response.text)
    
    if response.status_code == 200:
        data = response.json()
        print("\nParsed JSON:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
