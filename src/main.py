import sys
import gi
from dbus import SystemBus as SystemMessageBus

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw

from .window import ApplicationWindow

APP_ID = 'net.hemish.pe'

def main(version, testing):
    if testing == '1' or testing == 1:
        print("running in testing")
        from .utils_testing import Service, list_modems, create_ussd_iface
    else:
        from .utils import Service, list_modems, create_ussd_iface

    class Application(Adw.Application):
        def __init__(self):
            super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
            self.create_action("about", self.about)
            self.upi_service = Service(create_ussd_iface(list_modems(SystemMessageBus())[0]), True)
        
        def about(self, *args):
            about_window = Gtk.Builder().new_from_resource('/net/hemish/pe/ui/about.ui').get_object("about_window")
            about_window.set_transient_for(self.props.active_window)
            about_window.present()

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
            
    app = Application()
    return app.run(sys.argv)
