import requests
import json

# Test the /api/users endpoint
api_key = 'dq3mzqUaL_WaKZEV7G64TCZKkPHIrCyNvAkCrl2sAa8'
headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}

print(f"Testing with API key: {api_key}")
print(f"Headers: {headers}")

try:
    response = requests.get('http://127.0.0.1:5000/api/users', headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"JSON Data: {json.dumps(data, indent=2)}")
    else:
        print(f"Error: {response.status_code}")
        
except Exception as e:
    print(f"Exception: {e}")

# Also test the health endpoint to make sure Flask is working
try:
    health_response = requests.get('http://127.0.0.1:5000/api/health')
    print(f"\nHealth check - Status: {health_response.status_code}, Response: {health_response.text}")
except Exception as e:
    print(f"Health check exception: {e}")