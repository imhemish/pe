from argparse import ArgumentParser
import dbus
from xml.etree import ElementTree
from time import sleep

# Argument parsing ----------------------
ap = ArgumentParser('upi-ussd', description="Use NPCI's USSD UPI service via Modem")
ap.add_argument("--send", '-s', action='store_true', required=False, help="Send Money")
ap.add_argument("--receive", '-r', action='store_true', required=False, help="Receive Money")
ap.add_argument("--address", '-a', metavar='upi/number', required=False, nargs=1, help="UPI ID or number to send/receive from")
ap.add_argument("--amount", '-A', metavar='100', nargs=1, required=False, help="Amount of money to send/receive")
ap.add_argument("--pin", '-p', metavar='****', nargs=1, required=False, help="UPI pin")
ap.add_argument("--remark", "-R", metavar='"babe this is for you"', nargs=1, required=False, help="Remark to add (optional)")
ap.add_argument("--balance", '-b', action='store_true', help="Print remaining balance (requires PIN)")
ap.add_argument("--pending-request", '-P', action='store_true', help="Print last pending request with receiver and amount")
ap.add_argument("--reject-request", action='store_true', help="Reject last pending request")
ap.add_argument("--list-modems", '-l', action='store_true', help="List all available modems")
ap.add_argument("--modem", '-m', metavar='1', help="Modem to use (not required if there is only 1 modem)", nargs=1)
ap.add_argument("--determine-digits", '-d', action='store_true', help="Determine number of digits in PIN")
# ---------------------------------


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

def clear_requests(ussd_iface):
    # Cancel any previously running USSD request
    try:
        ussd_iface.Cancel()
    except:
        pass

def send_money_to_number(number, amount, pin, ussd_iface, remark='1'):
    clear_requests(ussd_iface)
    # If request is not failed, enter pin
    req = str(ussd_iface.Initiate(f"*99*1*1*{number}*{amount}*{remark}#"))
    
    if "You are paying to" in req:
        sleep(0.01)
        output: str = ussd_iface.Respond(pin)

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
    
def send_money_to_upi_id(id, amount, pin, ussd_iface, remark='1'):
    clear_requests(ussd_iface)

    # the upi id can not be sent in combined code
    req = str(ussd_iface.Initiate("*99*1*3#"))

    if "Enter UPI" in req:
        sleep(0.01)
        req = str(ussd_iface.Respond(id))

        # Found experimentally
        if "TRANSACTION DECLINED" in req:
            raise Exception("Invalid UPI id or UPI id does not exist")
        elif "Paying" in req:
            # Just after "Paying " is the name of receiver, before a comma
            name = req[7: req.find(",")]
            sleep(0.01)
            req = str(ussd_iface.Respond(amount))

            if "Enter a remark" in req:
                sleep(0.01)
                req = ussd_iface.Respond(remark)
                if "You are paying to" in req:
                    sleep(0.01)
                    output = ussd_iface.Respond(pin)
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

def receive_from_upi_id(id, amount, ussd_iface, remark='1'):
    clear_requests(ussd_iface)

    # the upi id can not be sent in combined code
    req = str(ussd_iface.Initiate("*99*2#"))
    if "UPI ID" in req:
        sleep(0.01)
        req = str(ussd_iface.Respond(id))

        # Found experimentally
        if "TRANSACTION DECLINED" in req:
            raise Exception("Invalid UPI id or UPI id does not exist")
        elif "Collecting from " in req:
            # Just after "Collecting from " is the name of receiver, before a newline
            name = req[16: req.find("\n")]
            sleep(0.01)
            req = str(ussd_iface.Respond(amount))

            if "Enter a remark" in req:
                sleep(0.01)
                req = ussd_iface.Respond(remark)
                if "You are requesting" in req:
                    sleep(0.01)
                    # Enter 1 to confirm
                    output = ussd_iface.Respond("1")
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

def receive_from_phone_number(number, amount, ussd_iface, remark='1'):
    clear_requests(ussd_iface)

    # the upi id can not be sent in combined code
    req = str(ussd_iface.Initiate(f"*99*2*{number}*{amount}*{remark}*1#"))
    if "Beneficiary payment address incorrect" in req:
        raise Exception("Invalid phone number or is not on UPI")
    elif "is successful" in req:
        reduced_output = req[(req.find(" from ")+6):]
        name = reduced_output[:reduced_output.find(" is successful")]
        return {"name": name}
    else:
        raise Exception("Some error occured")

