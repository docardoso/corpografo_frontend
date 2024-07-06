from nicegui import Client, app, ui
from functools import partial
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import RedirectResponse
import requests
from api_requests import api_post

input_required = {'Required': lambda value: len(value) > 0}

unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('access_token', False):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)

def notify_error(response):
    try:
        json = response.json()
        ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
    except requests.exceptions.JSONDecodeError:
        ui.notify(f'Operation failed: unexpected behavior', color='negative')

def try_logout() -> None:
    r = api_post('logout')
    app.storage.user.clear()
    if r.status_code == 200:
        ui.navigate.to('/login')
    else:
        notify_error(r)

def make_header_and_menu() -> None:
    with ui.left_drawer(value=False).classes('bg-blue-100') as left_drawer:
        ui.menu_item('Home', on_click=partial(ui.navigate.to, '/'))
        ui.separator()

        with ui.menu_item('Corpus'):
            with ui.menu() as menu:
                ui.menu_item('New', on_click=partial(ui.navigate.to, '/new_corpus'))
                ui.menu_item('List', on_click=partial(ui.navigate.to, '/corpus'))

        with ui.menu_item('Document'):
            with ui.menu() as menu:
                ui.menu_item('New', on_click=partial(ui.navigate.to, '/new_document'))
                ui.menu_item('List', on_click=partial(ui.navigate.to, '/document'))
        #for i in range(10):
        #    #ui.label(f'Item {i}')
        #    ui.menu_item(f'Item {i}', on_click=partial(ui.notify, f'Item {i}'))
        ui.separator()
        ui.menu_item('Logout', on_click=try_logout)

    with ui.header().classes(replace='row items-center'):
        ui.button(on_click=left_drawer.toggle, icon='menu').props('flat color=white').classes(remove='w-full')
        ui.label(f'Hello, {app.storage.user["name"]}!') #.classes('text-2xl')

