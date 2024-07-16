import os
import secrets

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from nicegui import app, ui

from util import api_request

from resources import *

from util import make_header_and_menu

from starlette.formparsers import MultiPartParser

MultiPartParser.max_file_size = 1024 * 1024 * 10  # 10 MB

app.add_middleware(login.AuthMiddleware)

NICEGUI_STORAGE_SECRET_KEY = os.getenv('NICEGUI_STORAGE_SECRET_KEY', str(secrets.SystemRandom().getrandbits(2**8)))

ui.menu_item.default_props('dense')
ui.menu_item.default_classes('w-full')
ui.input.default_classes('w-full')
#ui.button_group.default_classes('w-full')
#ui.button.default_classes('w-full')

@ui.page('/')
def main_page() -> None:
    make_header_and_menu()
    user_corpora = api_request('get', 'corpus').json()
    user_documents = api_request('get', 'document').json()

    with ui.card().classes('absolute-center items-center'):
        ui.label('Totals').style('font-size: 150%')
        ui.label(f'Corpora: {len(user_corpora)} items')
        ui.label(f'Documents: {len(user_documents)} items')


ui.run(
    host='0.0.0.0',
    #port=80,
    storage_secret=NICEGUI_STORAGE_SECRET_KEY,
    title = 'Corpografo (dev)',
)
