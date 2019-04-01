from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from storage import CARD_TO_STRING, CARD_FROM_STRING, CARDSET_TO_STRING, CARDSET_FROM_STRING
import datetime


class DBElementPopup(Popup):

    id_map = {}

    def __init__(self, title, default_vals=None, db_object=None,
                 from_string_methods=None, to_string_methods=None, storage=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.storage = storage
        self.db_object = db_object
        self.default_vals = default_vals or {}
        if self.db_object is not None:
            self.default_vals = self.db_object.to_dict()
        self.from_string_methods = from_string_methods or {}
        self.to_string_methods = to_string_methods or {}
        self.populate_content()

    def populate_content(self):
        for cell_id, db_field in self.id_map.items():
            conversion_method = self.to_string_methods.get(db_field, str)
            try:
                field_val = ''
                if db_field in self.default_vals:
                    field_val = conversion_method(self.default_vals[db_field])
                self.ids[cell_id].text = field_val
            except KeyError:
                pass

    def alert(self, msg):
        try:
            self.ids['alert'].text = msg
        except KeyError:
            pass

    def save(self):
        value_dict = {}
        for cell_id, db_field in self.id_map.items():
            try:
                new_val = self.ids[cell_id].text.strip()
            except KeyError:
                continue
            if db_field in self.from_string_methods:
                try:
                    new_val = self.from_string_methods[db_field](new_val)
                except ValueError:
                    self.alert('invalid value for %s!' % db_field)
                    return
            value_dict[db_field] = new_val
        if self.validate_input(value_dict) and self.check_for_changes(value_dict):
            self.act_on_save(value_dict)
            self.dismiss()

    def check_for_changes(self, value_dict):
        if self.db_object is None:
            # new entry
            return True
        # edit existing
        db_vals = self.db_object.to_dict()
        if all(self.from_string_methods.get(key, str)(db_vals[key]) == val for key, val in value_dict.items()):
            self.alert('nothing changed!')
            return False
        return True

    def validate_input(self, value_dict):
        return True

    def act_on_save(self, value_dict):
        pass

    def cancel(self):
        self.dismiss()


class CardsetPopup(DBElementPopup):

    id_map = {
        'edit_name': 'name',
        'edit_description': 'description',
        'edit_qi': 'left_info',
        'edit_ai': 'right_info',
    }

    def __init__(self, title, from_string_methods=None, to_string_methods=None, **kwargs):
        super().__init__(
            title,
            from_string_methods=from_string_methods or CARDSET_FROM_STRING,
            to_string_methods=to_string_methods or CARDSET_TO_STRING,
            **kwargs
        )

    def validate_input(self, value_dict):
        existing_names = set(x.name for x in self.storage.card_sets)
        if not len(value_dict['name']):
            self.alert('no name given!')
            return False
        if len(value_dict['name']) and value_dict['name'] in existing_names:
            self.alert('name already exists!')
            return False
        return True


class CardPopup(DBElementPopup):

    id_map = {
        'edit_q': 'left',
        'edit_a': 'right',
        'edit_qi': 'left_info',
        'edit_ai': 'right_info',
        'edit_s': 'streak',
        'edit_hu': 'hidden_until'
    }

    def __init__(self, title, from_string_methods=None, to_string_methods=None, **kwargs):
        super().__init__(
            title,
            from_string_methods=from_string_methods or CARD_FROM_STRING,
            to_string_methods=to_string_methods or CARD_TO_STRING,
            **kwargs
        )
#
#
# class NewElementPopup(Popup):
#
#     id_map = {}
#
#     def __init__(self, title, default_vals=None, conversion=None, **kwargs):
#         super().__init__(**kwargs)
#         self.default_vals = default_vals or {}
#         self.title = title
#         self.conversion = conversion or {}
#         self.populate_content()
#
#     def populate_content(self):
#         for cell_id, db_field in self.id_map.items():
#             self.ids[cell_id].text = str(self.default_vals.get(db_field, ''))
#
#     def alert(self, msg):
#         try:
#             self.ids['alert'].text = msg
#         except KeyError:
#             pass
#
#     def save(self):
#         value_dict = {}
#         for cell_id, db_field in self.id_map.items():
#             new_val = self.ids[cell_id].text.strip()
#             if db_field in self.conversion:
#                 try:
#                     new_val = self.conversion[db_field](new_val)
#                 except ValueError:
#                     self.alert('invalid value for %s!' % db_field)
#                     return
#             value_dict[db_field] = new_val
#         if self.validate_input(value_dict):
#             self.act_on_save(value_dict)
#             self.dismiss()
#
#     def validate_input(self, value_dict):
#         return True
#
#     def act_on_save(self, value_dict):
#         pass
#
#     def cancel(self):
#         self.dismiss()
#
#
# class EditPopup(Popup):
#
#     id_map = {}
#
#     def __init__(self, db_object, title, conversion=None, **kwargs):
#         super().__init__(**kwargs)
#         self.db_object = db_object
#         self.title = title
#         self.conversion = conversion or {}
#         self.populate_content()
#
#     def populate_content(self):
#         val_dict = self.db_object.to_dict()
#         for cell_id, db_field in self.id_map.items():
#             self.ids[cell_id].text = str(val_dict[db_field])
#
#     def alert(self, msg):
#         try:
#             self.ids['alert'].text = msg
#         except KeyError:
#             pass
#
#     def save(self):
#         val_dict = self.db_object.to_dict()
#         changed = False
#         for cell_id, db_field in self.id_map.items():
#             new_val = self.ids[cell_id].text.strip()
#             if db_field in self.conversion:
#                 try:
#                     new_val = self.conversion[db_field](new_val)
#                 except ValueError:
#                     self.alert('invalid value for %s!' % db_field)
#                     return
#             if new_val != val_dict[db_field]:
#                 changed = True
#                 setattr(self.db_object, db_field, new_val)
#         if changed:
#             if self.validate_input(value_dict):
#                 self.act_on_edit()
#                 self.dismiss()
#             else:
#                 return
#         else:
#             self.alert('nothing changed!')
#
#     def act_on_edit(self):
#         pass
#
#     def validate_input(self, value_dict):
#         return True
#
#     def cancel(self):
#         self.dismiss()


class PopupLabelCell(Label):
    pass


def get_screen_manager():
    return App.get_running_app().root


def get_screen(name):
    return get_screen_manager().get_screen(name)


def set_screen_active(name):
    get_screen_manager().current = name
