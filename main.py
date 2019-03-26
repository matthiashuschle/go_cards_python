from kivy.app import App
from kivy.lang import Builder
#from kivy.uix.checkbox import CheckBox, Button
from kivy.uix.button import Button
import storage


items = [
    {"color":(1, 1, 1, 1), "font_size": "20sp", "text": "white",     "input_data": ["some","random","data"]},
    {"color":(.5,1, 1, 1), "font_size": "30sp", "text": "lightblue", "input_data": [1,6,3]},
    {"color":(.5,.5,1, 1), "font_size": "40sp", "text": "blue",      "input_data": [64,16,9]},
    {"color":(.5,.5,.5,1), "font_size": "70sp", "text": "gray",      "input_data": [8766,13,6]},
    {"color":(1,.5,.5, 1), "font_size": "60sp", "text": "orange",    "input_data": [9,4,6]},
    {"color":(1, 1,.5, 1), "font_size": "50sp", "text": "yellow",    "input_data": [852,958,123]}
]


class MyButton(Button):

    def print_data(self, data):
        print(data)


class GoCardApp(App):

    def build(self):
        storage.create_tables()
        root = Builder.load_file('main.kv')
        root.data = items[:]
        return root

    def on_pause(self):
        pass
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    GoCardApp().run()
