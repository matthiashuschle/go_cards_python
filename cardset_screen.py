from kivy.uix.screenmanager import Screen
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView
from kivy.properties import BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from common import set_screen_active, get_screen


class CardListLabel(RecycleDataViewBehavior, BoxLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.card_id = None

    def refresh_view_attrs(self, rv, index, data):
        """ Catch and handle the view changes """
        # self.index = index
        self.card_id = data['card_id']
        btn_left = self.ids['btn_left']
        btn_right = self.ids['btn_right']
        btn_left.text = data['question']
        btn_right.text = data['answer']
        if index % 2 == 0:
            btn_left.background_color = [0.1, 0.1, 0.1, 1.]
            btn_right.background_color = [0.1, 0.1, 0.1, 1.]
        else:
            btn_left.background_color = [0., 0., 0., 1.]
            btn_right.background_color = [0., 0., 0., 1.]
        return super(CardListLabel, self).refresh_view_attrs(
            rv, index, data)

    def edit(self):
        print('in edit')
        get_screen('cardset').edit_card(self.card_id)


class CardRV(RecycleView):

    def __init__(self, storage, **kwargs):
        super(CardRV, self).__init__(**kwargs)
        self.storage = storage
        Logger.info('in RV')

    def reset_data(self):
        self.data = [{
            'set_name': x.name,
            'card_count': x.card_count,
            'active': x.active
        } for x in self.storage.card_sets]


class CardSetScreen(Screen):

    box_card_table = ObjectProperty(None)

    def __init__(self, storage, export_dir, **kwargs):
        super().__init__(**kwargs)
        self.storage = storage
        self.export_dir = export_dir
        self.current_set = None
        self.current_cards = None
        self.hide_known = False
        self.rv = CardRV(storage)
        self.box_card_table.add_widget(self.rv)
        # self.card_table = CardContainer(storage)
        # self.ids.card_table.add_widget(self.card_table)
        Logger.info('in CardSetScreen')

    def set_set_name(self, set_name):
        self.ids['title'].text = set_name
        set_data = [x for x in self.storage.card_sets if x.name == set_name]
        if len(set_data) != 1:
            return set_screen_active('manage')
        self.current_set = set_data[0]
        self.update_cards()

    def update_cards(self):
        self.current_cards = [x for x in self.storage.cards if x.card_set == self.current_set]
        self.rv.data = [{
            'card_id': card.card_id,
            'question': card.left,
            'answer': card.right
        } for card in self.current_cards]

    def edit_card(self, card_id):
        print('edit card', card_id)
