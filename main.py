import os
from datetime import datetime

import cv2
import face_recognition
import numpy as np

path = "ImagesAttendence"
images = []
classNames = []
myList = os.listdir(path)
print(myList)

for cl in myList:
    curImage = cv2.imread(f"{path}/{cl}")
    images.append(curImage)
    classNames.append(os.path.splitext(cl)[0])
print(classNames)

# Add Haar cascade
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList


def markAttendence(name):
    with open("Attendence.csv", "r+") as f:
        myDataList = f.readlines()
        nameList = []
        for line in myDataList:
            entry = line.split(",")
            nameList.append(entry[0])
        if name not in nameList:
            now = datetime.now()
            dtString = now.strftime("%H:%M:%S")
            f.writelines(f"\n{name},{dtString}")


encodeListKnown = findEncodings(images)
print("Encoding Complete")

cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Replace face_recognition detection with Haar cascade
    gray = cv2.cvtColor(imgS, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    # Convert Haar cascade format to face_recognition format
    facesCurFrame = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
    encodeCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodeCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        print(faceDis)

        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            name = classNames[matchIndex].upper()
            print(name)
            y1, x2, y2, x1 = faceLoc

            # Scale up
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            # Convert to (x, y, w, h)
            x, y, w, h = x1, y1, x2 - x1, y2 - y1
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.rectangle(img, (x, y + h - 35), (x + w, y + h), (0, 255, 0), cv2.FILLED)
            cv2.putText(
                img,
                name,
                (x + 6, y + h - 6),
                cv2.FONT_HERSHEY_COMPLEX,
                1,
                (255, 255, 255),
                2,
            )
            markAttendence(name)

    cv2.imshow("Webcam", img)
    cv2.waitKey(1)
