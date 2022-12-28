import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw

APP_ID = 'io.github.heymisphere.upi_ussd'

@Gtk.Template(filename='ui/ui/home.ui')
class HomeBox(Gtk.Box):
    __gtype_name__= "HomeBox"


@Gtk.Template(filename='ui/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"

    header_bar = Gtk.Template.Child()
    view_switcher_title = Gtk.Template.Child()
    view_switcher = Gtk.Template.Child()
    def __init__(self, **kwargs):
        Adw.ApplicationWindow.__init__(self, **kwargs)
    

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.create_action("about", self.about)
        self.create_action("bank", self.billa)
    
    def billa(self, *args):
        print("wow")

    def about(self, *args):
        about = Adw.AboutWindow()
        about.set_application_name("UPI USSD")
        about.set_developer_name("Hemish")
        about.set_application_icon("symbolic")
        about.set_website("https://github.com/heymisphere/upi-ussd")
        about.present()
    
    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ApplicationWindow(application=self)
        win.present()
    
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    app = Application()
    return app.run(sys.argv)

main(0.1)
