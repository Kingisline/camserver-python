import threading
import socket
import cv2
from flask import Flask, Response
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

# ---------- Flask Server ----------

flask_app = Flask(__name__)
camera = None
running = False

def gen():
    global camera, running
    while running:
        ret, frame = camera.read()
        if not ret:
            continue
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               jpeg.tobytes() + b'\r\n')

@flask_app.route('/')
def home():
    return "<h2>Android Cam Server</h2><img src='/video'>"

@flask_app.route('/video')
def video():
    return Response(gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

def run_flask():
    flask_app.run(host='0.0.0.0', port=5000, threaded=True)

# ---------- Kivy UI ----------

KV = """
BoxLayout:
    orientation: "vertical"
    padding: 20
    spacing: 20

    Label:
        text: "Android Python Cam Server"
        font_size: 22

    Button:
        text: "Start Server"
        on_press: app.start()

    Button:
        text: "Stop Server"
        on_press: app.stop()

    Label:
        id: status
        text: "Stopped"

    Label:
        id: ip
        text: ""
"""

class CamApp(App):

    def build(self):
        return Builder.load_string(KV)

    def get_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def start(self):
        global camera, running
        if running:
            return

        camera = cv2.VideoCapture(0)
        running = True

        self.root.ids.status.text = "Running"
        ip = self.get_ip()
        self.root.ids.ip.text = f"http://{ip}:5000"

        threading.Thread(target=run_flask, daemon=True).start()

    def stop(self):
        global camera, running
        running = False
        if camera:
            camera.release()

        self.root.ids.status.text = "Stopped"
        self.root.ids.ip.text = ""

CamApp().run()