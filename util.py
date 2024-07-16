import util
from nicegui import app, ui
from functools import partial
import requests, urllib, os

from collections.abc import Callable
from typing import Any

VERIFY_SSL = os.getenv('VERIFY_SSL', False)
CORPOGRAFO_API_URL = os.getenv('CORPOGRAFO_API_URL', 'https://127.0.0.1:5000')

input_required = {'Required': lambda value: len(value) > 0}

def notify_error(response: requests.Response):
    print('ERRO!!!'*22)
    print(response.content)
    try:
        json = response.json()
        ui.notify(f'Operation failed: {json.get("message", json)}', color='negative')
    except requests.exceptions.JSONDecodeError:
        ui.notify(f'Operation failed: unexpected behavior', color='negative')

def api_request(method, endpoint, **json_args):
    response = requests.request(
        method,
        urllib.parse.urljoin(CORPOGRAFO_API_URL, endpoint),
        json=json_args,
        headers={'Authorization': f'Bearer {app.storage.user.get("access_token")}'},
        verify=VERIFY_SSL,
    )

    if response.status_code // 100 != 2:
        notify_error(response)
        if response.status_code == 422 and response.json().get('msg') in set(['Signature verification failed', 'Not enough segments']):
            app.storage.user.clear()
            ui.navigate.to('/login')

    return response

def logout() -> None:
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

        with ui.menu_item('Language'):
            with ui.menu() as menu:
                ui.menu_item('New', on_click=partial(ui.navigate.to, '/new_language'))
                ui.menu_item('List', on_click=partial(ui.navigate.to, '/language'))

        with ui.menu_item('Organization'):
            with ui.menu() as menu:
                ui.menu_item('New', on_click=partial(ui.navigate.to, '/new_organization'))
                ui.menu_item('List', on_click=partial(ui.navigate.to, '/organization'))

        with ui.menu_item('Author'):
            with ui.menu() as menu:
                ui.menu_item('New', on_click=partial(ui.navigate.to, '/new_author'))
                ui.menu_item('List', on_click=partial(ui.navigate.to, '/author'))

        ui.separator()
        ui.menu_item('Logout', on_click=logout)

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
        print(user_entities)
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

def make_generic_list_entity_page(entity: str, table_title: str | None = None) -> Callable[[], None]:
    if table_title is None:
        table_title = entity.capitalize() + 's'

    def list_entity() -> None:
        make_header_and_menu()
        entity_collection = api_request('get', entity).json()

        with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
            with ui.scroll_area().classes('w-full h-full'):

                table = ui.table(
                    title=table_title,
                    columns=[
                        {'name': 'name', 'label': 'Name', 'field': 'name'}
                    ],
                    rows=list(entity_collection),
                    pagination=10,
                ).on(
                    'rowClick',
                    lambda event: ui.navigate.to(f'/{entity}/{event.args[-2]["id"]}')
                ).classes('w-full')

                with table.add_slot('top-right'):
                    table.bind_filter(ui.input('Filter'), 'value')

    return list_entity


def create_entity(entity, fields):
    r = api_request('post', entity, **{i: fields[i]['input'].value for i in fields})

    if r.status_code == 201:
        ui.navigate.to(f'/{entity}/{r.json()["id"]}')
    else:
        util.notify_error(r)

def make_generic_new_entity_page(entity: str, fields: dict[str, dict[str, Any]]) -> Callable[[], None]:
    def create_entity_page() -> None:
        util.make_header_and_menu()
        with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
            with ui.scroll_area().classes('w-full h-full'):
                ui.label(f'New {entity}').style('font-size: 150%')

                for i in fields:
                    if fields[i]['input_type'] == 'input':
                        fields[i]['input'] = ui.input(i.capitalize())

                ui.button('Create', on_click=partial(create_entity, entity, fields))

    return create_entity_page

def update_entity(entity, entity_id, fields):
    r = api_request('put', f'{entity}/{entity_id}', **{i: fields[i]['input'].value for i in fields if fields[i]['input_type'] != 'table'})

    if r.status_code == 200:
        ui.notify('Operation successful', color='positive')
    else:
        util.notify_error(r)

