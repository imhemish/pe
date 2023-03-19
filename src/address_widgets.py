from gi.repository import Gtk, Adw

class NormalWidget(Adw.EntryRow):
    def __init__(self, name, title, input_purpose):
        super().__init__()
        self.set_name(name)
        self.set_title(title)
        self.set_input_purpose(input_purpose)