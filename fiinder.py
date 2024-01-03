"""
This is the main application file for the Fiinder application.
"""
import sys
import os
import subprocess
import time
from utils.modem_comm import open_modem_connection, at_csq, signal_quality_indicator
# pylint: disable=no-name-in-module
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
from PyQt5.QtWidgets import QGridLayout,QSpacerItem, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal
# pylint: enable=no-name-in-module
from pytryfi import PyTryFi
import requests
import gpsd


class SignalQualityThread(QThread):
    """Thread for updating the signal quality indicator."""
    signal_quality_updated = pyqtSignal(int)

    def run(self):
        """Run the signal quality thread."""
        port = "/dev/ttyUSB2"
        ser = open_modem_connection(port)
        if ser is not None:
            while True:
                self.update_signal_quality(ser)
                time.sleep(5)  # Delay for 5 seconds

    def update_signal_quality(self, ser):
        """Parse the response from the modem and emit the signal quality value."""
        response = at_csq(ser)
        # print(response) # dev/delete
        # parse response to get rssi and rsrq values
        for line in response:
            signal_info = line.decode('utf-8').strip()  # Remove newline characters
            if signal_info.startswith('+CSQ:'):
                rssi, rsrq = [int(x) for x in signal_info.split(':')[1].split(',')]
                signal_quality = signal_quality_indicator(rssi, rsrq)
                self.signal_quality_updated.emit(signal_quality)
                # print("Signal Quality: " + str(signal_quality)) # dev/delete
                break  # Exit the loop once +CSQ line is found
        else:
            # print("No +CSQ line found in response") # dev/delete
            self.signal_quality_updated.emit(-1)  # Emit special value for no CSQ for indicator
            # !!add modem utils to restart modem or initiatete scan/a new connection

