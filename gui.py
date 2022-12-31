import sys
import gi
import dbus
import time

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw

from utils import Service, list_modems, create_ussd_iface

APP_ID = 'io.github.heymisphere.upi_ussd'

@Gtk.Template(filename='ui/ui/pinentry.ui')
class PinEntry(Adw.MessageDialog):
    __gtype_name__ = "PinEntry"
    gtk_entry = Gtk.Template.Child()
    def __init__(self, parent):
        super().__init__(transient_for=parent)
        self.add_response("ok", "OK")
        self.add_response("cancel", "Cancel")

@Gtk.Template(filename='ui/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    back_button = Gtk.Template.Child()
    home_stack = Gtk.Template.Child()
    stack_page_loading = Gtk.Template.Child()
    spinner = Gtk.Template.Child()
    balance_row = Gtk.Template.Child()
    def __init__(self, **kwargs):
        Adw.ApplicationWindow.__init__(self, **kwargs)
        #self.home_stack.set_visible_child_name("loading")

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.create_action("about", self.about)
        self.create_action("bank", self.billa)
        self.create_action("settings_stack", self.settings_stack)
        self.upi_service = Service(create_ussd_iface(list_modems(dbus.SystemBus())[0]), True)
        self.create_action("check_balance", self._check_balance)
    
    def _check_balance(self, *args):
        spinner = Gtk.Spinner()
        spinner.start()
        self.props.active_window.balance_row.spinner = spinner
        self.props.active_window.balance_row.add_suffix(self.props.active_window.balance_row.spinner)
        
        def when_response_given(pinentry, response):
            pin = pinentry.gtk_entry.get_text()
            balance = self.upi_service.check_balance(pin)
            label = Gtk.Label()
            label.set_label("₹" + balance)
            spinner.stop()
            self.props.active_window.balance_row.remove(self.props.active_window.balance_row.spinner)
            self.props.active_window.balance_row.add_suffix(label)

        pinentry_dialog = PinEntry(self.props.active_window)
        pinentry_dialog.connect('response', when_response_given)
        pinentry_dialog.present()

    def settings_stack(self, *args):
        pass
        #self.props.active_window.home_stack.set_visible_child_name("stack_page_done")
    
    def billa(self, *args):
        print("wow")

    def about(self, *args):
        builder = Gtk.Builder().new_from_file("ui/ui/about.ui")
        about = builder.get_object("about_window")
        about.set_transient_for(self.props.active_window)
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
