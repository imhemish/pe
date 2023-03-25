from gi.repository import Gtk, Gio, Adw
from dbus.exceptions import DBusException
import threading

from .pin_entry import PinEntry

# Is used by transaction_view, main_view, so I separated it out so
# that it can be reused by both, and I dont have to duplicate it in both
from .menu_button import MenuButton

from .address_widgets import NormalWidget

@Gtk.Template(resource_path='/net/hemish/pe/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    root_stack: Gtk.Stack = Gtk.Template.Child()
    leaflet: Adw.Leaflet = Gtk.Template.Child()
    transaction_view_send_receive: Gtk.Button = Gtk.Template.Child()
    transaction_view_amount = Gtk.Template.Child()
    transaction_view_input_group: Gtk.Box = Gtk.Template.Child()
    transaction_view_remark = Gtk.Template.Child()
    transaction_view_back_button = Gtk.Template.Child()
    success_view_status = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Append main_view to leaflet  ---------------------------------
        main_view_builder = Gtk.Builder.new_from_resource("/net/hemish/pe/ui/main_view.ui")
        main_view_box = main_view_builder.get_object("main_view_box")
        self.main_view_home_send: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_send")
        self.main_view_home_receive: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_receive")
        self.main_view_home_balance_row: Adw.ActionRow = main_view_builder.get_object("main_view_home_balance_row")
        self.main_view_home_options_list: Gtk.ListBox = main_view_builder.get_object("main_view_home_options_list")
        self.main_view_home_option_id = main_view_builder.get_object("main_view_home_option_id")
        self.main_view_home_options_list.select_row(self.main_view_home_option_id)

        # self.main_view is a Adw.LeafletPage returned by prepend method
        self.main_view: Adw.LeafletPage = self.leaflet.prepend(main_view_box)
        self.main_view.set_name('main_view')
        # ---------------------------------------------------------------

        # Connecting send and receive buttons to handler
        self.main_view_home_send.connect('clicked', self.handle_home_send_receive)
        self.main_view_home_receive.connect('clicked', self.handle_home_send_receive)

        # Connecting balance check row to balance check function
        self.main_view_home_balance_row.connect('activated', self.handle_home_check_balance)

        # Because you can't make a collect request from bank account and IFSC
        # So hiding 'receive' button when 'bank account' row is selected
        self.main_view_home_options_list.connect('row-selected', lambda *args: self.main_view_home_receive.set_visible(False) if (args[1].get_name()=='bank') else self.main_view_home_receive.set_visible(True))

        # Make sure you are intially at main view
        self.go_back_to_main_view()

        self.create_action('go_back_to_main_view', self.go_back_to_main_view)



    #----------------------------------------#
    #---------------- balance ---------------#
    def handle_home_check_balance(self, row, *data):
        spinner = Gtk.Spinner()

        # Remove existing child widget, e.g. previous spinner or balance label
        # if any exists
        try:
            self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
        except:
            pass

        # Adding and starting spinner
        self.main_view_home_balance_row.child_widget = spinner
        spinner.start()
        self.main_view_home_balance_row.add_suffix(self.main_view_home_balance_row.child_widget)

        # Function called when cancel clicked or Esc pressed
        def cancel(*args):
            # Remove the spinner
            self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
            
        # Function called when ok is clicked in pin dialog
        def submit(pin):

            # Because we dont want balance checking process to freeze the GUI mainloop;
            # the spinner would continue to spin till balance is retrieved.
            # That's why created a separate function which would be run in background

            def wrapped_in_thread(pin):
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
                except DBusException:
                    print('dbus exception happened')
                    self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
                    
            # Running in background
            thread = threading.Thread(target=wrapped_in_thread, args=(pin,))
            thread.start()

        # Pin dialog; passing it submit and cancel callbacks
        pin_entry = PinEntry(self, submit, cancel)

    #----------------------------------------#
    #----------------------------------------#


    #----------------------------------------#
    #------- send/receive handling ----------#
    def handle_home_send_receive(self, button: Gtk.Button):

        # First setting label and name of buttons of transaction view
        # according to which button of main view is pressed

        self.transaction_view_send_receive.set_name(button.get_name())

        # used button.get_child().get_label() because button has child Adw.ButtonContent 
        # which has label, and not button
        self.transaction_view_send_receive.set_label(button.get_child().get_label())

        self.leaflet.set_visible_child_name('transaction_view')
    
    #----------------------------------------#
    #----------------------------------------#

        
    
    def go_back_to_main_view(self, *args):
        self.root_stack.set_visible_child_name("leaflet")
        self.leaflet.set_visible_child_name('main_view')


    # This function is given by gnome builder in boilerplate
    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"win.{name}", shortcuts)