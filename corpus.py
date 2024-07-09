from functools import partial
from nicegui import ui
from api_requests import api_request  #api_get, api_post
from util import make_header_and_menu, notify_error, input_required, make_users_tbl, make_docs_corpora_tbl

@ui.page('/corpus')
def list_corpora() -> None:
    make_header_and_menu()
    user_corpora = api_request('get', 'corpus').json()

    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            corpora_tbl = ui.table(
                title='Corpora',
                columns=[
                    {'name': 'name', 'label': 'Name', 'field': 'name'}
                ],
                rows=list(user_corpora),
                pagination=5,
            ).on(
                'rowClick',
                lambda event: ui.navigate.to(f'/corpus/{event.args[-2]["id"]}')
            ).classes('w-full')

            with corpora_tbl.add_slot('top-right'):
                corpora_tbl.bind_filter(ui.input('Filter'), 'value')

def try_create_corpus(name):
    r = api_request('post', 'corpus', name=name.value)

    if r.status_code == 201:
        ui.notify('Operation successful', color='positive')

        name.set_value("")
    else:
        notify_error(r)

@ui.page('/new_corpus')
def create_corpus() -> None:
    make_header_and_menu()
    with ui.card().classes('w-1/2 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):
            ui.label('New corpus').style('font-size: 150%')
            corpus_name = ui.input('Name', validation=input_required)
            corpus_name.validate()
            ui.button('Create', on_click=partial(try_create_corpus, corpus_name))

@ui.page('/corpus/{corpus_id}')
def manage_corpus(corpus_id):

    @ui.refreshable
    def render_page():
        corpus = api_request('get', f'corpus/{corpus_id}').json()

        with ui.card().classes('w-1/2 h-5/6 absolute-center no-shadow'):
            with ui.scroll_area().classes('w-full h-full'):
                ui.label(f"Corpus: {corpus['name']}").style('font-size: 150%')

                make_users_tbl(corpus['users'], 'corpus', corpus_id, render_page)
                make_docs_corpora_tbl('Documents', 'document', corpus['documents'], corpus_id, render_page)

    render_page()
    make_header_and_menu()
