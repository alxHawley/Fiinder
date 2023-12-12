# Fiinder - A Simple Python application with GPS & LTE-M connectivity

Fiinder is a Python application that utilizes the [PyTryFi](https://github.com/sbabcock23/pytryfi) interface to interact with the Fi dog tracking collar. I started this project to extend tracking capabilities into more remote areas. The problem solved by the application and hardware, is that the Fi collar operates on the LTE-M network which often times reaches 2x as far as other 4g/5g bands. This creates a fringe zone where the collar is fully operable but the Android or IOS app does not have service. I wanted to be able to use the tracking capabilities of the collar in those areas where LTE-M is available but cell phones are out of range. The app can run in a desktop environment but it is being built for a mobile handheld device that has GPS and Cellular connectivity.

The project is still in development wtih plans for code optimization, offline mapping, and more robust features and utlities.

## Hardware:
Raspberry Pi 4

Sixfab 3g/4g LTE Base Hat

Telit ME910C1-WW Mini PCle LTE-M Module

Adafruit Ultimate GPS & active antenna

## Application:
Python

[PyQt5 (GUI)](https://pypi.org/project/PyQt5)

[Flask](https://pypi.org/project/Flask/)

[Soket.IO](https://socket.io/)

[GPSD (GPS receiver monitor)](https://gpsd.gitlab.io/gpsd/)

[Leaflet.js (Interactive mapping)](https://leafletjs.com/)

JS

HTML

[Thunderforest (Map provider)](https://www.thunderforest.com/)

## Current Features and Functionality:

Cellular signal quality indicator supported by a modem utility which constantly reads signal quality

GPS fix indicator for 3D, 2D, and no fix, reported from GPSD monitoring external GPS

Online mapping optimized using concurrent requests to multiple tile subdomains to decrease latency/ map rendering issues

Tracking using PyTryFi

## How it works (in a nutshell):
