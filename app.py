"""
Smart Home Controller - Flask Backend (Virtual Simulation)
"""

import threading

from flask import Flask, jsonify, render_template, request

from smart_home_state import home, background_ticker

app = Flask(__name__)


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/latest")
def api_latest():
    return jsonify(home.snapshot())


@app.route("/api/light_level", methods=["POST"])
def api_light_level():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(home.set_light_level(data.get("value", 55)))


@app.route("/api/temperature", methods=["POST"])
def api_temperature():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(home.set_temperature(data.get("value", 24)))


@app.route("/api/motion", methods=["POST"])
def api_motion():
    return jsonify(home.trigger_motion())


@app.route("/api/security", methods=["POST"])
def api_security():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(home.set_security_mode(data.get("enabled", False)))


@app.route("/api/manual", methods=["POST"])
def api_manual():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(home.set_manual_override(data.get("enabled", False)))


@app.route("/api/manual_control", methods=["POST"])
def api_manual_control():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(home.set_manual_device(data.get("device"), data.get("state", False)))


@app.route("/api/reset", methods=["POST"])
def api_reset():
    return jsonify(home.reset())


def start_background_thread():
    t = threading.Thread(target=background_ticker, daemon=True)
    t.start()


start_background_thread()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
