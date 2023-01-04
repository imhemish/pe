import sys
import gi
import dbus
import threading
import dbus

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw

from utils import Service, list_modems, create_ussd_iface

APP_ID = 'io.github.heymisphere.pe'

@Gtk.Template(filename='ui/ui/pinentry.ui')
class PinEntry(Adw.MessageDialog):
    __gtype_name__ = "PinEntry"
    gtk_entry = Gtk.Template.Child()
    def __init__(self, parent):
        super().__init__(transient_for=parent)
        self.add_response("ok", "OK")
        self.set_response_enabled('ok', 'cancel')
        self.set_response_appearance('ok', Adw.ResponseAppearance.SUGGESTED)
        self.add_response("cancel", "Cancel")
        self.set_response_appearance('cancel', Adw.ResponseAppearance.DESTRUCTIVE)

@Gtk.Template(filename='ui/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    root_stack: Gtk.Stack = Gtk.Template.Child()

    transaction_view: Gtk.StackPage = Gtk.Template.Child()
    transaction_view_back_button = Gtk.Template.Child()
    transaction_view_cancel: Gtk.Button = Gtk.Template.Child()
    transaction_view_send: Gtk.Button = Gtk.Template.Child()
    transaction_view_amount = Gtk.Template.Child()
    transaction_view_address_box: Gtk.Box = Gtk.Template.Child()
    success_view_back_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_action("check_balance", self._check_balance)


        # Append main view to main gui
        main_view_builder = Gtk.Builder.new_from_file("ui/ui/main_view.ui")
        main_view_box = main_view_builder.get_object("main_view_box")
        self.main_view_home_send: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_send")
        self.main_view_home_balance_row = main_view_builder.get_object("main_view_home_balance_row")

        # self.main_view is a Gtk.StackPage returned by add_named method
        self.main_view = self.root_stack.add_named(main_view_box, 'main')
        self.root_stack.set_visible_child_name('main')
        self.transaction_view_cancel.connect('clicked', self.go_back_to_main_view)
        self.transaction_view_back_button.connect('clicked', self.go_back_to_main_view)
        self.success_view_back_button.connect('clicked', self.go_back_to_main_view)
    
    def _check_balance(self, *args):
        spinner = Gtk.Spinner()
        spinner.start()

        # Remove existing child widget, e.g. previous spinner or balance label
        try:
            self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
        except:
            pass

        self.main_view_home_balance_row.child_widget = spinner
        self.main_view_home_balance_row.add_suffix(self.main_view_home_balance_row.child_widget)
        
        def when_response_given(pinentry, response):
            if response == 'ok':
                pin = pinentry.gtk_entry.get_text()
                try:
                    balance = self.get_application().upi_service.check_balance(pin)
                    self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
                    del pin
                    label = Gtk.Label()
                    label.set_label("₹" + balance)
                    spinner.stop()
                    self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
                    self.main_view_home_balance_row.child_widget = label
                    self.main_view_home_balance_row.add_suffix(self.main_view_home_balance_row.child_widget)
                except dbus.DBusException:
                    print('dbus exception happened')
                    self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
            elif response == 'cancel':
                self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)

        def when_response_given_wrapper_thread(pinentry, response):
            thread = threading.Thread(group= None, target=when_response_given, kwargs={"pinentry": pinentry, "response": response})
            thread.start()

        pinentry_dialog = PinEntry(self)
        pinentry_dialog.connect('response', when_response_given_wrapper_thread)
        pinentry_dialog.present()

    
    def go_back_to_main_view(self, *args):
        self.root_stack.set_visible_child_name("main")

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"win.{name}", shortcuts)

class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.create_action("about", self.about)
        #self.upi_service = Service(create_ussd_iface(list_modems(dbus.SystemBus())[0]), True)
    
    def about(self, *args):
        builder = Gtk.Builder().new_from_file("ui/ui/about.ui")
        about: Gtk.Window = builder.get_object("about_window")
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