import sys
import os
import subprocess
import time
from utils.modem_comm import open_modem_connection, send_at, signal_quality_indicator
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGridLayout, QSpacerItem, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
from pytryfi import PyTryFi
import requests
import gpsd


class SignalQualityThread(QThread):
    signal_quality_updated = pyqtSignal(int)

    def run(self):
        port = "/dev/ttyUSB2"
        ser = open_modem_connection(port)
        if ser is not None:
            while True:
                self.update_signal_quality(ser)
                time.sleep(5)  # Delay for 5 seconds

    def update_signal_quality(self, ser):
        response = send_at(ser)
        print(response) # delete this line later, for dev purposes only
        # parse response to get rssi and rsrq values
        for line in response:
            signal_info = line.decode('utf-8').strip()  # Remove newline characters
            if signal_info.startswith('+CSQ:'):
                rssi, rsrq = [int(x) for x in signal_info.split(':')[1].split(',')]  # Split the line to get rssi and rsrq
                signal_quality = signal_quality_indicator(rssi, rsrq)
                self.signal_quality_updated.emit(signal_quality)
                print("Signal Quality: " + str(signal_quality)) # delete this line later, for dev purposes only
                break  # Exit the loop once we've found the +CSQ line
        else:
            print("No +CSQ line found in response")
            self.signal_quality_updated.emit(-1)  # Emit special value for no CSQ

