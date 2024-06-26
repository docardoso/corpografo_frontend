from typing import Optional

from functools import partial

import urllib.parse
import os
import requests
import secrets
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from nicegui import Client, app, ui

NICEGUI_STORAGE_SECRET_KEY = os.getenv('NICEGUI_STORAGE_SECRET_KEY', str(secrets.SystemRandom().getrandbits(2**8)))
CORPOGRAFO_API_URL = os.getenv('CORPOGRAFO_API_URL', 'https://127.0.0.1:5000')
VERIFY_SSL = os.getenv('VERIFY_SSL', False)

unrestricted_page_routes = {'/login'}

ui.menu_item.default_props('dense')
ui.menu_item.default_classes('w-full')
ui.input.default_classes('w-full')


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('access_token', False):
            if request.url.path in Client.page_routes.values() and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)


app.add_middleware(AuthMiddleware)

def try_logout() -> None:
    r = requests.post(
        urllib.parse.urljoin(CORPOGRAFO_API_URL, 'logout'),
        headers={'Authorization': f'Bearer {app.storage.user.get("access_token")}'},
        verify=VERIFY_SSL,
    )
    app.storage.user.clear()
    if r.status_code == 200:
        ui.navigate.to('/login')
    else:
        try:
            json = r.json()
            ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
        except requests.exceptions.JSONDecodeError:
            ui.notify(f'Operation failed: unexpected behavior', color='negative')

@ui.page('/')
def main_page() -> None:
    make_header_and_menu()

def make_header_and_menu() -> None:
    with ui.left_drawer(value=False).classes('bg-blue-100') as left_drawer:
        ui.menu_item('Home', on_click=partial(ui.navigate.to, '/'))
        ui.separator()

        with ui.menu_item('Corpus'):
            with ui.menu() as menu:
                ui.menu_item('Create', on_click=partial(ui.navigate.to, '/create_corpus'))
                ui.menu_item('Manage', on_click=partial(ui.navigate.to, '/manage_corpus'))
        #for i in range(10):
        #    #ui.label(f'Item {i}')
        #    ui.menu_item(f'Item {i}', on_click=partial(ui.notify, f'Item {i}'))
        ui.separator()
        ui.menu_item('Logout', on_click=try_logout)


    with ui.header().classes(replace='row items-center'):
        ui.button(on_click=left_drawer.toggle, icon='menu').props('flat color=white')
        ui.label(f'Hello, {app.storage.user["name"]}!') #.classes('text-2xl')


@ui.page('/create_corpus')
def create_corpus() -> None:
    make_header_and_menu()
    with ui.card().classes('w-96 absolute-center items-center'):
        ui.label('New corpus: basic information')
        corpus_name = ui.input('Name', validation={'Required': lambda value: len(value) > 0})
        corpus_name.validate()
        ui.button('Create', on_click=partial(try_create_corpus, corpus_name))

def try_create_corpus(name):
    r = requests.post(
        urllib.parse.urljoin(CORPOGRAFO_API_URL, 'corpus'),
        json={
            'name': name.value,
        },
        headers={'Authorization': f'Bearer {app.storage.user.get("access_token")}'},
        verify=VERIFY_SSL,
    )

    if r.status_code == 201:
        ui.notify('Operation successful', color='positive')
    else:
        try:
            json = r.json()
            ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
        except requests.exceptions.JSONDecodeError:
            ui.notify(f'Operation failed: unexpected behavior', color='negative')



@ui.page('/manage_corpus')
def manage_corpus() -> None:
    make_header_and_menu()
    ui.label('MANAGE CORPUS.')

async def try_login(email, password, client) -> None:
    #print('oi'*10)
    #print('email:', id(email))
    if await check_captcha(client):
        r = requests.post(
            urllib.parse.urljoin(CORPOGRAFO_API_URL, 'login'),
            json={
                'email': email.value,
                'password': password.value,
            },
            verify=VERIFY_SSL,
        )

        json = r.json()
        #print(json)
        #print(r.status_code)
        if r.status_code == 200:
            app.storage.user.update({'email': email.value, **json})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
    else:
        ui.notify("Captcha not passed", color="negative")

async def try_register(name, email, client: Client) -> None:
    if await check_captcha(client):
        r = requests.post(
            urllib.parse.urljoin(CORPOGRAFO_API_URL, 'register'),
            json={
                'name': name.value,
                'email': email.value,
                'access_level': 2,
            },
            verify=VERIFY_SSL,
        )

        json = r.json()
        if r.status_code == 201:
            ui.notify(f'User successfully registered', color='positive')
            name.set_value(None)
            email.set_value(None)
        else:
            ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
    else:
        ui.notify("Captcha not passed", color="negative")

async def check_captcha(client: Client) -> bool:
    h_captcha_response = await ui.run_javascript("get_hcaptcha_response();")
    ip = client.environ['asgi.scope']['client'][0]
    payload = {
        "secret": os.getenv("HCAPTCHA_SECRETKEY"),
        "response": h_captcha_response,
        "remoteip": ip,
        "sitekey": os.getenv("HCAPTCHA_SITEKEY")
    }
    res = requests.post(url="https://api.hcaptcha.com/siteverify", data=payload)
    try:
        res = res.json()
        if res.get("success", False):
            return True
        else:
            ui.notify(f"hCaptcha Error: {','.join(res.get('error-codes', []))}")
    except Exception as e:
        print(repr(e))
        return False

@ui.page('/login')
def login(client: Client) -> Optional[RedirectResponse]:
    ui.add_head_html("""
        <script src="https://js.hcaptcha.com/1/api.js" async defer></script>
        <script>get_hcaptcha_response = () => {return document.getElementsByTagName("iframe")[0].attributes.getNamedItem("data-hcaptcha-response").nodeValue;}</script>
    """)

    if app.storage.user.get('access_token', False):
        return RedirectResponse('/')

    with ui.tabs().classes('w-full') as tabs:
        ui.tab('Login')
        ui.tab('Register')
        #ui.tab('Reset', label='Reset my password')

    with ui.column().classes('fixed-center items-center'):
        with ui.tab_panels(tabs, value='Login').classes('w-96'):
            with ui.tab_panel('Login'):
                with ui.card().classes('w-full items-center'):
                    email_login = ui.input('E-mail')  #.on('keydown.enter', js_handler='alert("asaaoks");')
                    password_login = ui.input('Password', password=True, password_toggle_button=True)  #.on('keydown.enter', try_login)
                    ui.button('Log in', on_click=lambda: try_login(email_login, password_login, client))

            with ui.tab_panel('Register'):
                with ui.card().classes('w-full items-center'):
                    register_name = ui.input('Name')
                    register_email = ui.input('E-mail')
                    ui.button('Register', on_click=lambda: try_register(register_name, register_email, client))

            #with ui.tab_panel('Reset'):
            #    with ui.card().classes('w-full items-center'):
            #        register_email = ui.input('E-mail').classes('w-full')
            #        #password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full')
            #        ui.button('Register', on_click=lambda: try_register(register_name, register_email, client))

        ui.element("div").classes("h-captcha").props(f'data-sitekey="{os.getenv("HCAPTCHA_SITEKEY")}" data-theme="light"')

    return None


ui.run(
    host='0.0.0.0',
    #port=80,
    storage_secret=NICEGUI_STORAGE_SECRET_KEY,
    title = 'Corpografo (dev)',
)
