from gi.repository import Gtk, Adw
from .menu_button import MenuButton

@Gtk.Template(resource_path="/io/github/imhemish/pe/ui/success_view.ui")
class SuccessView(Gtk.Box):
    __gtype_name__ = "SuccessView"
    success_view_status: Adw.StatusPage = Gtk.Template.Child()

    def __init__(self, text):
        super().__init__()
        self.success_view_status.set_description(text)