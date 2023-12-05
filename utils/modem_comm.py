import serial
import logging

# open serial port
def open_modem_connection(port, baud_rate=9600, timeout=1):
    try:
        ser = serial.Serial(port, baud_rate, timeout=timeout)
        return ser
    except serial.SerialException as e:
        logging.error("Could not open serial port: %s", e)
        return None

# send AT for signal strength
def send_at(ser):
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

def get_signal_quality(port, rssi, rsrq):
    ser = open_modem_connection(port)
    if ser is not None:
        send_at(ser)
        # parse response to get rssi and rsrq values
        signal_quality = signal_quality_indicator(rssi, rsrq)
        print("Signal Quality: " + str(signal_quality))
        return signal_quality
