from gi.repository import Gtk, Adw

class PinEntry(Adw.MessageDialog):
    def __init__(self, parent, ok_callback, cancel_callback = None, digits = None):
        super().__init__()

        self.set_heading("Enter PIN")

        self.cancel_callback = cancel_callback
        self.ok_callback = ok_callback

        self.pin_entry: Gtk.PasswordEntry = Gtk.PasswordEntry()

        if digits != None:
            self.pin_entry.set_placeholder_text("*"*digits)

        self.set_extra_child(self.pin_entry)

        self.add_response("ok", "OK")
        self.add_response("cancel", "Cancel")

        self.set_default_response("ok")
        self.set_close_response("cancel")

        self.connect("response", self.handle_reponses)

        self.set_transient_for(parent)
        self.present()
    
    def handle_reponses(self, dialog, response):
        print(response)
        if response == 'ok':
            print("calling ok callback")
            self.ok_callback(self.pin_entry.get_text())
        if response == 'cancel':
            if self.cancel_callback:
                self.cancel_callback()
