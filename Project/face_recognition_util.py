
#* This file contains the utility functions for face recognition.

import face_recognition
import cv2
import numpy as np

def get_face_encoding(image_path):
    """Load an image and return the face encoding.
    :param image_path: path to the image
    :return: face encoding"""
    image = face_recognition.load_image_file(image_path)
    face_encodings = face_recognition.face_encodings(image)
    if len(face_encodings) > 0:
        return face_encodings[0]
    return None

def capture_and_encode_face():
    """Capture a face from the webcam and return the encoding.
    :return: face encoding"""
    video_capture = cv2.VideoCapture(0)

    while True:
        # Grab a single frame of video
        ret, frame = video_capture.read()

        # Find all the faces and face encodings in the current frame of video
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        # Display the results
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit 's' on the keyboard to save the face and quit!
        if cv2.waitKey(1) & 0xFF == ord('s'):
            if len(face_encodings) > 0:
                video_capture.release()
                cv2.destroyAllWindows()
                return face_encodings[0]
            else:
                print("No face detected. Please try again.")

        # Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()
    return None