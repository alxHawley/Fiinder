from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO


app = Flask(__name__)
socketio = SocketIO(app, asysnc_mode='threading')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_location', methods=['POST'])
def update_location():
    # get the GPS data from the request
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    orientation = request.form.get('orientation')  # get the orientation data

    # emit the 'update_location' event with the GPS data
    socketio.emit('update_location', {'latitude': latitude, 'longitude': longitude, 'orientation': orientation})

    # return a success response
    return jsonify({'status': 'success'})

@app.route('/update_tracked_location', methods=['POST'])
def update_tracked_location():
    # get the GPS data from the request
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # emit the 'update_tracked_location' event with the GPS data
    socketio.emit('update_tracked_location', {'latitude': latitude, 'longitude': longitude})

    # return a success response
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    socketio.run(app)
