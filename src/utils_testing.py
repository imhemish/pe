from time import sleep
from xml.etree import ElementTree
import sys

def list_modems(bus):
    return [1]

def create_ussd_iface(modem):
    return None

class Service:
    def __init__(self, ussd_iface, log=False):
        self.ussd = ussd_iface
        self.log = log

    def log_if_needs(self, message):
        if self.log:
            sys.stderr.write("UPI USSD log: "+message+"\n")
    
    def clear_requests(self):
    # Cancel any previously running USSD request
        pass

    def send_money_to_number(self, number, amount, pin, remark='1'):
        self.clear_requests()

        sleep(6)
        
        return {"name": "name", "refid": "refid"}
        
    def send_money_to_upi_id(self, id, amount, pin, remark='1'):
        self.clear_requests()
        print('send request received')

        sleep(6)

        
        return {"name": "name", "refid": "refid"}

    def receive_from_upi_id(self, id, amount, remark='1'):
        self.clear_requests()

        sleep(6)

        
        return {"name": "name"}

    def receive_from_phone_number(self, number, amount, remark='1'):
        self.clear_requests()

        sleep(6)

        return {"name": "name"}

    def check_balance(self, pin):
        self.clear_requests()
        sleep(2)
        
        return "100"

    def determine_digits_in_pin(self):
        self.clear_requests()
        return '4'
        

        
    def last_pending_request(self):
        # If there are multiple requests, it returns the recent one only
        # Also, it does not return any 'note' or remark
        self.clear_requests()
        {"receiver": "receiver", "amount": '100'}


    def reject_last_pending_request(self):
        self.clear_requests()

        return {"refid": "refid"}

    def profile_information(self):
        self.clear_requests()

        return {"name": 'name', "id": 'upi_id', "account": 'bank_account', "pin_set": 'pin_set'}
    