async def link_entities(query_entity:str, endpoint_spec:str, reference_id:int, refresh:Callable):
    with ui.dialog() as dialog, ui.card():
        #query_entity = 'corpus' if reference_entity == 'document' else 'document'
        user_entities = api_request('get', query_entity).json()
        print(user_entities)
        selected_id = ui.select({i['id']: i['name'] for i in user_entities}, label=f'Which {query_entity}?', with_input=True)

        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit(selected_id.value))
            ui.button('Cancel', on_click=lambda: dialog.submit(None))

    selected_id = await dialog
    if selected_id is not None:
        response = api_request('post', endpoint_spec.format(reference_id=reference_id, selected_id=selected_id))
        if response.status_code == 200:
            ui.notify('Operation successful', color='positive')
            refresh()
        else:
            notify_error(response)

def unlink_entities(endpoint, refresh):
    response = api_request('delete', endpoint)
    if response.status_code == 200:
        ui.notify('Operation successful', color='positive')
        refresh()
    else:
        notify_error(response)


def make_generic_detail_entity_page(entity: str, fields: dict[str, dict[str, Any]]) -> Callable[[int], None]:
    def detail_entity(entity_id):
        @ui.refreshable
        def render_page():
            entity_item = api_request('get', f'{entity}/{entity_id}').json()

            with ui.card().classes('w-1/2 h-5/6 absolute-center no-shadow'):
                with ui.scroll_area().classes('w-full h-full'):
                    ui.label(f'{entity.capitalize()} detail').style('font-size: 150%')

                    ui.button('Save changes', on_click=partial(update_entity, entity, entity_id, fields))

                    for i in fields:
                        if fields[i]['input_type'] == 'table':
                            tbl = ui.table(
                                title=i.capitalize(),
                                columns=[
                                    {'name': 'name', 'label':'Name', 'field': 'name'},
                                    {'name': 'operations', 'label':'', 'field': ''},
                                ],
                                rows=entity_item[i],
                                pagination=5,
                            ).props('bordered').classes('w-full')

                            operations_slot = r'''
                                <q-td :props="props" style="width:0%;">
                            '''

                            if 'link_endpoint' in fields[i]:
                                tbl.on(
                                    'unlink',
                                    partial(
                                        (lambda i, event: unlink_entities(fields[i]['link_endpoint'].format(selected_id=event.args["id"], reference_id=entity_id), render_page.refresh)),
                                        i,
                                    )
                                )

                                operations_slot += r'''
                                    <q-btn @click="$parent.$emit('unlink', props.row)" label="Unlink" />
                                '''

                            operations_slot += r'''
                                    <q-btn @click="$parent.$emit('view', props.row)" label="View" />
                                </q-td>
                            '''

                            tbl.add_slot('body-cell-operations', operations_slot)

                            tbl.on(
                                'view',
                                partial((lambda i, event: ui.navigate.to(f'/{fields[i]["entity"]}/{event.args["id"]}')), i),
                            )

                            with tbl.add_slot('top-right'):
                                with ui.column().classes('items-right'):
                                    if 'link_endpoint' in fields[i]:
                                        ui.button(
                                            'Link',
                                            on_click=partial(
                                                link_entities,
                                                fields[i]['entity'],
                                                fields[i]['link_endpoint'],
                                                entity_id,
                                                render_page.refresh,
                                            )
                                        ).classes('w-full')
                                    tbl.bind_filter(ui.input('Filter'), 'value')


                        elif fields[i]['input_type'] == 'select':
                            input_kwargs = dict(
                                options=fields[i]['options_maker'](),
                                label=i.capitalize(),
                                value=entity_item[i],
                                with_input=True,
                            )
                            input_kwargs |=  fields[i].get('input_kwargs', {})
                            if 'entity' in fields[i]:
                                with ui.row().classes('w-full'):
                                    fields[i]['input'] = ui.select(**input_kwargs).classes("grow")
                                    btn = ui.button(
                                        'Detail',
                                        on_click=partial(
                                            lambda i: ui.navigate.to(f'/{fields[i]["entity"]}/{fields[i]["input"].value}'),
                                            i,
                                        ),
                                    )

                                    btn.bind_visibility_from(fields[i]['input'], 'value', lambda x: x is not None)
                            else:
                                fields[i]['input'] = ui.select(**input_kwargs).classes('w-full')
                        else:
                            input_kwargs = dict(
                                label=i.capitalize(),
                                value=entity_item[i],
                            )
                            input_kwargs |=  fields[i].get('input_kwargs', {})
                            fields[i]['input'] = getattr(ui, fields[i]['input_type'])(**input_kwargs).classes('w-full')

        render_page()
        util.make_header_and_menu()
    return detail_entity