from gi.repository import Gtk, Gio, Adw
from dbus.exceptions import DBusException
import threading


# Used as a decorator to run things in the background
# Picked up from Linux Mint's webapp-manager
def _async(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

from .pin_entry import PinEntry

# Is used by transaction_view, main_view, so I separated it out so
# that it can be reused by both, and I dont have to duplicate it in both
from .menu_button import MenuButton

@Gtk.Template(resource_path='/net/hemish/pe/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):

    # For beginners, __gtype_name__ is used to identify an object template you declared in
    # UI/BLP files.
    __gtype_name__ = "ApplicationWindow"

    root_stack: Gtk.Stack = Gtk.Template.Child()
    leaflet: Adw.Leaflet = Gtk.Template.Child()
    transaction_view_send_receive: Gtk.Button = Gtk.Template.Child()
    transaction_view_amount = Gtk.Template.Child()
    transaction_view_input_group: Adw.PreferencesGroup = Gtk.Template.Child()
    transaction_view_id: Adw.EntryRow = Gtk.Template.Child()
    transaction_view_number: Adw.EntryRow = Gtk.Template.Child()
    transaction_view_remark = Gtk.Template.Child()
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

        self.transaction_view_send_receive.connect('clicked', self.submit_send_receive)


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

    # Called when either send or receive button is pressed in main view
    def handle_home_send_receive(self, button: Gtk.Button):

        action = button.get_name()
        identifier_type = self.main_view_home_options_list.get_selected_row().get_name()
        print(identifier_type)
        self._handle_send_receive(action, identifier_type)


    # Meta send/receive function which can be used by gui, or cli upi:// link passing
    def _handle_send_receive(self, action, identifier_type, identifier_raw = None):
        # identifier_raw is optional, it may be provided or not
        # identifier_type can be one of 'number', 'id', etc.
        # while identifer_raw is the actua id or number like 94XXXXXXXX
        
        # First setting label and name of buttons of transaction view
        # according to which button of main view is pressed

        self.transaction_view_send_receive.set_name(action)

        # used button.get_child().get_label() because button has child Adw.ButtonContent 
        # which has label, and not button
        if action == 'send':
            self.transaction_view_send_receive.get_child().set_label("Send")
        else: 
            self.transaction_view_send_receive.get_child().set_label("Receive")
        
        if identifier_type == 'id':
            self.transaction_view_input_group.active_identifier = self.transaction_view_id
            self.transaction_view_id.show()
            self.transaction_view_number.hide()
            if identifier_raw != None:
                self.transaction_view_id.set_text(identifier_raw)
        elif identifier_type == 'number':
            self.transaction_view_input_group.active_identifier = self.transaction_view_number
            self.transaction_view_id.hide()
            self.transaction_view_number.show()
            if identifier_raw != None:
                self.transaction_view_number.set_text(identifier_raw)

        self.leaflet.set_visible_child_name('transaction_view')

    # The callback which handles the 'actual' send/receive when either 
    # of the button is clicked

    def submit_send_receive(self, button):
        service = self.get_application().upi_service

        amount = self.transaction_view_amount.get_text()
        remark = self.transaction_view_remark.get_text()
        if remark == '' or remark == None:
            remark = 1

        identifier_raw = self.transaction_view_input_group.active_identifier.get_text()

        @_async
        def submit(pin):
            # Pin is only required for sending, but I am adding receive handlers also here
            # though this function would not be called by pin entry in receive scenarious,
            # i would be calling it manually

            print("button name is ", button.get_name())

            if button.get_name() == 'send':
                print(self.transaction_view_input_group.active_identifier.get_name())
                if self.transaction_view_input_group.active_identifier.get_name() == 'id':
                    print('active identifier is id')
                    output = service.send_money_to_upi_id(identifier_raw, amount, pin, remark)

                elif self.transaction_view_input_group.active_identifier.get_name() == 'number':
                    output = service.send_money_to_number(identifier_raw, amount, pin, remark)
            
            elif button.get_name() == 'receive':
                if self.transaction_view_input_group.active_identifier.get_name() == 'id':
                    print(service.receive_from_upi_id(identifier_raw, amount, remark))

                elif self.transaction_view_input_group.active_identifier.get_name() == 'number':
                    print(service.receive_from_phone_number(identifier_raw, amount, remark))
            self.root_stack.set_visible_child_name('success_view')
            print(output)

        self.root_stack.set_visible_child_name('processing_view')

        if self.transaction_view_send_receive.get_name() == 'send':
            PinEntry(self, ok_callback=submit)

        elif self.transaction_view_send_receive.get_name() == 'receive':
            # Pin is not required for receiving
            submit(None)




        
        
        
        

    
    #----------------------------------------#
    #----------------------------------------#

        
    # Is used to make an action, which is then resued in .blp 
    # files for navigation via back button in headerbar
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
