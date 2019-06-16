# A UI for the client to use the dfs
import sys
import time
import kivy
import wx
from functools import partial
from kivy.core.window import Window
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import StringProperty, BooleanProperty
from kivy.clock import Clock

from messaging import combine_dirtext
kivy.require('1.10.1')


exit_red = 0.85, 0.15, 0.2, 1
button_col = 0.7, 0.8, 0.8, 1
black = 0, 0, 0, 1
green = 0.26, 0.95, 0.40, 1
file_background = 189 / 255, 229 / 255, 237 / 255, 1
grey = 81 / 255, 226 / 255, 1, 1
white = 0.7, 0.8, 0.8, 1  # white
text_input_color = 2/255, 221/255, 237/255, 1

app = wx.App(False)
wxwidth, wxheight = wx.GetDisplaySize()
window_width, window_height = 700 / 1920 * wxwidth, 700 / 1080 * wxheight
Window.size = (window_width, window_height)
Window.borderless = True
Window.clearcolor = white  # stops black flicker on transition

msg_q = None

gui = f"""
AppScreenManager:
    MainScreen:
        name: 'main'
        id: main_id

    SettingsScreen:
        name: 'settings'
        id: settings_id

<SettingsScreen>:
    canvas.before:
        Color:
            rgb: {white}
        Rectangle:
            pos: self.pos
            size: self.size
    RelativeLayout:
        Button:
            text: 'x'
            color: {black}
            background_color: {exit_red}
            background_normal: ''
            size_hint: 0.05, 0.05
            pos: {window_width - 0.05* window_width}, {window_height - window_height*0.05}
            on_release:
                app.exit()
        Button:
            text: 'main'
            color: {black}
            background_color: {green}
            background_normal: ''
            size_hint: 0.1, 0.05
            pos: {window_width - 0.15* window_width}, {window_height - window_height*0.05}
            on_release:
                root.manager.transition.direction = 'up'
                root.manager.current='main'
        Label:
            text: 'Enter username:'
            color: {black}
            size_hint: 0.29, 0.1
            valign: 'center'
            halign: 'left'
            text_size: self.size
            font_size: 19
            pos: {window_width*0.05}, {window_height/2 + 0.2*window_height - 21}
        Label:
            text: 'Enter password:'
            color: {black}
            size_hint: 0.29, 0.1
            valign: 'center'
            halign: 'left'
            text_size: self.size
            font_size: 19
            pos: {window_width*0.05}, {window_height/2 -21}
        TextInput:
            id: username_textinput_id
            background_color: {text_input_color}
            background_normal: ''
            size_hint: 0.7, 0.1
            font_size: 25
            text_size: self.size
            padding_y: 20
            pos: {window_width*0.05+21}, {window_height/2 + 0.1*window_height -20}
            multiline: False        
            on_text_validate:
                app.username = self.text
            
        TextInput:
            id: password_textinput_id
            password: True
            password_mask:'•'
            background_color: {text_input_color}
            background_normal: ''
            size_hint: 0.7, 0.1
            font_size: 25
            text_size: self.size
            padding_y: 20
            pos: {window_width*0.05 +21}, {window_height/2 -22 - 0.1*window_height}
            multiline: False
            on_text_validate:
                app.password = self.text
                app.set_logins()
            



<MainScreen>:
    canvas.before:
        Color:
            rgb: {white}
        Rectangle:
            pos: self.pos
            size: self.size
    RelativeLayout:
        Button:
            text: 'x'
            color: {black}
            background_color: {exit_red}
            background_normal: ''
            size_hint: 0.05, 0.05
            pos: {window_width - 0.05* window_width}, {window_height - window_height*0.05}
            on_release:
                app.exit()
        Button:
            text: 'login'
            color: {black}
            background_color: {green}
            background_normal: ''
            size_hint: 0.1, 0.05
            pos: {window_width - 0.15* window_width}, {window_height - window_height*0.05}
            on_release:
                root.manager.transition.direction = 'down'
                root.manager.current='settings'
        BoxLayout:
            size_hint: 1, 0.1
            pos: 0, 0.5
            canvas.before:
                Color:
                    rgb: {black}
                Rectangle:
                    pos: self.pos
                    size: self.size
            TextInput:
                id: textin
                focus: True
                background_color: {black}
                foreground_color:{white}
                cursor_color: 1, 1, 1, 1
                color: 1, 1, 1, 1
                multiline: False
                on_text_validate:
                    root.sent_cmd(self.text)
                    self.text =''
                    self.focus = True
                    root.reselect(textin)


        Label:
            color: {black}
            text: ' dir: ' +app.curr_dir
            bold: True
            text_size: self.size
            valign: 'center'
            halign: 'left'
            size_hint: 0.67, 0.05
            pos: 0, {0.95*window_height}

        Label:
            color: {black}
            text: 'output:' 
            text_size: self.size
            valign: 'center'
            halign: 'left'
            size_hint: 0.67, 0.05
            pos: {0.67*window_width} , {0.95*window_height}

        BoxLayout:

            size_hint: 0.67, 0.85
            pos: {0.67*window_width} , {0.1 * window_height}
            canvas.before:
                Color:
                    rgb: {grey}
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                color: {black}
                text: root.out
                text_size: self.size
                valign: 'bottom'
                halign: 'left' 
                multiline: True

        BoxLayout:

            size_hint: 0.67, 0.85
            pos: 0, {0.1 * window_height}
            canvas.before:
                Color:
                    rgb: {file_background}
                Rectangle:
                    pos: self.pos
                    size: self.size
            TextInput:
                id:id_file_input
                color: {black}
                padding: (10, 5)
                text: app.files
                text_size: self.size
                valign: 'top'
                halign: 'left' 
                multiline: True
                disabled: app.disable_input
                background_disabled_normal: ''
                disabled_color: ''
                disabled_foreground_color: {black}
"""

