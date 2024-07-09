from nicegui import app, ui
from functools import partial
import requests
from api_requests import api_request

input_required = {'Required': lambda value: len(value) > 0}

def notify_error(response):
    try:
        json = response.json()
        ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
    except requests.exceptions.JSONDecodeError:
        ui.notify(f'Operation failed: unexpected behavior', color='negative')

def try_logout() -> None:
    r = api_request('post', 'logout')
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


async def share_with_user(entity_name, entity_id, to_refresh):
    with ui.dialog() as dialog, ui.card():
        user_email = ui.input('E-mail')

        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit(user_email.value)).classes(remove='w-full')
            ui.button('Cancel', on_click=lambda: dialog.submit(None)).classes(remove='w-full')

    user_email = await dialog
    if user_email is not None:
        response = api_request('post', f'{entity_name}/{entity_id}/user/{user_email}')
        if response.status_code == 200:
            ui.notify('Operation successful', color='positive')
            to_refresh.refresh()
        else:
            notify_error(response)

def unshare_with_user(entity_name, entity_id, user_id, to_refresh):
    response = api_request('delete', f'{entity_name}/{entity_id}/user/{user_id}')
    if response.status_code == 200:
        ui.notify('Operation successful', color='positive')
        to_refresh.refresh()
    else:
        notify_error(response)

def make_users_tbl(rows, entity_name, entity_id, to_refresh):
    users_tbl = ui.table(
        title='Users',
        columns=[
            {'name': 'name', 'label':'Name', 'field': 'name'},
            {'name': 'email', 'label':'E-mail', 'field': 'email'},
            {'name': 'unshare', 'label':'', 'field': ''},
        ],
        rows=rows,
        pagination=5,
    ).props('bordered').classes('w-full')

    users_tbl.add_slot(
        'body',
        r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    <q-btn v-if="col.name == 'unshare'" @click="$parent.$emit('unshare', props.row)" label="Unshare" />
                    <span v-else>
                        {{ col.value }}
                    </span>
                </q-td>
            </q-tr>
        '''
    )

    users_tbl.on(
        'unshare',
        lambda event: unshare_with_user(entity_name, entity_id, event.args["id"], to_refresh)
    )

    with users_tbl.add_slot('top-right'):
        with ui.column().classes('items-right'):
            ui.button('Share', on_click=partial(share_with_user, entity_name, entity_id, to_refresh)).classes('w-full')
            users_tbl.bind_filter(ui.input('Filter'), 'value')


def make_docs_corpora_tbl(title, entity, rows, reference_id, to_refresh):
    tbl = ui.table(
        title=title,
        columns=[
            {'name': 'name', 'label':'Name', 'field': 'name'},
            {'name': 'operations', 'label':'', 'field': ''},
        ],
        rows=rows,
        pagination=5,
    ).props('bordered').classes('w-full')

    tbl.add_slot(
        'body',
        r'''
            <q-tr :props="props">
                <q-td v-for="col in props.cols" :key="col.name" :props="props">
                    <q-btn v-if="col.name == 'operations'" @click="$parent.$emit('unlink', props.row)" label="Unlink" />
                    <q-btn v-if="col.name == 'operations'" @click="$parent.$emit('view', props.row)" label="View" />
                    <span v-else>
                        {{ col.value }}
                    </span>
                </q-td>
            </q-tr>
        '''
    )

    if entity == 'corpus':
        tbl.on(
            'unlink',
            lambda event: unlink_corpus_document(reference_id, event.args["id"], to_refresh)
        )

    else:
        tbl.on(
            'unlink',
            lambda event: unlink_corpus_document(event.args["id"], reference_id, to_refresh)
        )

    tbl.on(
        'view',
        lambda event: ui.navigate.to(f'/{entity}/{event.args["id"]}')
    )

    with tbl.add_slot('top-right'):
        with ui.column().classes('items-right'):
            ui.button('Link document to corpus', on_click=partial(link_corpus_document, entity, reference_id, to_refresh)).classes('w-full')
            tbl.bind_filter(ui.input('Filter'), 'value')

async def link_corpus_document(query_entity, reference_id, to_refresh):
    with ui.dialog() as dialog, ui.card():
        #query_entity = 'corpus' if reference_entity == 'document' else 'document'
        user_entities = api_request('get', query_entity).json()
        selected_id = ui.select({i['id']: i['name'] for i in user_entities}, label=f'Which {query_entity}?', with_input=True)

        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit(selected_id.value))
            ui.button('Cancel', on_click=lambda: dialog.submit(None))

    selected_id = await dialog
    if selected_id is not None:
        if query_entity == 'corpus':
            corpus_id = selected_id
            document_id = reference_id
        else:
            corpus_id = reference_id
            document_id = selected_id

        response = api_request('post', f'corpus/{corpus_id}/document/{document_id}')
        if response.status_code == 200:
            ui.notify('Operation successful', color='positive')
            to_refresh.refresh()
        else:
            notify_error(response)

def unlink_corpus_document(document_id, corpus_id, to_refresh):
    response = api_request('delete', f'corpus/{corpus_id}/document/{document_id}')
    if response.status_code == 200:
        ui.notify('Operation successful', color='positive')
        to_refresh.refresh()
    else:
        notify_error(response)