
from nicegui import ui, events
import util

ui.page('/author')(util.make_generic_list_entity_page('author'))

ui.page('/new_author')(util.make_generic_new_entity_page('author', {
    'name': {'input_type': 'input'},
    'url': {'input_type': 'input'},
    'email': {'input_type': 'input'},
}))

ui.page('/author/{entity_id}')(util.make_generic_detail_entity_page('author', {
    'name': {'input_type': 'input'},
    'url': {'input_type': 'input'},
    'email': {'input_type': 'input'},
    'organization_id': {
        'input_type': 'select',
        'options_maker': lambda: {None: 'Undefined'} | {i['id']:i['name'] for i in util.api_request('get', 'organization').json()},
        'input_kwargs': {'label': 'Organization'},
        'entity': 'organization',
    },
    'documents': {
        'input_type': 'table',
        'entity': 'document',
        'link_endpoint': 'author/{reference_id}/document/{selected_id}',
    },
}))