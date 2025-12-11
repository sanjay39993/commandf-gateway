import requests

try:
    response = requests.get('http://127.0.0.1:5000/api/health')
    print(f"Health Status Code: {response.status_code}")
    print(f"Health Response: {response.text}")
except Exception as e:
    print(f"Health Exception: {e}")