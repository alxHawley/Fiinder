from tkinter import *
from tkinter import PhotoImage
# pytryfi is installed in a virtual environment that is activated in the .bashrc file
from pytryfi import PyTryFi
import subprocess
import os
from datetime import datetime


class App:
    def __init__(self, master):
        self.master = master
        master.title("Fiinder")

        # load checkmark image for login success gui
        self.checkmark_image = PhotoImage(file="/home/alexh/Fiinder/assets/checkmark-16.png")

        # create the checkmark label
        self.checkmark_label = Label(master, image=self.checkmark_image)

        # create the login button
        self.login_button = Button(master, text="Login", command=self.login)
        self.login_button.pack()

        # create the fetch button
        self.fetch_button = Button(master, text="Fetch Location", command=self.fetch_location)
        self.fetch_button.pack()

        # create the latitude label
        self.latitude_label = Label(master, text="Latitude: ")
        self.latitude_label.pack()

        # create the longitude label
        self.longitude_label = Label(master, text="Longitude: ")
        self.longitude_label.pack()

        # create the map button
        self.map_button = Button(master, text="Open Map", command=self.open_map)
        self.map_button.pack()

        # initialize the PyTryFi object to None
        self.tryfi = None

        # GPX file to monitor for updates to the collar location
        self.file_to_monitor = "/home/alexh/Fiinder/fi_collar.gpx"

    def login(self):
        # initialize the PyTryFi object with the email and password
        self.tryfi = PyTryFi("hawley.ac@gmail.com", "MiZYZEekPMmTwwPk6UDZ")

        # if the login was successful, pack the checkmark label
        if self.tryfi is not None:
            self.checkmark_label.pack()

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
        else:
            print("Failed to update pet location")

        # get the current time in ISO 8601 format
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ")

        # write the lat and long to the fi collar gpx file /home/alexh/Fiinder/fi_collar.gpx
        location_path = os.path.abspath("fi_collar.gpx")
        with open(location_path, "w") as f:
            f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write("<gpx version=\"1.1\" creator=\"Fiinder\" xmlns=\"http://www.topografix.com/GPX/1/1\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:schemaLocation=\"http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd\">\n")
            f.write("  <wpt lat=\"{:.6f}\" lon=\"{:.6f}\">\n".format(latitude, longitude))
            f.write("    <name>Bruce</name>\n")
            f.write("    <comment>{}</comment>\n".format(timestamp))
            f.write("  </wpt>\n")
            f.write("</gpx>\n")

        # write the latitude and longitude to the labels
        self.latitude_label["text"] = "Latitude: {:.4f}".format(latitude)
        self.longitude_label["text"] = "Longitude: {:.4f}".format(longitude)

    def open_map(self):
        # open the map in Viking GPS with the file /home/alexh/Fiinder/fiinder.vik
        subprocess.call(["viking", "fiinder.vik"])

root = Tk()
app = App(root)
root.mainloop()