class App(QWidget):
    """The main application window."""

    def __init__(self, skip_login=False):
        """Initialize the application window."""
        super().__init__()

        # initialize instance variables
        self.tryfi = None
        self.tracking = False
        self.has_fix = False

        # TIMERS ##################################

        # start the timer to check the server status
        self.server_status_timer = QTimer()
        self.server_status_timer.timeout.connect(self.check_server_status)
        self.server_status_timer.start(1000)  # check every second

        # create the update location timer
        self.update_location_timer = QTimer()

        # create the lost dog mode timer
        self.lost_dog_mode_timer = QTimer()

        # create the tracking timer
        self.tracking_timer = QTimer()

        # create the fetch location timer
        self.fetch_timer = QTimer()

        if not skip_login:
            self.login()

        # create the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.setWindowTitle('Fiinder')
        self.setGeometry(300, 300, 900, 500)

        # Start the Flask server
        self.flask_process = subprocess.Popen(["python", "/home/alexh/Fiinder/server.py"])

        # create a network access manager
        self.manager = QNetworkAccessManager()

        # clear the map cache
        QWebEngineProfile.defaultProfile().clearHttpCache()

        # create the map
        self.map = QWebEngineView()
        self.layout.addWidget(self.map, 3, 0, 1, 9)

        # set the stretch factor for the map
        self.layout.setRowStretch(3, 1)

        # initialize gpsd and start updating GPS location
        gpsd.connect()

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

    def update_signal_quality_icon(self, signal_quality):
        """Update the signal quality indicator icon."""
        # print("Updating signal quality icon:", signal_quality) # dev/delete
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

    def check_server_status(self):
        """Check the server status and load the map if the server is up."""
        request = QNetworkRequest(QUrl('http://localhost:5000'))
        self.manager.head(request)  # send a HEAD request to the server
        self.manager.finished.connect(self.on_finished)

    def on_finished(self, reply):
        """Handle the finished signal of the network access manager."""
        if reply.error() == QNetworkReply.NoError:
            # the server is up, stop the timer and load the map
            self.server_status_timer.stop()
            self.map.load(QUrl('http://localhost:5000'))

            # Call update_location after the map has loaded
            self.update_location()

        reply.deleteLater()  # clean up

    def login(self):
        """Log in to the Fi server and initialize the PyTryFi object."""
        # initialize the PyTryFi object with the email and password
        email = os.getenv('TRYFI_EMAIL')
        password = os.getenv('TRYFI_PASSWORD')
        self.tryfi = PyTryFi(email, password)

    def update_location(self):
        """Update the GPS location of the device and send it to the server."""
        # Get the current gpsd position
        packet = gpsd.get_current()

        # Check if a GPS fix has been acquired
        if packet.mode >= 2:
            # Get the latitude and longitude
            latitude = packet.lat
            longitude = packet.lon

            # Get the orientation
            orientation = packet.track

            # Send the GPS data to the server
            response = requests.post('http://localhost:5000/update_location',
                                    data={'latitude': latitude, 'longitude':
                                    longitude, 'orientation': orientation},
                                    timeout=5)
            if response.status_code == 200:
                print('***Successfully sent GPS location to server***')
            else:
                print('***Failed to send GPS location to server***')

        # Update the fix status icon regardless of whether a fix has been obtained
        self.update_fix_status_icon(packet.mode)

        # Schedule the next update
        if self.update_location_timer is None or not self.update_location_timer.isActive():
            self.update_location_timer.timeout.connect(self.update_location)
            self.update_location_timer.start(2000)  # start the timer with an interval of 2 seconds

    def update_fix_status_icon(self, fix_status):
        """Update the GPS fix status indicator icon."""
        # update the fix status indicator icon based on the fix status
        if fix_status == 3:
            # set icon 3d_fix
            pixmap = QPixmap('images/3d_gps.png')
            self.fix_status_icon.setToolTip('3D Fix')
            self.has_fix = True

        elif fix_status == 2:
            # set icon to 2d_fix
            pixmap = QPixmap('images/2d_gps.png')
            self.fix_status_icon.setToolTip('2D Fix')
            self.has_fix = True
        else:
            # set icon to none
            pixmap = QPixmap('images/no_gps.png')
            self.fix_status_icon.setToolTip('No Fix')

            # If the fix status has changed from having a fix to not having a fix, send a request to the server to clear the location
            if self.has_fix:

                # Send a request to the server to clear the location
                try:
                    response = requests.post('http://localhost:5000/clear_location', timeout=5)
                    if response.status_code == 200:
                        print('***Successfully sent clear location to server***')
                except requests.exceptions.RequestException as err:
                    print ("Error sending clear location request", err)
                self.has_fix = False

        pixmap = pixmap.scaled(25, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.fix_status_icon.setPixmap(pixmap)

    def toggle_tracking(self):
        """Toggle tracking mode on or off."""
        if self.tryfi is None:
            raise ValueError("PyTryFi object not initialized")

        if self.tracking:
            self.tracking = False
            self.tracking_button.setText('Start Tracking')
            self.tryfi.pets[0].setLostDogMode(self.tryfi.session, False)
            self.lost_dog_mode_timer.stop()  # stop lost dog timer when you stop tracking
            if self.tracking_timer is not None:
                self.tracking_timer.stop()  # stop tracking timer when you stop tracking
            if self.fetch_timer is not None:
                self.fetch_timer.stop()  # stop the fetch_location timer when you stop tracking
                requests.post('http://localhost:5000/hide_marker', timeout=5)
        else:
            self.tracking = True
            self.tracking_button.setText('Stop Tracking')
            self.tryfi.pets[0].setLostDogMode(self.tryfi.session, True)
            self.lost_dog_mode_timer.start(5000)  # start lost_mode timer when tracking starts
            if self.tracking_timer is None:
                self.tracking_timer.timeout.connect(self.fetch_location)
            self.tracking_timer.start(5000)  # start fetch_location timer when tracking starts

        # add a delay before checking the isLost property
        QTimer.singleShot(1000, self.check_and_enable_lost_dog_mode)  # delay of 1000 milliseconds

    def check_and_enable_lost_dog_mode(self):
        """Check the isLost property of the pet and enable lost dog mode if it."""
        if not self.tracking:
            return

        print(f"Pet isLost status: {self.tryfi.pets[0].isLost}")
        if not self.tryfi.pets[0].isLost:
            self.tryfi.pets[0].setLostDogMode(self.tryfi.session, True)
        else:
            self.fetch_location()

    def fetch_location(self):
        """Fetch the location of the fi collar and send it to the server."""
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
            response = requests.post('http://localhost:5000/update_tracked_location',
                                     data={'latitude': latitude, 'longitude': longitude}, timeout=5)

            if response.status_code == 200:
                print('*****COLLAR location sent to server*****')
            else:
                print('*****COLLAR location failed to send to server*****')

        else:
            print("Failed to update pet location")

        # schedule the next update in 5 seconds
        if self.tracking:
            if self.fetch_timer is None or not self.fetch_timer.isActive():
                self.fetch_timer.timeout.connect(self.fetch_location)
                self.fetch_timer.start(5000)  # start the timer with an interval

    def closeEvent(self, event): # pylint: disable=invalid-name
        """Override the default close event handler."""
        # stop the Flask server
        self.flask_process.kill()

        # continue with the default close event handling
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = App()
    main.show()
    sys.exit(app.exec_())

app = QApplication([])
window = App()
window.show()
app.exec_()
