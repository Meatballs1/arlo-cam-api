import flask
import threading
import sqlite3
import json
from arlo.camera import Camera
from arlo.messages import Message

app = flask.Flask(__name__)
app.config["DEBUG"] = False
app.use_reloader=False


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
                (ip,serial_number,hostname,registration,status) = row
                cameras.append({"ip":ip,"hostname":hostname,"serial_number":serial_number})

        return flask.jsonify(cameras)

@app.route('/camera/<serial>', methods=['GET'])
def status(serial):
    with sqlite3.connect('arlo.db') as conn:
        c = conn.cursor()
        c.execute("SELECT status FROM camera WHERE serial = ?", (serial,))
        (status,) = c.fetchone()
        if status is not None and status != "None":
            return flask.jsonify(json.loads(status))
        else:
            flask.abort(404)

threading.Thread(target=app.run).start()