def check_balance(pin, ussd_iface):
    clear_requests(ussd_iface)

    req = str(ussd_iface.Initiate("*99*3#"))
    
    if "Enter" in req:
        sleep(0.01)
        output: str = ussd_iface.Respond(pin)
        if "Incorrect UPI" in output:
            raise Exception("Incorrect UPI PIN")
        elif "Your account balance is":
            pass
        else:
            raise Exception("Some error occured")

    else:
        raise Exception("Some error occured")
    
    balance = output[(output.find("Your account balance is Rs. ")+28):]
    return balance

def determine_digits_in_pin(ussd_iface):
    clear_requests(ussd_iface)

    # The service tells the digits in check balance function in form "Enter * digit..."
    req = str(ussd_iface.Initiate("*99*3#"))
    
    if "Enter" in req:
        shortened_req = req[(req.find("Enter ")+6):]
        return shortened_req[:shortened_req.find(" digit")]

    else:
        raise Exception("Some error occured")
    
    balance = output[(output.find("Your account balance is Rs. ")+28):]
    return balance
    
def last_pending_request(ussd_iface):
    # If there are multiple requests, it returns the recent one only
    # Also, it does not return any 'note' or remark
    clear_requests(ussd_iface)

    req = str(ussd_iface.Initiate("*99*5#"))
    
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

def reject_last_pending_request(ussd_iface):
    clear_requests(ussd_iface)

    req = str(ussd_iface.Initiate("*99*5#"))

    if "You do not have any requests pending" in req:
        raise Exception("no pending request")
    
    elif ("Enter your" in req) and ("to pay" in req):

        # Respond 2 to reject
        output = ussd_iface.Respond("2")
        if "Reject this txn" in output:
            output2 = ussd_iface.Respond("1")
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


def main():
    bus = dbus.SystemBus()
    args = ap.parse_args()

    modems = list_modems(bus)

    # List modems if asked
    if args.list_modems:
        for item in modems:
            print(item)
        exit() # Because if there is no modem, and user just wants to see if there is a modem or not, next block of code which chooses modem, fails raising an exception

    # If there is only 1 modem, then use it, else use the one specified by --modem flag
    if len(modems) == 1:
        modem = modems[0]
    else:
        if args.modem == None:
            raise Exception("no modem specified")
        else:
            modem = args.modem[0]

    modem_obj = bus.get_object("org.freedesktop.ModemManager1", f"/org/freedesktop/ModemManager1/Modem/{modem}")
    ussd = dbus.Interface(modem_obj, dbus_interface='org.freedesktop.ModemManager1.Modem.Modem3gpp.Ussd')

    if args.send:
        # Send money

        if args.remark == None:
            remark = '1'
        else:
            remark = args.remark[0]

        if args.address != None:
            # Is a 10 digit mobile number
            if str(args.address[0]).isdigit():
                if len(args.address[0]) == 10:
                    print(send_money_to_number(args.address[0], args.amount[0], args.pin[0], ussd, remark))
                else:
                    raise Exception("not 10 digits")
            if "@" in str(args.address[0]):
                print(send_money_to_upi_id(args.address[0], args.amount[0], args.pin[0], ussd, remark ))
                
        else:
            raise Exception("Address not provided")
    
    elif args.receive:
        # Make a receive request
        if args.remark == None:
            remark = '1'
        else:
            remark = args.remark[0]

        if args.address != None:
            # Is a 10 digit mobile number
            if str(args.address[0]).isdigit():
                if len(args.address[0]) == 10:
                    print(receive_from_phone_number(args.address[0], args.amount[0], ussd, remark))
                else:
                    raise Exception("not 10 digits")
            if "@" in str(args.address[0]):
                print(receive_from_upi_id(args.address[0], args.amount[0], ussd, remark ))
                
        else:
            raise Exception("Address not provided")
    elif args.balance:
        if args.pin == None:
            raise Exception("pin not provided")
        else:
            print(check_balance(args.pin[0], ussd))
    
    elif args.determine_digits:
        print(determine_digits_in_pin(ussd))
    
    if args.pending_request:
        print(last_pending_request(ussd))
    if args.reject_request:
        print(reject_last_pending_request(ussd))
    

if __name__ == "__main__":
    main()