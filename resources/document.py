from nicegui import ui, events
import util
import pathlib
import base64
import pypdf
import bs4
import docx

ui.page('/document')(util.make_generic_list_entity_page('document'))

def try_create_document(name, content, input_file):
    r = util.api_request('post', 'document', name=name, content=content, input_file=input_file)

    if r.status_code == 201:
        ui.navigate.to(f'/document/{r.json()["id"]}')
    else:
        util.notify_error(r)

content_extractors = {
    '.txt':  lambda content_file, raw_content: raw_content.decode('utf-8'),
    '.pdf':  lambda content_file, raw_content: '\n'.join(i.extract_text() for i in pypdf.PdfReader(content_file).pages),
    '.html': lambda content_file, raw_content: bs4.BeautifulSoup(raw_content.decode('utf-8')).get_text(),
    '.htm':  lambda content_file, raw_content: bs4.BeautifulSoup(raw_content.decode('utf-8')).get_text(),
    '.docx': lambda content_file, raw_content: '\n'.join(i.text for i in docx.Document(content_file).paragraphs),
}

def handle_upload(e: events.UploadEventArguments):
    try:
        extractor = content_extractors[pathlib.Path(e.name).suffix]
    except KeyError:
        ui.notify('Unknown file type', type='negative')
        return

    raw_content = e.content.read()
    content = extractor(e.content, raw_content)

    try_create_document(e.name, content, base64.b64encode(raw_content).decode('utf8'))
    e.sender.reset()

@ui.page('/new_document')
def create_document() -> None:
    util.make_header_and_menu()
    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):
            ui.label('New document').style('font-size: 150%')
            ui.upload(label='Input file', auto_upload=True, on_upload=handle_upload).classes('w-full')
            ui.label('Supported file types/extensions:')
            for i in content_extractors:
                ui.label(i)

ui.page('/document/{entity_id}')(util.make_generic_detail_entity_page('document', {
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
}))

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