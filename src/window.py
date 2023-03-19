from gi.repository import Gtk, Gio, Adw
from dbus.exceptions import DBusException
import threading

from .pin_entry import PinEntry
from .menu_button import MenuButton
from .success_view import SuccessView
from .transaction_view import TransactionView
from .address_widgets import NormalWidget

@Gtk.Template(resource_path='/net/hemish/pe/ui/gui.ui')
class ApplicationWindow(Adw.ApplicationWindow):
    __gtype_name__ = "ApplicationWindow"
    root_stack: Gtk.Stack = Gtk.Template.Child()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Append main view to main gui ---------------------------------
        main_view_builder = Gtk.Builder.new_from_resource("/net/hemish/pe/ui/main_view.ui")
        main_view_box = main_view_builder.get_object("main_view_box")
        self.main_view_home_send: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_send")
        self.main_view_home_receive: Gtk.ToggleButton = main_view_builder.get_object("main_view_home_receive")
        self.main_view_home_balance_row: Adw.ActionRow = main_view_builder.get_object("main_view_home_balance_row")
        self.main_view_home_options_list: Gtk.ListBox = main_view_builder.get_object("main_view_home_options_list")
        self.main_view_home_option_id = main_view_builder.get_object("main_view_home_option_id")
        self.main_view_home_options_list.select_row(self.main_view_home_option_id)

        # self.main_view is a Gtk.StackPage returned by add_named method
        self.main_view = self.root_stack.add_named(main_view_box, 'main')
        # ---------------------------------------------------------------

        self.main_view_home_send.connect('clicked', self.handle_home_send_receive)
        self.main_view_home_receive.connect('clicked', self.handle_home_send_receive)

        self.main_view_home_balance_row.connect('activated', self.handle_home_check_balance)

        # Because you can't make a collect request from bank account and ifsc
        self.main_view_home_options_list.connect('row-selected', lambda *args: self.main_view_home_receive.set_visible(False) if (args[1].get_name()=='bank') else self.main_view_home_receive.set_visible(True))


        self.root_stack.set_visible_child_name('main')

        self.create_action('go_back_to_main_view', self.go_back_to_main_view)


    def handle_home_send_receive(self, button: Gtk.Button):

        # Remove any existing transaction_view
        try:
            self.root_stack.remove(self.root_stack.get_child_by_name('transaction'))
        except:
            pass

        def cancel_and_back_callback(*args):

            # Order of this is important, first change view, then remove
            self.go_back_to_main_view()
            self.root_stack.remove(self.root_stack.get_child_by_name('transaction'))
        
        def submit_callback(button, *args):
            def pin_entry_back(*args):
                self.root_stack.set_visible_child_name('transaction')
                self.root_stack.remove(self.root_stack.get_child_by_name('pin_entry'))
            
            def pin_entry_submit(*args):
                pin = self.root_stack.get_child_by_name('pin_entry').pinentry_view_entry_row.get_text()
                address_type = self.root_stack.get_child_by_name('transaction').address_widget.get_name()
                address = self.root_stack.get_child_by_name('transaction').address_widget.get_text()
                amount = self.root_stack.get_child_by_name('transaction').transaction_view_amount.get_text()
                remark = self.root_stack.get_child_by_name('transaction').transaction_view_remark.get_text()
                type = button.get_name()

                if (remark == None) or (remark == ''):
                    remark = '1'
                self.root_stack.set_visible_child_name('processing')

                def wrapped_in_a_thread(type, address, address_type, pin, amount, remark):
                    service = self.get_application().upi_service
                    print(type)
                    if type == 'send':
                        print(address_type)
                        if address_type == 'number':
                            result = service.send_money_to_number(address, amount, pin, remark)
                        elif address_type == 'id':
                            result = service.send_money_to_upi_id(address, amount, pin, remark)
                    self.root_stack.add_named(SuccessView("Name: {}, RefId: {}".format(result['name'], result['refid']),  lambda x: self.root_stack.remove(self.root_stack.get_child_by_name('success'))), 'success')
                    self.root_stack.set_visible_child_name('success')

                    # Cleanup
                    self.root_stack.remove(self.root_stack.get_child_by_name('pin_entry'))
                    self.root_stack.remove(self.root_stack.get_child_by_name('transaction'))
                
                threading.Thread(target=wrapped_in_a_thread, args=(type, address, address_type, pin, amount, remark)).start()

            action = button.get_name()
            self.root_stack.add_named(PinEntry(pin_entry_back, pin_entry_submit), 'pin_entry')
            self.root_stack.set_visible_child_name('pin_entry')


        
        selected_row =  self.main_view_home_options_list.get_selected_row()
        name = selected_row.get_name()
        title = selected_row.get_title()

        if name == 'number':
            input_purpose = Gtk.InputPurpose.DIGITS
        elif name == 'id':
            input_purpose = Gtk.InputPurpose.EMAIL

        transaction = TransactionView(button.get_child().get_label(), button.get_name(), NormalWidget(name, title, input_purpose), cancel_and_back_callback, submit_callback)
        self.root_stack.add_named(transaction, 'transaction')
        self.root_stack.set_visible_child_name('transaction')

    
    def handle_home_check_balance(self, row, *data):
        spinner = Gtk.Spinner()

        # Remove existing child widget, e.g. previous spinner or balance label
        try:
            self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
        except:
            pass

        self.main_view_home_balance_row.child_widget = spinner
        spinner.start()
        self.main_view_home_balance_row.add_suffix(self.main_view_home_balance_row.child_widget)

        # Go back
        def cancel(*args):
            self.main_view_home_balance_row.remove(self.main_view_home_balance_row.child_widget)
            
            # Order is important
            self.go_back_to_main_view(())
            self.root_stack.remove(self.root_stack.get_child_by_name('pin_entry'))
            

        def when_apply_pressed_wrapper(row: Adw.PasswordEntryRow):
            pin = str(row.get_text())
            
            # Order of these is important
            self.go_back_to_main_view(())
            self.root_stack.remove(self.root_stack.get_child_by_name('pin_entry'))

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
                    
            
            thread = threading.Thread(target=wrapped_in_thread, args=(pin,))
            thread.start()

        pin_entry = PinEntry(cancel, when_apply_pressed_wrapper)
        self.root_stack.add_named(pin_entry, "pin_entry")
        self.root_stack.set_visible_child_name('pin_entry')
        

    
    def go_back_to_main_view(self, *args):
        self.root_stack.set_visible_child_name("main")

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"win.{name}", shortcuts)