app_curr_dir = ''

class AppScreenManager(ScreenManager):
    pass


class SettingsScreen(Screen):
    pass


# Declare screens
class MainScreen(Screen):
    out = StringProperty('')
    prev_out = out

    def sent_cmd(self, txt):
        print("entered " + txt)
        if txt == '':
            txt = ' '
        if txt == 'sv':
            # user wants to save their current file
            txt = f'sv {self.ids.id_file_input.text}'
        msg_q.put(combine_dirtext(app_curr_dir, txt))  # only forward message if originates from user
        self.out = self.prev_out + '\n' + '>' + txt     # use log_id if plan to show server/client chat
        self.prev_out = self.out
        return txt



    def reselect(self, textinref):
        Clock.schedule_once(partial(self.keep_blinking, textinref), .5)

    def keep_blinking(self, textinref, *args):
        textinref.focus = True

    def exit(self):
        msg_q.put()
        sys.exit()


class AppClass(App):
    files = StringProperty("enter 'home' to begin")
    curr_dir = StringProperty('~')
    global app_curr_dir
    username = StringProperty()
    password = StringProperty()
    disable_input = BooleanProperty()

    def build(self):
        global app_curr_dir
        app_curr_dir = self.curr_dir
        self.set_disable_input(True)    # on startup, editing is disabled
        self.title = 'DFS'
        return Builder.load_string(gui)

    def update_files(self, new):
        self.files = new

    def get_disable_input(self):
        return self.disable_input

    def set_disable_input(self, newval):
        # turn on or off textinput
        self.disable_input = newval

    def update_curr_dir(self, new_dir):
        global app_curr_dir
        self.curr_dir = new_dir
        app_curr_dir = new_dir

    def exit(self):
        print("putting into q")
        msg_q.put('close')
        print("closing app")
        time.sleep(0.5)         # TODO: is this sleep needed - probably not? remove it?
        self.stop()

    def setlogins(self):
        pass
        # TODO: make it so that this saves the username and password into a file where they can be read by the
        # dfsbackend and by the user to stay signed in when reopening the app. have textinputs display username/password
        # values on startup of terminal UI


def start():
    app_instance = AppClass()
    app_instance.run()

# start()
# use pyinstaller --noconsole -- onefile UI.py

