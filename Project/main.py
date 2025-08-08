import database
import face_recognition_util
import numpy as np
import cv2
import face_recognition

def add_student():
    """
    Capture a student's face and add it to the database.
    """
    name = input("Enter student's name: ")
    print("Please look at the camera. Press 's' to save your face.")
    encoding = face_recognition_util.capture_and_encode_face()

    if encoding is not None:
        conn = database.create_connection()
        if conn is not None:
            database.add_student(conn, name, encoding.tobytes())
            conn.close()
            print(f"Student {name} added successfully.")
        else:
            print("Error: Could not connect to the database.")
    else:
        print("Could not capture face. Please try again.")

import csv
from datetime import datetime

def recognize_and_mark_attendance():
    """
    Recognize faces from the webcam and mark attendance.
    """
    class_name = input("Enter class name: ")
    conn = database.create_connection()
    if conn is None:
        print("Error: Could not connect to the database.")
        return

    students = database.get_all_students(conn)
    known_face_encodings = [np.frombuffer(row[2], dtype=np.float64) for row in students]
    known_face_names = [row[1] for row in students]
    student_ids = [row[0] for row in students]

    video_capture = cv2.VideoCapture(0)
    
    attendance_records = set()

    while True:
        ret, frame = video_capture.read()

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                student_id = student_ids[best_match_index]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if student_id not in attendance_records:
                    database.add_attendance(conn, student_id, class_name, timestamp)
                    attendance_records.add(student_id)
                    print(f"Marked {name} as present.")


        cv2.imshow('Video', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    conn.close()
    export_attendance(class_name)

def export_attendance(class_name):
    """
    Export attendance to a CSV file.
    """
    conn = database.create_connection()
    if conn is None:
        print("Error: Could not connect to the database.")
        return

    records = database.get_attendance_by_class(conn, class_name)
    conn.close()

    if not records:
        print("No attendance records to export.")
        return

    filename = f"attendance_{class_name}_{datetime.now().strftime('%Y-%m-%d')}.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Student Name", "Class Name", "Timestamp"])
        writer.writerows(records)
    
    print(f"Attendance exported to {filename}")

def main():
    """
    Main function to run the application.
    """
    # Create database and table if they don't exist
    conn = database.create_connection()
    if conn is not None:
        database.create_table(conn)
        conn.close()

    while True:
        print("\nMenu:")
        print("1. Add a new student")
        print("2. Recognize and mark attendance")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            add_student()
        elif choice == '2':
            recognize_and_mark_attendance()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()