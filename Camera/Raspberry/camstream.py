import cv2
from flask import Flask, Response
from picamera2 import Picamera2
import Constants
#test
app = Flask(__name__)

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (Constants.CAMERA_FRAME_WIDTH, Constants.CAMERA_FRAME_HEIGHT)}))
picam2.set_controls({"FrameRate": Constants.CAMERA_FRAMERATE})
picam2.start()

def generate_frames():
    while True:
        im = picam2.capture_array()
        ret, jpeg = cv2.imencode('.jpg', im)
        frame = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='5000')