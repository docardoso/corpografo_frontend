
from nicegui import ui, events
import util

ui.page('/organization')(util.make_generic_list_entity_page('organization'))

ui.page('/new_organization')(util.make_generic_new_entity_page('organization', {
    'name': {'input_type': 'input'},
    'url': {'input_type': 'input'},
    'email': {'input_type': 'input'},
}))

ui.page('/organization/{entity_id}')(util.make_generic_detail_entity_page('organization', {
    'name': {'input_type': 'input'},
    'url': {'input_type': 'input'},
    'email': {'input_type': 'input'},
    'documents': {'input_type': 'table', 'entity': 'document'},
}))