import sys
import gi
import dbus

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw

from .utils import Service, list_modems, create_ussd_iface

APP_ID = 'io.github.heymisphere.pe'


@Gtk.Template(resource_path='/io/github/imhemish/pe/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    root_stack: Gtk.Stack = Gtk.Template.Child()

    transaction_view: Gtk.StackPage = Gtk.Template.Child()
    transaction_view_back_button = Gtk.Template.Child()
    transaction_view_cancel: Gtk.Button = Gtk.Template.Child()
    transaction_view_send_receive: Gtk.Button = Gtk.Template.Child()
    transaction_view_amount = Gtk.Template.Child()
    transaction_view_input_group: Gtk.Box = Gtk.Template.Child()
    success_view_back_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.create_action("check_balance", self.handle_home_check_balance)


        # Append main view to main gui
        main_view_builder = Gtk.Builder.new_from_file("ui/ui/main_view.ui")
        main_view_box = main_view_builder.get_object("main_view_box")
        self.main_view_home_send: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_send")
        self.main_view_home_receive: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_receive")
        self.main_view_home_balance_row: Adw.ActionRow = main_view_builder.get_object("main_view_home_balance_row")
        self.main_view_home_options_list: Gtk.ListBox = main_view_builder.get_object("main_view_home_options_list")
        self.main_view_home_option_id = main_view_builder.get_object("main_view_home_option_id")
        self.main_view_home_options_list.select_row(self.main_view_home_option_id)

        self.main_view_home_send.connect('clicked', self.handle_home_send_receive)
        self.main_view_home_receive.connect('clicked', self.handle_home_send_receive)

        # Because you can't make an collect request from bank account and ifsc
        self.main_view_home_options_list.connect('row-selected', lambda *args: self.main_view_home_receive.set_visible(False) if (args[1].get_name()=='bank') else self.main_view_home_receive.set_visible(True))

        # self.main_view is a Gtk.StackPage returned by add_named method
        self.main_view = self.root_stack.add_named(main_view_box, 'main')
        self.root_stack.set_visible_child_name('pinentry')

        # Go back to main view from back_button(s) in headerbars of respective views
        self.transaction_view_cancel.connect('clicked', self.go_back_to_main_view)
        self.transaction_view_back_button.connect('clicked', self.go_back_to_main_view)
        self.success_view_back_button.connect('clicked', self.go_back_to_main_view)


    def handle_home_send_receive(self, button: Gtk.Button):
        self.root_stack.set_visible_child_name('transaction')
        
        # Pick some properties depending on send or receive action ------------------
        self.transaction_view_send_receive.set_name(button.get_name())

        # Send and receive buttons have Adw.ButtonContent as child
        self.transaction_view_send_receive.set_label(button.get_child().get_label())
        #----------------------------------------------------------------------------

        option_selected = self.main_view_home_options_list.get_selected_row().get_name()
        if option_selected == 'id':
            address_row = Adw.EntryRow(input_purpose=Gtk.InputPurpose.EMAIL)
            address_row.set_name("address")
            address_row.set_title("UPI ID")
            self.transaction_view_input_group.add(address_row)
        if option_selected == 'number':
            address_row = Adw.EntryRow(input_purpose=Gtk.InputPurpose.DIGITS)
            address_row.set_name("address")
            address_row.set_title("Phone Number")
            self.transaction_view_input_group.add(address_row)
    
    def handle_home_check_balance(self, *args):
        spinner = Gtk.Spinner()

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

        #pinentry_dialog = PinEntry(self)
        #pinentry_dialog.connect('response', when_response_given_wrapper_thread)
        #pinentry_dialog.present()

    
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
        about_window = Gtk.Builder().new_from_resource('/io/github/imhemish/pe/ui/about.ui').get_object("about_window")
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


def main(version):
    app = Application()
    return app.run(sys.argv)