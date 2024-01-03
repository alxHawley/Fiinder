from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO


app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    '''Serve the index HTML - this is the embedded map'''
    return render_template('index.html')

@app.route('/update_location', methods=['POST'])
def update_location():
    '''Update the location of the user on the map - this is the device GPS location'''
    # get the GPS data from the post request
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')
    orientation = request.form.get('orientation')  # get the orientation data

    # emit the 'update_location' event with the GPS data
    socketio.emit('update_location', {'latitude': latitude, 'longitude': longitude, 'orientation': orientation})

    # return a success response
    return jsonify({'status': 'success'})

@app.route('/clear_location', methods=['POST'])
def clear_location():
    '''Clear the location of the user on the map - remove device GPS marker if GPS signal is lost'''
    # Emit the 'clear_location' event
    socketio.emit('clear_location')
    # Return a success response
    return jsonify({'status': 'success'})

@app.route('/update_tracked_location', methods=['POST'])
def update_tracked_location():
    '''Update the location of the fi collar on the map - this is the collar GPS location'''
    # get the GPS data from the post request
    latitude = request.form.get('latitude')
    longitude = request.form.get('longitude')

    # emit the 'update_tracked_location' event with the GPS data
    socketio.emit('update_tracked_location', {'latitude': latitude, 'longitude': longitude})

    # return a success response
    return jsonify({'status': 'success'})

@app.route('/hide_marker', methods=['POST'])
def hide_marker():
    '''This hides the fi collar the marker on the map when tracking is disabled'''
    # Emit the 'hide_marker' event
    socketio.emit('hide_marker')
    # Return a success response
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    socketio.run(app)
