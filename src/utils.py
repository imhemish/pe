from time import sleep
from xml.etree import ElementTree
import sys
import dbus
import threading

def list_modems(bus):
    modems = []
    obj = bus.get_object("org.freedesktop.ModemManager1", "/org/freedesktop/ModemManager1/Modem")

    # Introspect Dbus to find all modems under /org/freedestop/ModemManager1/Modem/
    # Modified from an answer from https://unix.stackexchange.com/questions/203410/how-to-list-all-object-paths-under-a-dbus-service
    iface = dbus.Interface(obj, dbus_interface='org.freedesktop.DBus.Introspectable')
    xml_string = iface.Introspect()
    for child in ElementTree.fromstring(xml_string):
        modems.append(child.attrib['name'])
    return modems

def create_ussd_iface(modem):
    modem_obj = dbus.SystemBus().get_object("org.freedesktop.ModemManager1", f"/org/freedesktop/ModemManager1/Modem/{modem}")
    return dbus.Interface(modem_obj, dbus_interface='org.freedesktop.ModemManager1.Modem.Modem3gpp.Ussd')
    
class Service:
    def __init__(self, ussd_iface, log=False):
        self.ussd = ussd_iface
        self.log = log

    def log_if_needs(self, message):
        if self.log:
            sys.stderr.write("UPI USSD log: "+message+"\n")
    
    def clear_requests(self):
    # Cancel any previously running USSD request
        try:
            self.ussd.Cancel()
        except:
            pass

    def send_money_to_number(self, number, amount, pin, remark='1'):
        self.clear_requests()
        # If request is not failed, enter pin
        req = str(self.ussd.Initiate(f"*99*1*1*{number}*{amount}*{remark}#"))
        self.log_if_needs(req)

        if "You are paying to" in req:
            sleep(0.01)
            output: str = self.ussd.Respond(pin)
            self.log_if_needs(output)

        # Invalid number
        elif "is not a valid" in req:
            raise Exception("unvalid number")
        else:
            raise Exception("Some error occured")
        

        if "is successful" in output:

            # Values obtained by experimenting with actual output

            reduced_output = output[(output.find("(RefId: ")+8):]
            refid = reduced_output[0:reduced_output.find(")")]

            # Just reusing the variable name, doesnt have anything to do with previous refid
            reduced_output = output[(output.find("Your payment to ")+16):]
            name = reduced_output[0:reduced_output.find(",")]

            return {"name": name, "refid": refid}

        else:
            # By experimenting, it has been found that the service does not tell why it failed, like was the reason the wrong upi pin, or insufficient funds

            raise Exception("Some error occured")
        
    def send_money_to_upi_id(self, id, amount, pin, remark='1'):
        self.clear_requests()

        # the upi id can not be sent in combined code
        req = str(self.ussd.Initiate("*99*1*3#"))
        self.log_if_needs(req)

        if "Enter UPI" in req:
            sleep(0.01)
            req = str(self.ussd.Respond(id))
            self.log_if_needs(req)

            # Found experimentally
            if "TRANSACTION DECLINED" in req:
                raise Exception("Invalid UPI id or UPI id does not exist")
            elif "Paying" in req:
                # Just after "Paying " is the name of receiver, before a comma
                name = req[7: req.find(",")]
                sleep(0.01)
                req = str(self.ussd.Respond(amount))
                self.log_if_needs(req)

                if "Enter a remark" in req:
                    sleep(0.01)
                    req = self.ussd.Respond(remark)
                    self.log_if_needs(req)
                    if "You are paying to" in req:
                        sleep(0.01)
                        output = self.ussd.Respond(pin)
                        self.log_if_needs(output)
                    else:
                        raise Exception("Some error occured")
                # Invalid amount
                elif "not a valid" in req:
                        raise Exception("")
                    
                else:
                    raise Exception("Some error occured")
                
            else:
                raise Exception("Some error occured")
        
        else:
            raise Exception("Some error occured")
            

        if "is successful" in output:

            # Values obtained by experimenting with actual output

            reduced_output = output[(output.find("(RefId: ")+8):]
            refid = reduced_output[0:reduced_output.find(")")]

            # Just reusing the variable name, doesnt have anything to do with previous refid
            reduced_output = output[(output.find("Your payment to ")+16):]
            name = reduced_output[0:reduced_output.find(",")]

            return {"name": name, "refid": refid}

        else:
            # By experimenting, it has been found that the service does not tell why it failed, like was the reason the wrong upi pin, or insufficient funds

            raise Exception("Some error occured")

    def receive_from_upi_id(self, id, amount, remark='1'):
        self.clear_requests()

        # the upi id can not be sent in combined code
        req = str(self.ussd.Initiate("*99*2#"))
        if "UPI ID" in req:
            sleep(0.01)
            req = str(self.ussd.Respond(id))
            self.log_if_needs(req)

            # Found experimentally
            if "TRANSACTION DECLINED" in req:
                raise Exception("Invalid UPI id or UPI id does not exist")
            elif "Collecting from " in req:
                # Just after "Collecting from " is the name of receiver, before a newline
                name = req[16: req.find("\n")]
                sleep(0.01)
                req = str(self.ussd.Respond(amount))
                self.log_if_needs(req)

                if "Enter a remark" in req:
                    sleep(0.01)
                    req = self.ussd.Respond(remark)
                    self.log_if_needs(req)
                    if "You are requesting" in req:
                        sleep(0.01)
                        # Enter 1 to confirm
                        output = self.ussd.Respond("1")
                        self.log_if_needs(output)
                    else:
                        raise Exception("Some error occured")
                # Invalid amount
                elif "not a valid" in req:
                    raise Exception("invalid amount")
                
                else:
                    raise Exception("Some error occured")
                
            else:
                raise Exception("Some error occured")
        
        else:
            raise Exception("Some error occured")
        
        if "is successful" in output:
            return {"name": name}
        else:
            raise Exception("Some error occured")

    def receive_from_phone_number(self, number, amount, remark='1'):
        self.clear_requests()

        # the upi id can not be sent in combined code
        req = str(self.ussd.Initiate(f"*99*2*{number}*{amount}*{remark}*1#"))
        self.log_if_needs(req)
        if "Beneficiary payment address incorrect" in req:
            raise Exception("Invalid phone number or is not on UPI")
        elif "is successful" in req:
            reduced_output = req[(req.find(" from ")+6):]
            name = reduced_output[:reduced_output.find(" is successful")]
            return {"name": name}
        else:
            raise Exception("Some error occured")

    def check_balance(self, pin):
        self.clear_requests()

        req = str(self.ussd.Initiate("*99*3#"))
        self.log_if_needs(req)
        
        if "Enter" in req:
            sleep(0.01)
            output: str = self.ussd.Respond(pin)
            self.log_if_needs(output)
            if "Incorrect UPI" in output:
                raise Exception("Incorrect UPI PIN")
            elif "Your account balance is":
                pass

            # Happens in my account at night (my internet upi apps also fail to check balance)
            elif "Error fetching balance":
                raise Exception("error fetching balance")
            
            else:
                raise Exception("Some error occured")

        else:
            raise Exception("Some error occured")
        
        balance = output[(output.find("Your account balance is Rs. ")+28):]
        return balance

    def determine_digits_in_pin(self):
        self.clear_requests()

        # The service tells the digits in check balance function in form "Enter * digit..."
        req = str(self.ussd.Initiate("*99*3#"))
        self.log_if_needs(req)
        
        if "Enter" in req:
            shortened_req = req[(req.find("Enter ")+6):]
            return shortened_req[:shortened_req.find(" digit")]

        else:
            raise Exception("Some error occured")
        
        balance = output[(output.find("Your account balance is Rs. ")+28):]
        return balance
        
    def last_pending_request(self):
        # If there are multiple requests, it returns the recent one only
        # Also, it does not return any 'note' or remark
        self.clear_requests()

        req = str(self.ussd.Initiate("*99*5#"))
        self.log_if_needs(req)
        
        if "You do not have any requests pending" in req:
            return None
        elif ("Enter your" in req) and ("to pay" in req):
            reduced_req = req[(req.find("to pay ")+7):]
            receiver = reduced_req[:reduced_req.find(" Rs.")]
            red_red_req = reduced_req[(reduced_req.find(" Rs.")+4):]
            amount = red_red_req[:red_red_req.find("\n")]
            return {"receiver": receiver, "amount": amount}
        else:
            raise Exception("Some error occured")

    def reject_last_pending_request(self):
        self.clear_requests()

        req = str(self.ussd.Initiate("*99*5#"))
        self.log_if_needs(req)

        if "You do not have any requests pending" in req:
            raise Exception("no pending request")
        
        elif ("Enter your" in req) and ("to pay" in req):

            # Respond 2 to reject
            output = self.ussd.Respond("2")
            self.log_if_needs(output)
            if "Reject this txn" in output:
                output2 = self.ussd.Respond("1")
                self.log_if_needs(output2)
            else:
                raise Exception("Some error occured")
        
        else:
            raise Exception("Some error occured")
        
        
        if "You have declined" in output2:
            reduced_output = output2[(output2.find("(RefId: ")+8):]
            refid = reduced_output[:reduced_output.find(")")]
            return {"refid": refid}
        else:
            raise Exception("Some error occured")

    def profile_information(self):
        self.clear_requests()

        req = self.ussd.Initiate("*99*4*3#")
        self.log_if_needs(req)

        if "Name:" in req:
            output_list = str(req).split("\n")
            name = output_list[0][(output_list[0].find("Name: ")+6):]
            upi_id = output_list[1][(output_list[1].find("UPI ID: ")+8):]
            bank_account = output_list[3]
            if "UPI PIN Set" in output_list[4]:
                pin_set = True
            else:
                pin_set = False
            return {"name": name, "id": upi_id, "account": bank_account, "pin_set": pin_set}
        else:
            raise Exception("Some error occured")
    