from gi.repository import Gtk, Adw
from .menu_button import MenuButton

@Gtk.Template(resource_path="/net/hemish/pe/ui/transaction_view.ui")
class TransactionView(Gtk.Box):
    __gtype_name__ = "TransactionView"
    transaction_view_back_button = Gtk.Template.Child()
    transaction_view_send_receive: Gtk.Button = Gtk.Template.Child()
    transaction_view_amount = Gtk.Template.Child()
    transaction_view_input_group: Gtk.Box = Gtk.Template.Child()
    transaction_view_cancel = Gtk.Template.Child()
    transaction_view_remark = Gtk.Template.Child()
    
    def __init__(self, send_receive_label, send_receive_name, address_widget, cancel_and_back_callback, submit_callback):
        super().__init__()
        self.transaction_view_send_receive.set_label(send_receive_label)
        self.transaction_view_send_receive.set_name(send_receive_name)
        self.address_widget = address_widget
        self.transaction_view_input_group.add(self.address_widget)
        self.transaction_view_back_button.connect('clicked', cancel_and_back_callback)
        self.transaction_view_cancel.connect('clicked', cancel_and_back_callback)
        self.transaction_view_send_receive.connect('clicked', submit_callback)