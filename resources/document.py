from functools import partial
from nicegui import ui, events
import util
import base64

ui.page('/document')(util.make_generic_list_entity_page('document'))

def try_create_document(name, input_file):
    r = util.api_request('post', 'document', name=name, input_file=input_file)

    if r.status_code == 201:
        ui.navigate.to(f'/document/{r.json()["id"]}')
    else:
        util.notify_error(r)

def handle_upload(e: events.UploadEventArguments):
    try_create_document(e.name, base64.b64encode(e.content.read()).decode('utf8'))
    e.sender.reset()

@ui.page('/new_document')
def create_document() -> None:
    util.make_header_and_menu()
    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):
            ui.label('New document').style('font-size: 150%')
            ui.upload(label='Input file', auto_upload=True, on_upload=handle_upload).classes('w-full')
            #ui.label('Supported file types/extensions:')
            #for i in content_extractors:
            #    ui.label(i)

def make_menu_document_detailing(document_id):
    ui.menu_item('Dictionary', partial(ui.navigate.to, f'/dictionary/{document_id}'))
    ui.menu_item('Phrasing', partial(ui.navigate.to, f'/phrasing/{document_id}'))

ui.page('/document/{entity_id}')(util.make_generic_detail_entity_page(
    'document',
    {
        'name': {'input_type': 'input'},
        'language_id': {
            'input_type': 'select',
            'options_maker': lambda: {None: 'Undefined'} | {i['id']:i['name'] for i in util.api_request('get', 'language').json()},
            'input_kwargs': {'label': 'Language'},
            'entity': 'language',
        },
        'source_id': {
            'input_type': 'select',
            'options_maker': lambda: {None: 'Undefined'} | {i['id']:i['name'] for i in util.api_request('get', 'organization').json()},
            'input_kwargs': {'label': 'Source'},
            'entity': 'organization',
        },
        'publisher_id': {
            'input_type': 'select',
            'options_maker': lambda: {None: 'Undefined'} | {i['id']:i['name'] for i in util.api_request('get', 'organization').json()},
            'input_kwargs': {'label': 'Publisher'},
            'entity': 'organization',
        },
        'corpora': {
            'input_type': 'table',
            'entity': 'corpus',
            'link_endpoint': 'corpus/{selected_id}/document/{reference_id}',
        },
        'authors': {
            'input_type': 'table',
            'entity': 'author',
            'link_endpoint': 'author/{selected_id}/document/{reference_id}',
        },
        'content': {'input_type': 'textarea'},
        'citation': {'input_type': 'textarea'},
        #'users': {'input_type': 'table', 'entity': ''},
    },
    make_menu_document_detailing,
))

@ui.page('/phrasing/{document_id}')
def dictionary(document_id):
    util.make_header_and_menu()
    name, phrases = util.api_request('get', f'phrasing/{document_id}').json()

    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            ui.button('Detail document', on_click=partial(ui.navigate.to, f'/document/{document_id}'))

            table = ui.table(
                [
                    {'name': 'position', 'label': 'Position', 'field': 'position', 'sortable': True},
                    {'name': 'length',   'label': 'Length',   'field': 'length',   'sortable': True},
                    {'name': 'phrase',   'label': 'Phrase',   'field': 'phrase',   'sortable': True, 'align': 'left'},
                ],
                [{'position': j, 'phrase': i, 'length': len(i)} for j, i in enumerate(phrases, 1)],
                title=f'Phrasing: {name}',
                pagination=10,
            ).classes('w-full').props('wrap-cells')

            with table.add_slot('top-right'):
                table.bind_filter(ui.input('Filter'), 'value')

@ui.page('/dictionary/{document_id}')
def dictionary(document_id):
    util.make_header_and_menu()
    name, dictionary = util.api_request('get', f'dictionary/{document_id}').json()

    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            ui.button('Detail document', on_click=partial(ui.navigate.to, f'/document/{document_id}'))

            table = ui.table(
                [
                    {'name': 'term', 'label': 'Term', 'field': 'term', 'sortable': True},
                    {'name': 'frequency', 'label': 'Frequency', 'field': 'frequency', 'sortable': True},
                ],
                sorted(
                    [{'term': i[0], 'frequency': i[1]} for i in dictionary.items()],
                    key=lambda i: (i['frequency'], i['term']),
                    reverse=True
                ),
                title=f'Dictionary: {name}',
                pagination=10,
            ).classes('w-full')

            with table.add_slot('top-right'):
                table.bind_filter(ui.input('Filter'), 'value')

@ui.page('/document2/{document_id}')
def manage_document(document_id):

    inputs = ['name']
    textareas = ['citation', 'content']
    selects = ['language']

    @ui.refreshable
    def render_page():
        document = util.api_request('get', f'document/{document_id}').json()
        #print(list(document.keys()))
        #print(document['language'])

        with ui.card().classes('w-1/2 h-5/6 absolute-center no-shadow'):
            with ui.scroll_area().classes('w-full h-full'):
                #ui.label(f'Document: {document["name"]}').style('font-size: 150%')
                ui.label(f'Document detail').style('font-size: 150%')

                ui.button('Download input file', on_click=lambda: ui.download(base64.b64decode(document['input_file'].encode('utf-8')), document['name']))

                for i in inputs:
                    ui.input(i.title(), value=document[i]).classes('w-full')

                #for i in selects:
                #    ui.select()

                for i in textareas:
                    ui.textarea(i.title(), value=document[i]).classes('w-full')

                util.make_users_tbl(document['users'], 'document', document_id, render_page)

                util.make_docs_corpora_tbl('Corpora', 'corpus', document['corpora'], document_id, render_page)

    render_page()
    util.make_header_and_menu()