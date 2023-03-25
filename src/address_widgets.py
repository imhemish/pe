# Address widgets to be used in Transaction View
# like UPI ID entry row, phone number entry row

from gi.repository import Gtk, Adw

# a common widget for UPI ID entry row and phone number entry row
class NormalWidget(Adw.EntryRow):
    def __init__(self, name, title, input_purpose):
        super().__init__()
        self.set_name(name)
        self.set_title(title)
        self.set_input_purpose(input_purpose)