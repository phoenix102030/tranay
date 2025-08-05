# tranay/tools/api_client.py

import requests

USER_ID = "686cc6029cd2bfe70bb8d126"

def get_all_projects(base_api_url):
    """Fetches all projects, returning a list of dicts with 'id' and 'name'."""
    # ... (This function's code remains unchanged)
    projects_list = []
    page = 1
    while True:
        endpoint = "/projects"
        params = {"user_id": USER_ID, "page": page, "page_size": 50}
        try:
            response = requests.get(base_api_url + endpoint, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            projects_on_page = data.get('projects', [])
            if not projects_on_page:
                break
            for p in projects_on_page:
                projects_list.append({'id': p['id'], 'name': p['name']})
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"API Client Error: Could not fetch projects. {e}")
            return []
    return projects_list


def get_sensor_data_for_project(base_api_url, project_id):
    """Fetches and processes sensor data for a given project ID."""
    # ... (This function's code remains unchanged)
    endpoint = f"/sensors"
    params = {'project_id': project_id}
    try:
        response = requests.get(base_api_url + endpoint, params=params, timeout=30)
        response.raise_for_status()
        sensor_data_raw = response.json()
        
        all_sensor_readings = []
        if sensor_data_raw and 'map' in sensor_data_raw and 'features' in sensor_data_raw['map']:
            for feature in sensor_data_raw['map']['features']:
                for reading in feature['properties'].get('data', []):
                    clean_document = {
                        "project_id": project_id,
                        "sensor_id": int(feature['properties']['id']),
                        "location": str(feature['geometry']['coordinates']),
                        "timestamp": reading["timestamp"],
                        "speed": reading.get("speed"),
                        "flow": reading.get("flow"),
                        "occupancy": reading.get("occupancy"),
                        "count": reading.get("count")
                    }
                    all_sensor_readings.append(clean_document)
        return all_sensor_readings
    except requests.exceptions.RequestException as e:
        print(f"API Client Error: Could not fetch sensor data for project {project_id}. {e}")
        return None
