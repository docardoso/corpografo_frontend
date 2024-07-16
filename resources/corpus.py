from functools import partial
from nicegui import ui
from util import api_request
import util

ui.page('/corpus')(util.make_generic_list_entity_page('corpus', 'Corpora'))

ui.page('/new_corpus')(util.make_generic_new_entity_page('corpus', {'name': {'input_type': 'input'}}))

ui.page('/corpus/{entity_id}')(util.make_generic_detail_entity_page('corpus', {
    'name': {'input_type': 'input'},
    'documents': {'input_type': 'table', 'picker': 'document'},
    #'users': {'input_type': 'table', 'picker': 'document'},
    'documents': {
        'input_type': 'table',
        'entity': 'document',
        'link_endpoint': 'corpus/{reference_id}/document/{selected_id}',
    },
}))


@ui.page('/corpus2/{corpus_id}')
def manage_corpus(corpus_id):

    @ui.refreshable
    def render_page():
        corpus = api_request('get', f'corpus/{corpus_id}').json()

        with ui.card().classes('w-1/2 h-5/6 absolute-center no-shadow'):
            with ui.scroll_area().classes('w-full h-full'):
                ui.label(f"Corpus: {corpus['name']}").style('font-size: 150%')

                util.make_users_tbl(corpus['users'], 'corpus', corpus_id, render_page)
                util.make_docs_corpora_tbl('Documents', 'document', corpus['documents'], corpus_id, render_page)

    render_page()
    util.make_header_and_menu()