class App(QWidget):
    def __init__(self, skip_login=False):
        super().__init__()

        self.tryfi = None
        self.tracking = False
        self.timer = None

        # create the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowTitle('Fiinder')
        self.setGeometry(300, 300, 900, 500)

        # Start the Flask server
        self.flask_process = subprocess.Popen(["python", "/home/alexh/fiinder/server.py"])

        # clear the map cache
        QWebEngineProfile.defaultProfile().clearHttpCache()

        # create the map
        self.map = QWebEngineView()
        self.map.load(QUrl('http://localhost:5000'))
        self.layout.addWidget(self.map, 3, 0, 1, 9)

        # set the stretch factor for the map
        self.layout.setRowStretch(3, 1)

        # initialize gpsd and start updating GPS location
        gpsd.connect()

        # delay the first update_location call
        QTimer.singleShot(1000, self.update_location)

        # create tracking status label
        self.tracking_button = QPushButton('Start Tracking', self)
        self.tracking_button.clicked.connect(self.toggle_tracking)
        self.tracking_button.setFixedSize(115, 30)

        self.layout.addWidget(self.tracking_button, 1, 0)

        # create the GPS fix status indicator
        self.fix_status_icon = QLabel()
        self.layout.addWidget(self.fix_status_icon, 1, 7)

        # create the signal quality indicator
        self.signal_quality_icon = QLabel()
        self.layout.addWidget(self.signal_quality_icon, 1, 8)

        # Add a horizontal spacer at column 6 (or any column to the left of the indicator)
        spacer = QSpacerItem(35, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.layout.addItem(spacer, 1, 6)

        # signal quality threading
        self.signal_quality_thread = SignalQualityThread()
        self.signal_quality_thread.signal_quality_updated.connect(self.update_signal_quality_icon)
        self.signal_quality_thread.start()
        
        if not skip_login:
            self.login()
 
    def update_signal_quality_icon(self, signal_quality):
        print("Updating signal quality icon:", signal_quality) # delete line later, for dev purposes only
        # update the signal quality indicator icon based on signal_quality
        if signal_quality == 1:
            # set icon to excellent
            pixmap = QPixmap('images/excellent.png')
            self.signal_quality_icon.setToolTip('Excellent Signal')
        elif signal_quality == 2:
            # set icon to good
            pixmap = QPixmap('images/good.png')
            self.signal_quality_icon.setToolTip('Good Signal')
        elif signal_quality == 3:
            # set icon to ok
            pixmap = QPixmap('images/ok.png')
            self.signal_quality_icon.setToolTip('OK Signal')
        elif signal_quality == 4:
            # set icon to weak
            pixmap = QPixmap('images/weak.png')
            self.signal_quality_icon.setToolTip('Weak Signal')
        elif signal_quality == 5:
            # set icon to none
            pixmap = QPixmap('images/offline.png')
            self.signal_quality_icon.setToolTip('No Signal')
        else:
            # set icon to error
            pixmap = QPixmap('images/error.png')
            self.signal_quality_icon.setToolTip('Error: No CSQ or unexpected value')

        pixmap = pixmap.scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.signal_quality_icon.setPixmap(pixmap)

    def login(self):
        # initialize the PyTryFi object with the email and password
        email = os.getenv('TRYFI_EMAIL')
        password = os.getenv('TRYFI_PASSWORD')
        self.tryfi = PyTryFi(email, password)

    def update_location(self):
        # Get the current gpsd position
        packet = gpsd.get_current()

        # Get the latitude and longitude
        latitude = packet.lat
        longitude = packet.lon

        # Get the orientation
        orientation = packet.track

        # update the fix status icon
        self.update_fix_status_icon(packet.mode)

        # Send the GPS data to the server
        response = requests.post('http://localhost:5000/update_location', data={'latitude': latitude, 'longitude':
                                                                            longitude, 'orientation': orientation},
                                                                            timeout=5)
        if response.status_code == 200:
            print('Successfully sent GPS data to server')
            print('Received GPS data from server:', response.json())
        else:
            print('Failed to send GPS data to server')
    
        # Schedule the next update
        if self.timer is None or not self.timer.isActive():
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_location)
            self.timer.start(2000)  # start the timer with an interval of 2 seconds
    
    def update_fix_status_icon(self, fix_status):
        # update the fix status indicator icon based on the fix status
        if fix_status == 3:
            # set icon 3d_fix
            pixmap = QPixmap('images/3d_gps.png')
            self.fix_status_icon.setToolTip('3D Fix')

        elif fix_status == 2:
            # set icon to 2d_fix
            pixmap = QPixmap('images/2d_gps.png')
            self.fix_status_icon.setToolTip('2D Fix')
        else:
            # set icon to none
            pixmap = QPixmap('images/no_gps.png')
            self.fix_status_icon.setToolTip('No Fix')

        pixmap = pixmap.scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.fix_status_icon.setPixmap(pixmap)

    def toggle_tracking(self):
        if self.tryfi is None:
            raise ValueError("PyTryFi object not initialized")

        if self.tracking:
            self.tracking = False
            self.tracking_button.setText('Start Tracking')
            self.tryfi.pets[0].setLostDogMode(self.tryfi.session, False)
        else:
            self.tracking = True
            self.tracking_button.setText('Stop Tracking')
            self.tryfi.pets[0].setLostDogMode(self.tryfi.session, True)

        # add a delay before checking the isLost property
        QTimer.singleShot(1000, self.check_and_enable_lost_dog_mode)  # delay of 1000 milliseconds

        # start a timer to check and enable lost dog mode every 5 seconds
        self.lost_dog_mode_timer = QTimer()
        self.lost_dog_mode_timer.timeout.connect(self.check_and_enable_lost_dog_mode)
        self.lost_dog_mode_timer.start(5000)  # interval of 5000 milliseconds

    def check_and_enable_lost_dog_mode(self):
        if not self.tracking:
            return

        print(f"Pet isLost status: {self.tryfi.pets[0].isLost}")
        if not self.tryfi.pets[0].isLost:
            self.tryfi.pets[0].setLostDogMode(self.tryfi.session, True)
        else:
            self.fetch_location()
            self.lost_dog_mode_timer.stop()  # stop the timer once lost dog mode is enabled

    def fetch_location(self):
        if self.tryfi is None:
            # if the PyTryFi object hasn't been initialized, raise an error
            raise ValueError("PyTryFi object not initialized")

        # fetch updated location data from collar
        update_successful = self.tryfi.pets[0].updatePetLocation(self.tryfi.session)

        if update_successful:
            pet = self.tryfi.pets[0]
            latitude = pet._currLatitude
            longitude = pet._currLongitude

            # Send the collar location data to the server
            response = requests.post('http://localhost:5000/update_tracked_location', data={'latitude': latitude,
                                                                                            'longitude': longitude},
                                                                                            timeout=5)

            if response.status_code == 200:
                print('Successfully sent tracked object location data to server')
            else:
                print('Failed to send tracked object location data to server')

        else:
            print("Failed to update pet location")

        # write the lat and long to the labels
        self.latitude_label.setText("Latitude: {:.4f}".format(latitude))
        self.longitude_label.setText("Longitude: {:.4f}".format(longitude))

        # schedule the next update in 15 seconds
        if self.tracking:
            if self.timer is None or not self.timer.isActive():
                self.timer = QTimer()
                self.timer.timeout.connect(self.fetch_location)
                self.timer.start(15000)  # start the timer with an interval of 15000 milliseconds

    def close_event(self, event):
        """Override the default close event handler."""
        # stop the Flask server
        self.flask_process.terminate()

        # continue with the default close event handling
        super().close_event(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = App()
    main.show()

    sys.exit(app.exec_())

app = QApplication([])
window = App()
window.show()
app.exec_()
