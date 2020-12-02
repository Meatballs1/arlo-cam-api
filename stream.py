import numpy as np
import cv2
import os
import time

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;0"

addr = '172.14.1.194'
url = f"rtsp://{addr}/live"

cap = cv2.VideoCapture(url)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = None

time.sleep(1)
while cap.isOpened():
    width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Width:{width} Height:{height} FPS:{fps}")
    if out is None:
        out = cv2.VideoWriter('output.avi',fourcc, fps, (int(width),int(height)))

    ret, frame = cap.read()
    if not ret:
        print("frame read failed")
        break
    else:
        out.write(frame)

    cv2.imshow('frame',frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cap.release()
out.release()
cv2.destroyAllWindows()
