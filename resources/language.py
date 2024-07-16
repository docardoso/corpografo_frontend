
from nicegui import ui, events
import util

ui.page('/language')(util.make_generic_list_entity_page('language'))

ui.page('/new_language')(util.make_generic_new_entity_page('language', {'name': {'input_type': 'input'}}))

ui.page('/language/{entity_id}')(util.make_generic_detail_entity_page('language', {
    'name': {'input_type': 'input'},
    'documents': {'input_type': 'table', 'entity': 'document'},
}))