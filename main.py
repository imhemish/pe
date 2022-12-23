from argparse import ArgumentParser
import dbus
from xml.etree import ElementTree
from time import sleep

# Argument parsing ----------------------
ap = ArgumentParser('upi-ussd', description="Use NPCI's USSD UPI service via Modem")
ap.add_argument("--send", '-s', action='store_true', required=False, help="Send Money")
ap.add_argument("--receive", '-r', action='store_true', required=False, help="Receive Money")
ap.add_argument("--address", '-a', metavar='upi/number', nargs=1, required=False, help="UPI ID or number to send/receive from")
ap.add_argument("--amount", '-A', metavar='100', nargs=1, required=False, help="Amount of money to send/receive")
ap.add_argument("--pin", '-p', metavar='****', nargs=1, required=False, help="UPI pin")
ap.add_argument("--remark", "-R", metavar='"babe this is for you"', nargs=1, required=False, help="Remark to add (optional)")
ap.add_argument("--balance", '-b', action='store_true', help="Print remaining balance (requires PIN)")
ap.add_argument("--list-modems", '-l', action='store_true', help="List all available modems")
ap.add_argument("--modem", '-m', metavar='1', help="Modem to use (not required if there is only 1 modem)", nargs=1)
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

def send_money_to_number(number, amount, pin, ussd_iface, remark='1'):
    
    # Cancel any previously running USSD request
    try:
        ussd_iface.Cancel()
    except:
        pass

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
    
    # Cancel any previously running USSD request
    try:
        ussd_iface.Cancel()
    except:
        pass

    # the upi id can not be sent in combined code
    req = str(ussd_iface.Initiate(f"*99*1*3#"))

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

                # Invalid amount
                if "not a valid" in req:
                    raise Exception("")
                elif "You are paying to" in req:
                    sleep(0.01)
                    output = ussd_iface.Respond(pin)
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

def check_balance(pin, ussd_iface):
    
    # Cancel any previously running USSD request
    try:
        ussd_iface.Cancel()
    except:
        pass

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
    
def main():
    bus = dbus.SystemBus()
    args = ap.parse_args()

    modems = list_modems(bus)

    # List modems if asked
    if args.list_modems:
        for item in modems:
            print(item)
    
    modems = list_modems(bus)

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
    
    elif args.balance:
        if args.pin == None:
            raise Exception("pin not provided")
        else:
            print(check_balance(args.pin[0], ussd))
if __name__ == "__main__":
    main()