from functools import partial
from nicegui import ui
from api_requests import api_get, api_post
from util import make_header_and_menu, notify_error, input_required

@ui.page('/document')
def list_documents() -> None:
    make_header_and_menu()

    user_documents = api_get('document').json()
    columns = [{'name': 'name', 'label': 'Name', 'field': 'name'}]  #[{'name': k, 'label': k, 'field': k} for k in user_documents[0]]

    with ui.card().classes('w-1/3 absolute-center items-center'):
        ui.label('Documents').style('font-size: 150%')

        documents_tbl = ui.table(
            columns=columns,
            rows=list(user_documents),
        ).on(
            'rowClick',
            lambda event: ui.navigate.to(f'/document/{event.args[-2]["id"]}')
        ).classes('w-full')

        with documents_tbl.add_slot('top-right'):
            documents_tbl.bind_filter(ui.input('Filter'), 'value')

def try_create_document(name, content):
    r = api_post('document', name=name.value, content=content.value)

    if r.status_code == 201:
        ui.notify('Operation successful', color='positive')

        name.set_value("")
        content.set_value("")
    else:
        notify_error(r)

@ui.page('/new_document')
def create_document() -> None:
    make_header_and_menu()
    with ui.card().classes('w-1/3 absolute-center items-center'):
        ui.label('New document').style('font-size: 150%')
        name = ui.input('Name', validation=input_required)
        name.validate()
        content = ui.textarea('Content').classes('w-full')
        ui.button('Create', on_click=partial(try_create_document, name, content))

async def show_add_to_corpus():
    with ui.dialog() as dialog, ui.card():
        corpus_name = ui.input('Which corpus?')

        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit(corpus_name.value)).classes(remove='w-full')
            ui.button('Cancel', on_click=lambda: dialog.submit(None)).classes(remove='w-full')

    corpus_name = await dialog
    ui.notify(f'You chose {corpus_name}')

@ui.page('/document/{document_id}')
def manage_document(document_id):
    make_header_and_menu()

    document = api_get(f'document/{document_id}').json()

    with ui.card().classes('absolute-center items-center'):
        ui.label(f"Document: {document['name']}").style('font-size: 150%')

        users_tbl = ui.table(
            title='Users',
            columns=[
                {'name': 'name', 'label':'Name', 'field': 'name'},
                {'name': 'email', 'label':'E-mail', 'field': 'email'},
                {'name': 'unshare', 'label':'', 'field': ''},
            ],
            rows=document['users'],
        ).props('bordered').classes('w-max')

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

        users_tbl.on('unshare', lambda event: print(event))

        with users_tbl.add_slot('top-right'):
            with ui.column().classes('items-right'):
                ui.button('Share')
                users_tbl.bind_filter(ui.input('Filter'), 'value')

        corpora_tbl = ui.table(
            title='Corpora',
            columns=[
                {'name': 'name', 'label':'Name', 'field': 'name'},
            ],
            rows=document['corpora'],
        ).props('bordered').classes('w-full')

        with corpora_tbl.add_slot('top-right'):
            with ui.column().classes('items-right'):
                ui.button('Add to corpus', on_click=show_add_to_corpus)
                corpora_tbl.bind_filter(ui.input('Filter'), 'value')