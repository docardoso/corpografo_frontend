from functools import partial
from nicegui import ui
from api_requests import api_get, api_post
from util import make_header_and_menu, notify_error, input_required

@ui.page('/corpus')
def list_corpora() -> None:
    make_header_and_menu()

    with ui.card().classes('w-1/3 absolute-center items-center'):
        ui.label('Corpora').style('font-size: 150%')

        user_corpora = api_get('corpus').json()
        columns = [{'name': 'name', 'label': 'Name', 'field': 'name'}]  #[{'name': k, 'label': k, 'field': k} for k in user_corpora[0]]

        corpora_tbl = ui.table(
            columns=columns,
            rows=list(user_corpora),
        ).on(
            'rowClick',
            lambda event: ui.navigate.to(f'/corpus/{event.args[-2]["id"]}')
        ).classes('w-full')

        with corpora_tbl.add_slot('top-right'):
            corpora_tbl.bind_filter(ui.input('Filter'), 'value')

def try_create_corpus(name):
    r = api_post('corpus', name=name.value)

    if r.status_code == 201:
        ui.notify('Operation successful', color='positive')

        name.set_value("")
    else:
        notify_error(r)

@ui.page('/new_corpus')
def create_corpus() -> None:
    make_header_and_menu()
    with ui.card().classes('w-1/2 absolute-center items-center'):
        ui.label('New corpus').style('font-size: 150%')
        corpus_name = ui.input('Name', validation=input_required)
        corpus_name.validate()
        ui.button('Create', on_click=partial(try_create_corpus, corpus_name))

@ui.page('/corpus/{corpus_id}')
def manage_corpus(corpus_id):
    make_header_and_menu()

    corpus = api_get(f'corpus/{corpus_id}').json()

    with ui.card().classes('absolute-center items-center'):
        ui.label(f"Corpus: {corpus['name']}").style('font-size: 150%')

        users_tbl = ui.table(
            title='Users',
            columns=[
                {'name': 'name', 'label':'Name', 'field': 'name'},
                {'name': 'email', 'label':'E-mail', 'field': 'email'},
                {'name': 'unshare', 'label':'', 'field': ''},
            ],
            rows=corpus['users'],
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

        docs_tbl = ui.table(
            title='Documents',
            columns=[
                {'name': 'remove_doc', 'label':'', 'field': ''},
                {'name': 'name', 'label':'Name', 'field': 'name'},
            ],
            rows=corpus['documents'],
        ).props('bordered').classes('w-full')

        docs_tbl.add_slot(
            'body',
            r'''
                <q-tr :props="props">
                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                        <q-btn v-if="col.name == 'remove_doc'" @click="$parent.$emit('remove_doc', props.row)" label="Remove" />
                        <span v-else>
                            {{ col.value }}
                        </span>
                    </q-td>
                </q-tr>
            '''
        )

        docs_tbl.on('remove_doc', lambda event: print(event))

        with docs_tbl.add_slot('top-right'):
            with ui.column().classes('items-right'):
                ui.button('Add document')
                docs_tbl.bind_filter(ui.input('Filter'), 'value')