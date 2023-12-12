import serial
import logging

# open serial port
def open_modem_connection(port, baud_rate=9600, timeout=1):
    """method to open a serial connection to the modem"""
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        return ser
    except serial.SerialException as e:
        logging.error("Could not open serial port: %s", e)
        return None

# send AT+CSQ for signal quality
def at_csq(ser):
    """method to send AT+CSQ command to modem and return response"""
    ser.write(b'AT+CSQ\r\n')
    response_lines = []
    while True:
        line = ser.readline()
        response_lines.append(line)
        if b'OK' in line or b'ERROR' in line:
            break
    return response_lines

# interpret csq value
def signal_quality_indicator(rssi, rsrq):
    """method to interpret rssi and rsrq values and return signal quality"""
    if rssi is None or rsrq is None or not isinstance(rssi, int) or not isinstance(rsrq, int):
        return -1  # "Error: No CSQ"
    elif rssi >= 31 and rsrq <= 3:
        return 1  # "Excellent Signal"
    elif rssi >= 22 and rsrq <= 3:
        return 2  # "Very Good Signal"
    elif rssi >= 12 and rsrq <= 6:
        return 3  # "Good Signal"
    elif rssi >= 2 and rsrq <= 7:
        return 4  # "Signal may degrade"
    else:
        return 5  # "Signal quality not defined"


##############################################################################
# network commands

# # send AT command to modem
# def send_at(ser, command):
#     ser.write(command + '\r\n')
#     response_lines = []
#     while True:
#         line = ser.readline()
#         response_lines.append(line)
#         if b'OK' in line or b'ERROR' in line:
#             break
#     return response_lines

# # scan for available networks
# def scan_networks(ser):
#     response_lines = send_at(ser, 'AT+COPS=?')
#     # parse response to get list of networks
#     return response_lines

# # register on a network
# def register_network(ser, network_code):
#     response_lines = send_at(ser, 'AT+COPS=1,2,"' + network_code + '"')
#     return response_lines

# # automatically register on a network
# def auto_register_network(ser):
#     response_lines = send_at(ser, 'AT+COPS=0')
#     return response_lines