import requests

base_url = "http://127.0.0.1:5000"

def test_api(route_from, route_to):
    url = f"{base_url}/api/route-price?from={route_from}&to={route_to}"
    print(f"Testing: {url}")
    try:
        response = requests.get(url)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Note: These will only work if the server is running.
    # Since I cannot easily start the server and wait for it in a script,
    # I will assume the server is NOT running and I will test by importing app logic if possible.
    
    # Actually, it's better to test the function logic directly.
    pass
