from functools import partial
from nicegui import ui
from api_requests import api_request
from util import make_header_and_menu, notify_error, input_required, make_users_tbl, make_docs_corpora_tbl

@ui.page('/document')
def list_documents() -> None:
    make_header_and_menu()
    user_documents = api_request('get', 'document').json()

    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            documents_tbl = ui.table(
                title='Documents',
                columns=[
                    {'name': 'name', 'label': 'Name', 'field': 'name'}
                ],
                rows=list(user_documents),
                pagination=5,
            ).on(
                'rowClick',
                lambda event: ui.navigate.to(f'/document/{event.args[-2]["id"]}')
            ).classes('w-full')

            with documents_tbl.add_slot('top-right'):
                documents_tbl.bind_filter(ui.input('Filter'), 'value')

def try_create_document(name, content):
    r = api_request('post', 'document', name=name.value, content=content.value)

    if r.status_code == 201:
        ui.notify('Operation successful', color='positive')

        name.set_value("")
        content.set_value("")
    else:
        notify_error(r)

@ui.page('/new_document')
def create_document() -> None:
    make_header_and_menu()
    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):
            ui.label('New document').style('font-size: 150%')
            name = ui.input('Name', validation=input_required)
            name.validate()
            content = ui.textarea('Content').classes('w-full')
            ui.button('Create', on_click=partial(try_create_document, name, content))

@ui.page('/document/{document_id}')
def manage_document(document_id):

    @ui.refreshable
    def render_page():
        document = api_request('get', f'document/{document_id}').json()

        with ui.card().classes('w-1/2 h-5/6 absolute-center no-shadow'):
            with ui.scroll_area().classes('w-full h-full'):
                ui.label(f'Document: {document["name"]}').style('font-size: 150%')

                with ui.card().classes('items-center w-full'):
                    ui.textarea('Content', value=document['content']).classes('w-full')
                    #ui.button('Update').classes(remove='w-full')

                make_users_tbl(document['users'], 'document', document_id, render_page)

                make_docs_corpora_tbl('Corpora', 'corpus', document['corpora'], document_id, render_page)

    render_page()
    make_header_and_menu()