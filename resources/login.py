from typing import Optional
from util import notify_error, input_required
from util import api_request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui
import os
import requests
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

HCAPTCHA_SITEKEY = os.getenv("HCAPTCHA_SITEKEY")
HCAPTCHA_SECRETKEY = os.getenv("HCAPTCHA_SECRETKEY"),

unrestricted_page_routes = {'/login'}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        #print('-'*10)
        #print(app.storage.user)
        #print(request.url.path)
        #print(Client.page_routes)
        #print('-'*10)
        if not app.storage.user.get('access_token', False):
            if request.url.path not in unrestricted_page_routes and request.url.path in Client.page_routes.values():
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)


async def try_login(email, password, client) -> None:
    if True:  #await check_captcha(client):
        r = api_request('post', 'login', email=email.value, password=password.value)

        if r.status_code == 200:
            app.storage.user.update({'email': email.value, **r.json()})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            notify_error(r)
    else:
        ui.notify("Captcha not passed", color="negative")

async def try_register(name, email, client: Client) -> None:
    if True:  #await check_captcha(client):
        r = api_request('post', 'register', name=name.value, email=email.value, access_level=2)

        if r.status_code == 201:
            ui.notify(f'User successfully registered', color='positive')
            name.set_value("")
            email.set_value("")
        else:
            notify_error(r)
    else:
        ui.notify("Captcha not passed", color="negative")

async def check_captcha(client: Client) -> bool:
    h_captcha_response = await ui.run_javascript("get_hcaptcha_response();", timeout=5.0)
    ip = client.environ['asgi.scope']['client'][0]
    payload = {
        "secret": HCAPTCHA_SECRETKEY,
        "response": h_captcha_response,
        "remoteip": ip,
        "sitekey": HCAPTCHA_SITEKEY
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
                    register_name = ui.input('Name', validation=input_required)
                    register_name.validate()
                    register_email = ui.input('E-mail', validation=input_required)
                    register_email.validate()
                    ui.button('Register', on_click=lambda: try_register(register_name, register_email, client))

            #with ui.tab_panel('Reset'):
            #    with ui.card().classes('w-full items-center'):
            #        register_email = ui.input('E-mail').classes('w-full')
            #        #password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full')
            #        ui.button('Register', on_click=lambda: try_register(register_name, register_email, client))

        #ui.element("div").classes("h-captcha").props(f'data-sitekey="{HCAPTCHA_SITEKEY}" data-theme="light"')
        #print(ui.run_javascript("document.getElementsByClassName('h-captcha');", timeout=5.0))
        #print(ui.run_javascript("hcaptcha.render('h-captcha', {'sitekey': '" + HCAPTCHA_SITEKEY + "'});", timeout=5.0))

    return None
