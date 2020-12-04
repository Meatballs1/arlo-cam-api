import flask
import threading
import sqlite3
import json
import functools
import os
from arlo.camera import Camera
from arlo.messages import Message
from flask import g

app = flask.Flask(__name__)
app.config["DEBUG"] = False
app.use_reloader=False

def validate_camera_request(body_required=True):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            g.camera = Camera.from_db_serial(kwargs['serial'])
            if g.camera is None:
                flask.abort(404)

            if body_required:
                g.args = flask.request.get_json()
                if g.args is None:
                    flask.abort(400)

            return f(*args,**kwargs)
        return wrapper
    return decorator

@app.route('/', methods=['GET'])
def home():
    return "PING"

@app.route('/camera', methods=['GET'])
def list():
    with sqlite3.connect('arlo.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM camera")
        rows = c.fetchall()
        cameras = []
        if rows is not None:
            for row in rows:
                (ip,serial_number,hostname,registration,status,friendly_name) = row
                cameras.append({"ip":ip,"hostname":hostname,"serial_number":serial_number,"friendly_name":friendly_name})

        return flask.jsonify(cameras)

@app.route('/camera/<serial>', methods=['GET'])
@validate_camera_request(body_required=False)
def status(serial):
    if g.camera.status is None:
        return flask.jsonify({})
    else:
        return flask.jsonify(g.camera.status.dictionary)

@app.route('/camera/<serial>/registration', methods=['GET'])
@validate_camera_request(body_required=False)
def registration(serial):
    if g.camera.registration is None:
        return flask.jsonify({})
    else:
        return flask.jsonify(g.camera.registration.dictionary)

@app.route('/camera/<serial>/statusrequest', methods=['POST'])
@validate_camera_request(body_required=False)
def status_request(serial):
    result = g.camera.status_request()
    return flask.jsonify({"result":result})

@app.route('/camera/<serial>/userstreamactive', methods=['POST'])
@validate_camera_request()
def user_stream_active(serial):
    active = g.args["active"]
    if active is None:
        flask.abort(400)

    result = g.camera.set_user_stream_active(int(active))
    return flask.jsonify({"result":result})

@app.route('/camera/<serial>/arm', methods=['POST'])
@validate_camera_request()
def arm(serial):
    result = g.camera.arm(g.args)
    return flask.jsonify({"result":result})

@app.route('/camera/<serial>/pirled', methods=['POST'])
@validate_camera_request()
def pir_led(serial):
    result = g.camera.pir_led(g.args)
    return flask.jsonify({"result":result})

@app.route('/camera/<serial>/quality', methods=['POST'])
@validate_camera_request()
def set_quality(serial):
    if g.args['quality'] is None:
        flask.abort(400)
    else:
        result = g.camera.set_quality(g.args)
        return flask.jsonify({"result":result})

@app.route('/camera/<serial>/snapshot', methods=['POST'])
@validate_camera_request()
def request_snapshot(serial):
    if g.args['url'] is None:
        flask.abort(400)
    else:
        result = g.camera.snapshot_request(g.args['url'])
        return flask.jsonify({"result":result})

@app.route('/camera/<serial>/audiomic', methods=['POST'])
@validate_camera_request()
def request_mic(serial):
    if g.args['enabled'] is None:
        flask.abort(400)
    else:
        result = g.camera.mic_request(g.args['enabled'])
        return flask.jsonify({"result":result})

@app.route('/camera/<serial>/audiospeaker', methods=['POST'])
@validate_camera_request()
def request_speaker(serial):
    if g.args['enabled'] is None:
        flask.abort(400)
    else:
        result = g.camera.speaker_request(g.args['enabled'])
        return flask.jsonify({"result":result})

@app.route('/camera/<serial>/record', methods=['POST'])
@validate_camera_request()
def request_record(serial):
    if g.args['duration'] is None:
        flask.abort(400)
    else:
        result = g.camera.record(g.args['duration'])
        return flask.jsonify({"result":result})

@app.route('/camera/<serial>/friendlyname', methods=['POST'])
@validate_camera_request()
def set_friendlyname(serial):
    if g.args['name'] is None:
        flask.abort(400)
    else:
        g.camera.friendly_name = g.args['name']
        g.camera.persist()

        return flask.jsonify({"result":True})

@app.route('/camera/<serial>/activityzones', methods=['POST','DELETE'])
@validate_camera_request()
def set_activity_zones(serial):
    if flask.request.method == 'DELETE':
        result = g.camera.unset_activity_zones()
    else:
        result = g.camera.set_activity_zones(g.args)

    return flask.jsonify({"result":result})

@app.route('/snapshot/<identifier>/', methods=['POST'])
def receive_snapshot(identifier):
    if 'file' not in flask.request.files:
        abort(400)
    else:
        file = flask.request.files['file']
        if file.filename=='':
            abort(400)
        else:
            start_path = os.path.abspath('/tmp')
            target_path = os.path.join(start_path,f"{identifier}.jpg")
            common_prefix = os.path.commonprefix([target_path, start_path])
            if (common_prefix != start_path):
                abort(400)
            else:
                file.save(target_path)
            return ""


def get_thread():
    return threading.Thread(target=app.run(host='0.0.0.0'))
