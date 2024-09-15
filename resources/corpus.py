import urllib.parse
from functools import partial
from nicegui import ui
from util import api_request
import util

ui.page('/corpus')(util.make_generic_list_entity_page('corpus', 'Corpora'))

ui.page('/new_corpus')(util.make_generic_new_entity_page('corpus', {'name': {'input_type': 'input'}}))

async def ngram_analysis_setup(corpus_id):
    with ui.dialog() as dialog, ui.card():
        ui.label('N-grams length')
        ngrams_range = ui.range(min=1, max=15, value={'min': 5, 'max': 10}).props('label snap switch-label-side')
        case_sensitive = ui.switch('Case sensitive?').props('left-label')

        with ui.row():
            ui.button('OK', on_click=lambda: dialog.submit((ngrams_range.value, case_sensitive.value))).classes(remove='w-full')
            ui.button('Cancel', on_click=lambda: dialog.submit(None)).classes(remove='w-full')

    settings = await dialog

    if settings is not None:
        ui.navigate.to(f'/ngram/{corpus_id}/{settings[0]["min"]}/{settings[0]["max"]}/{settings[1]}')

async def regex_matching_setup(corpus_id):
    with ui.dialog() as dialog, ui.card():
        regex = ui.input('Regular Expression')
        ui.label('Context')
        window_context = ui.toggle({True: 'Window', False:'Phrase'}, value=False)
        with ui.column().classes('w-full').bind_visibility(window_context, 'value'):
            ui.label('Left window size')
            left_window_size = ui.slider(min=0, max=15, value=0).props('label snap switch-label-side')
            ui.label('Right window size')
            right_window_size = ui.slider(min=0, max=15, value=0).props('label snap switch-label-side')
        case_sensitive = ui.switch('Case sensitive?').props('left-label')

        with ui.row():
            ui.button(
                'OK',
                on_click=lambda: dialog.submit((
                    window_context.value,
                    regex.value,
                    case_sensitive.value,
                    left_window_size.value,
                    right_window_size.value,
                ))
            ).classes(remove='w-full')
            ui.button('Cancel', on_click=lambda: dialog.submit(None)).classes(remove='w-full')

    settings = await dialog

    if settings is not None:
        #ui.notify(settings)
        if settings[0]:
            ui.navigate.to(f'/regex_window/{corpus_id}/{urllib.parse.quote(settings[1])}/{settings[2]}/{settings[3]}/{settings[4]}')
        else:
            ui.navigate.to(f'/regex_phrases/{corpus_id}/{urllib.parse.quote(settings[1])}/{settings[2]}')

def make_menu_corpus_detailing(corpus_id):
    ui.menu_item('N-grams analysis', partial(ngram_analysis_setup, corpus_id), auto_close=False)
    ui.menu_item('Regex matching', partial(regex_matching_setup, corpus_id), auto_close=False)

ui.page('/corpus/{entity_id}')(util.make_generic_detail_entity_page(
    'corpus',
    {
        'name': {'input_type': 'input'},
        'documents': {'input_type': 'table', 'picker': 'document'},
        #'users': {'input_type': 'table', 'picker': 'document'},
        'documents': {
            'input_type': 'table',
            'entity': 'document',
            'link_endpoint': 'corpus/{reference_id}/document/{selected_id}',
        },
    },
    make_menu_corpus_detailing,
))

@ui.page('/ngram/{corpus_id:int}/{min_len:int}/{max_len:int}/{case_sensitive}')
def manage_corpus(corpus_id, min_len, max_len, case_sensitive):
    util.make_header_and_menu()

    name, ngrams = util.api_request('get', f'/ngram/{corpus_id}/{min_len}/{max_len}/{case_sensitive}').json()

    with ui.card().classes('w-2/3 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            ui.button('Detail corpus', on_click=partial(ui.navigate.to, f'/corpus/{corpus_id}'))

            table = ui.table(
                [
                    {'name': 'ngram', 'label': 'N-gram', 'field': 'ngram', 'sortable': True},
                    {'name': 'frequency', 'label': 'Frequency', 'field': 'frequency', 'sortable': True},
                ],
                sorted(
                    [{'ngram': i[0], 'frequency': i[1]} for i in ngrams.items()],
                    key=lambda i: (i['frequency'], i['ngram']),
                    reverse=True
                ),
                #title=f'N-grams ({min_len-1} < N < {max_len+1}): {name}',
                title=f'N-grams: {name}',
                pagination=10,
            ).classes('w-full')

            with table.add_slot('top-right'):
                table.bind_filter(ui.input('Filter'), 'value')

@ui.page('/regex_window/{corpus_id:int}/{regex}/{case_sensitive}/{left_window_size:int}/{right_window_size:int}')
def regex_window(corpus_id, regex, case_sensitive, left_window_size, right_window_size):
    util.make_header_and_menu()

    name, matches = util.api_request('get', f'/regex_window/{corpus_id}/{regex}/{case_sensitive}/{left_window_size}/{right_window_size}').json()

    with ui.card().classes('w-2/3 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            ui.button('Detail corpus', on_click=partial(ui.navigate.to, f'/corpus/{corpus_id}'))

            table = ui.table(
                [
                    {'name': 'match', 'label': 'Match', 'field': 'match', 'sortable': True},
                    {'name': 'frequency', 'label': 'Frequency', 'field': 'frequency', 'sortable': True},
                ],
                sorted(
                    [{'match': i[0], 'frequency': i[1]} for i in matches.items()],
                    key=lambda i: (i['frequency'], i['match']),
                    reverse=True
                ),
                title=f'Regex matching (window): {name}, {regex}',
                pagination=10,
            ).classes('w-full').props('wrap-cells')

            with table.add_slot('top-right'):
                table.bind_filter(ui.input('Filter'), 'value')

            #for i, phrase in enumerate(phrases):
            #    with ui.teleport(f'#c{table.id} tr:nth-child({i+1}) td:nth-child(3)'):
            #        ui.html(f'<b>{phrase}</b>')

@ui.page('/regex_phrases/{corpus_id:int}/{regex}/{case_sensitive}')
def regex_phrases(corpus_id, regex, case_sensitive):
    util.make_header_and_menu()

    name, matches = util.api_request('get', f'/regex_phrases/{corpus_id}/{regex}/{case_sensitive}').json()

    with ui.card().classes('w-2/3 h-5/6 absolute-center items-center no-shadow'):
        with ui.scroll_area().classes('w-full h-full'):

            ui.button('Detail corpus', on_click=partial(ui.navigate.to, f'/corpus/{corpus_id}'))

            table = ui.table(
                [
                    {'name': 'position', 'label': 'Position', 'field': 'position', 'sortable': True},
                    {'name': 'length',   'label': 'Length',   'field': 'length',   'sortable': True},
                    {'name': 'phrase',   'label': 'Phrase',   'field': 'phrase',   'sortable': True, 'align': 'left'},
                ],
                [{'position': j, 'phrase': i, 'length': len(i)} for j, i in enumerate(matches, 1)],
                title=f'Regex matching (phrases): {name}, {regex}',
                pagination=10,
            ).classes('w-full').props('wrap-cells')

            with table.add_slot('top-right'):
                table.bind_filter(ui.input('Filter'), 'value')

            #for i, phrase in enumerate(phrases):
            #    with ui.teleport(f'#c{table.id} tr:nth-child({i+1}) td:nth-child(3)'):
            #        ui.html(f'<b>{phrase}</b>')
