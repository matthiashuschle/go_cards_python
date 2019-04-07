import os
import datetime
from kivy.uix.screenmanager import Screen
from kivy.logger import Logger
from kivy.properties import ObjectProperty
from storage import MIN_DATE, DT_FORMAT
from common import set_screen_active, get_screen, CardPopup, DeletePopup


class DebugScreen(Screen):

    text_out = ObjectProperty(None)

    def __init__(self, msg, **kwargs):
        super().__init__(**kwargs)
        self.set_text(msg)

    def set_text(self, msg):
        self.text_out.text = str(msg)
