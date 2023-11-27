from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGridLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebEngineWidgets import QWebEngineProfile
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QTimer
import sys
import os
import subprocess
from pytryfi import PyTryFi
import requests
import gpsd


class App(QWidget):
    def __init__(self):
        super().__init__()

        self.tryfi = None
        self.tracking = False
        self.timer = None
        self.checkmark_label = None

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
        self.layout.addWidget(self.map, 3, 0, 1, 2)
    
        # set the stretch factor for the map
        self.layout.setRowStretch(3, 1)

        # set the stretch factor for the columns
        self.layout.setColumnStretch(0, 1)
        self.layout.setColumnStretch(1, 1)
        
        # create the login status label
        self.login_status_label = QLabel(self)
        self.login_status_label.setText("Logging in...")
        self.login_status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.login_status_label, 0, 0)

        # create the checkmark label
        self.checkmark_label = QLabel(self)
        self.checkmark_label.setPixmap(QPixmap('assets/checkmark-16.png'))
        self.checkmark_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.checkmark_label, 0, 1)
        self.checkmark_label.hide()

        # create tracking status label
        self.tracking_button = QPushButton('Start Tracking', self)
        self.tracking_button.clicked.connect(self.toggle_tracking)

        self.layout.addWidget(self.tracking_button, 1, 0, 1, 2)

        # create the latitude label
        self.latitude_label = QLabel(self)
        self.latitude_label.setText("Latitude: ")
        self.layout.addWidget(self.latitude_label, 2, 0)

        # create the longitude label
        self.longitude_label = QLabel(self)
        self.longitude_label.setText("Longitude: ")
        self.layout.addWidget(self.longitude_label, 2, 1)

        # initialize gpsd and start updating GPS location
        gpsd.connect()

        self.login()

        # delay the first update_location call
        QTimer.singleShot(5000, self.update_location)  # delay of 5000 milliseconds

    def login(self):
        # initialize the PyTryFi object with the email and password
        email = os.getenv('TRYFI_EMAIL')
        password = os.getenv('TRYFI_PASSWORD')
        self.tryfi = PyTryFi(email, password)

        # if the login was successful update ui
        if self.tryfi is not None:
            # update the login status label
            self.login_status_label.setText("Login successful")

            # show the checkmark label
            self.checkmark_label.show()

    def update_location(self):
        # Get the current gpsd position
        packet = gpsd.get_current()

        # Get the latitude and longitude
        latitude = packet.lat
        longitude = packet.lon

        # Get the orientation
        orientation = packet.track

        # Send the GPS data to the server
        response = requests.post('http://localhost:5000/update_location', data={'latitude': latitude, 'longitude': longitude, 'orientation': orientation})
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

            # Send the tracked object's location data to the server
            response = requests.post('http://localhost:5000/update_tracked_location', data={'latitude': latitude, 'longitude': longitude})

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

    def closeEvent(self, event):
        # stop the Flask server
        self.flask_process.terminate()

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
