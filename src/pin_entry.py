from gi.repository import Gtk, Adw
from .menu_button import MenuButton

@Gtk.Template(resource_path='/net/hemish/pe/ui/pin_entry.ui')
class PinEntry(Gtk.Box):
    __gtype_name__ = "PinEntry"
    pinentry_view_entry_row: Adw.PasswordEntryRow = Gtk.Template.Child()
    pinentry_view_back_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, back_connect, apply_connect):
        super().__init__()
        self.pinentry_view_back_button.connect('clicked', back_connect)
        self.pinentry_view_entry_row.connect('apply', apply_connect)