import urllib.parse
import requests
from nicegui import app, ui
import os

VERIFY_SSL = os.getenv('VERIFY_SSL', False)
CORPOGRAFO_API_URL = os.getenv('CORPOGRAFO_API_URL', 'https://127.0.0.1:5000')

def api_post(endpoint, **json_args):
    response = requests.post(
        urllib.parse.urljoin(CORPOGRAFO_API_URL, endpoint),
        json=json_args,
        headers={'Authorization': f'Bearer {app.storage.user.get("access_token")}'},
        verify=VERIFY_SSL,
    )

    if response.status_code == 422:
        app.storage.user.clear()
        ui.navigate.to('/login')

    return response

def api_get(endpoint, **json_args):
    response = requests.get(
        urllib.parse.urljoin(CORPOGRAFO_API_URL, endpoint),
        json=json_args,
        headers={'Authorization': f'Bearer {app.storage.user.get("access_token")}'},
        verify=VERIFY_SSL,
    )

    if response.status_code == 422:
        app.storage.user.clear()
        ui.navigate.to('/login')

    return response