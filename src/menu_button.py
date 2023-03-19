from gi.repository import Gtk, Gio

@Gtk.Template(resource_path="/net/hemish/pe/ui/menu_button.ui")
class MenuButton(Gtk.MenuButton):
    __gtype_name__ = "MenuButton"
    def __init__(self):
        super().__init__()