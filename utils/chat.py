import requests

BASE_URL = "https://find-doc-user-service-97b949dda34a.herokuapp.com"
BACKEND_URL = "https://find-doc-provider-service-2ea5236aec86.herokuapp.com/providers"

def login(email, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if response.status_code == 200:
        return response.json().get("token")
    return None

def search_providers(token, specialty, insurance, street, city, state, zip_code, radius=10):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "specialty": specialty,
        "insurance": insurance,
        "street": street,
        "city": city,
        "state": state,
        "zip": zip_code,
        "radius": radius
    }
    response = requests.post(f"{BACKEND_URL}/search", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()  # List of providers
    return None

def search_provider(token, provider_id) :
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "id": provider_id
    }
    response = requests.get(f"{BACKEND_URL}/search-provider?id={provider_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def book_appointment(token, provider_id, provider_first_name, provider_last_name, start_datetime, reason):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "provider_id": provider_id, 
        "provider_first_name": provider_first_name,
        "provider_last_name": provider_last_name,
        "start_datetime": start_datetime,
        "reason": reason,
    }
    response = requests.post(f"{BASE_URL}/users/appointment", json=payload, headers=headers)
    return response.status_code == 200

def provider_sched(token, providerId):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/provider_schedules/{providerId}", headers=headers)
    if response.status_code == 200:
        return response.json()

def fetch_user_appointments(token):
    """
    Fetches a user's appointments.
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get("appointments", [])
    return None

def cancel_user_appointment(token, appointment_id):
    """
    Cancels a user's appointment.
    """
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{BASE_URL}/users/appointment/{appointment_id}", headers=headers)
    return response.status_code == 200