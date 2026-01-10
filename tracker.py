#  python3 tracker.py to run
import cv2
from ultralytics import YOLO
import requests
import time

# load model
model = YOLO("yolov8l.pt")

# initialise the webcam
cap = cv2.VideoCapture(0)

# parameters
BASELINE_FRAMES = 30 
DROP_FRAMES = 15  
ALPHA = 0.6

baseline_samples = []
baseline_count = None
smoothed_count = None
drop_counter = 0
alarm_triggered = False

FLASK_ALERT_URL = "http://127.0.0.1:5000/trigger-alert"

last_flask_alert = 0
FLASK_COOLDOWN = 10  # seconds (prevents email spam)

# reads the next frame from the stream
ret, frame = cap.read()
if not ret:
    raise RuntimeError("Camera failed to start")

# initializes the tracking portion of the frame
h, w, _ = frame.shape
region = (0, 0, w, h)

while True:
    # reads the next frame from the stream
    ret, frame = cap.read()
    if not ret:
        break

    # detect the objects
    results = model(frame, conf=0.25, verbose=False)[0]
    object_count = 0

    # if anything was detected in the frame
    if results.boxes is not None:
        # loop over the boxes
        for box in results.boxes:
            # id and labels
            cls = int(box.cls[0])
            label = model.names[cls]

            # disregard "person" label
            if label == "person":
                continue

            # get bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # if the object is in the protected region, object is present, draw and label
            if region[0] < cx < region[2] and region[1] < cy < region[3]:
                object_count += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

    # smooth out the count if the frames flicker
    if smoothed_count is None:
        smoothed_count = object_count
    else:
        smoothed_count = int(ALPHA * smoothed_count + (1 - ALPHA) * object_count)

    # counts the initial and stable number of objects in the frame
    if baseline_count is None:
        baseline_samples.append(smoothed_count)
        cv2.putText(frame, "Calibrating baseline...",
                    (40, 110), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (0, 255, 255), 2)

        # when enough frames have passed, the baseline can be set
        if len(baseline_samples) >= BASELINE_FRAMES:
            baseline_count = round(sum(baseline_samples) / len(baseline_samples))
            print(f"Baseline locked at {baseline_count} objects")
        continue

    # theft logic
    if smoothed_count < baseline_count:
        drop_counter += 1
    else:
        drop_counter = 0

    # trigger alarm
    if drop_counter >= DROP_FRAMES and not alarm_triggered:
        alarm_triggered = True
        print("🚨 ALERT: OBJECT REMOVED!")

        now = time.time()
        if now - last_flask_alert > FLASK_COOLDOWN:
            try:
                requests.get(FLASK_ALERT_URL, timeout=1)
                print("Flask alert triggered")
            except requests.exceptions.RequestException as e:
                print("Failed to reach Flask server:", e)

            last_flask_alert = now

    # display the status
    if alarm_triggered:
        status = "STATUS: ALERT (OBJECT REMOVED)"
        color = (0, 0, 255)
    else:
        status = "STATUS: SAFE"
        color = (0, 255, 0)

    # show status
    cv2.putText(frame, status, (40, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)

    # current object, baseline object count
    cv2.putText(frame, f"Baseline: {baseline_count}  Current: {smoothed_count}", (40, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # frame title
    cv2.imshow("Object Guard", cv2.resize(frame, (1280, 720)))

    # press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()