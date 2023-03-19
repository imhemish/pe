from gi.repository import Gtk, Adw
from .menu_button import MenuButton

@Gtk.Template(resource_path="/net/hemish/pe/ui/success_view.ui")
class SuccessView(Gtk.Box):
    __gtype_name__ = "SuccessView"
    success_view_status: Adw.StatusPage = Gtk.Template.Child()
    success_view_back_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, text, back_callback):
        super().__init__()
        self.success_view_status.set_description(text)
        self.success_view_back_button.set_action_name('win.go_back_to_main_view')
        self.success_view_back_button.connect('clicked', back_callback)