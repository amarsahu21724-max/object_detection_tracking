import streamlit as st
import cv2
import tempfile
import os
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

st.title("🎯 Object Detection & Tracking")

model = YOLO("yolov8s.pt")
tracker = DeepSort(max_age=30)

source = st.selectbox(
    "Select Source",
    ["Dataset Video", "Upload Video", "Webcam"]
)

cap = None

if source == "Dataset Video":
    video = st.selectbox("Choose Video", os.listdir("dataset"))
    if st.button("Start Detection"):
        cap = cv2.VideoCapture(f"dataset/{video}")

elif source == "Upload Video":
    file = st.file_uploader("Upload Video", ["mp4", "avi", "mov"])
    if file:
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(file.read())
        cap = cv2.VideoCapture(temp.name)

else:
    st.info("Webcam works locally. Use Upload Video after deployment.")
    if st.button("Start Camera"):
        cap = cv2.VideoCapture(0)

if cap:

    frame_area = st.empty()

    while cap.isOpened():

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (800, 500))

        detections = []

        for r in model(frame, verbose=False):
            for b in r.boxes:

                x1, y1, x2, y2 = map(int, b.xyxy[0])
                conf = float(b.conf[0])
                cls = int(b.cls[0])

                if conf > 0.5:
                    detections.append(
                        ([x1, y1, x2-x1, y2-y1], conf, cls)
                    )

        tracks = tracker.update_tracks(
            detections,
            frame=frame
        )

        for t in tracks:

            if not t.is_confirmed():
                continue

            x1, y1, x2, y2 = map(int, t.to_ltrb())
            label = model.names[int(t.det_class)]

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            cv2.putText(
                frame,
                f"{label} ID:{t.track_id}",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        frame_area.image(
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
            use_container_width=True
        )

    cap.release()