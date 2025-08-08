
#* This file contains the main functions for the attendance system.

import database
import face_recognition_util
import numpy as np
import cv2
import face_recognition

def add_student():
    """Capture a student's face and add it to the database with auto-generated unique ID."""
    name = input("Enter student's name: ")
    print("Please look at the camera. Press 's' to save your face.")
    encoding = face_recognition_util.capture_and_encode_face()

    if encoding is not None:
        conn = database.create_connection()
        if conn is not None:
            try:
                student_id, student_uid = database.add_student(conn, name, encoding.tobytes())
                print(f"Student {name} added successfully with ID: {student_uid}")
            except Exception as e:
                print(f"Error adding student: {e}")
            finally:
                conn.close()
        else:
            print("Error: Could not connect to the database.")
    else:
        print("Could not capture face. Please try again.")

import csv
from datetime import datetime

def recognize_and_mark_attendance():
    """Recognize faces from the webcam and mark attendance."""
    class_name = input("Enter class name: ")
    conn = database.create_connection()
    if conn is None:
        print("Error: Could not connect to the database.")
        return

    students = database.get_all_students(conn)
    if not students:
        print("No students found in database. Please add students first.")
        conn.close()
        return

    known_face_encodings = [np.frombuffer(row[3], dtype=np.float64) for row in students]
    known_face_names = [row[2] for row in students]
    known_student_uids = [row[1] for row in students]

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        print("Error: Could not open camera.")
        conn.close()
        return
    
    attendance_records = set()
    last_face_time = None
    no_face_start_time = None
    timeout_duration = 30  # 30 seconds timeout
    
    print(f"\nAttendance session started for class: {class_name}")
    print("Press 'q' to quit or wait 30 seconds without faces to auto-exit")
    print("Detected students will be marked present automatically\n")

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break

        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        
        current_time = cv2.getTickCount() / cv2.getTickFrequency()
        
        # Check if faces are detected
        if face_locations:
            last_face_time = current_time
            no_face_start_time = None
            # Reset timeout display
            cv2.putText(frame, "Face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            if no_face_start_time is None:
                no_face_start_time = current_time
            elif last_face_time is not None:
                time_without_face = current_time - no_face_start_time
                remaining_time = timeout_duration - time_without_face
                
                if remaining_time <= 0:
                    print(f"\nNo faces detected for {timeout_duration} seconds. Ending attendance session.")
                    break
                else:
                    # Display countdown
                    cv2.putText(frame, f"No face - Auto-exit in: {int(remaining_time)}s", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Process detected faces
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                student_uid = known_student_uids[best_match_index]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if student_uid not in attendance_records:
                    database.add_attendance(conn, student_uid, class_name, timestamp)
                    attendance_records.add(student_uid)
                    print(f"✓ Marked {name} ({student_uid}) as present.")

        # Display attendance info on frame
        cv2.putText(frame, f"Class: {class_name}", (10, frame.shape[0] - 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"Present: {len(attendance_records)}/{len(students)}", (10, frame.shape[0] - 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit", (10, frame.shape[0] - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow('Attendance System', frame)

        # Check for quit key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\nAttendance session ended by user.")
            break

    video_capture.release()
    cv2.destroyAllWindows()
    conn.close()
    
    print(f"\nAttendance session completed!")
    print(f"Total students marked present: {len(attendance_records)}/{len(students)}")
    if attendance_records:
        export_attendance(class_name)
    else:
        print("No attendance records to export.")

def export_attendance(class_name):
    """Export attendance to a CSV file."""
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
        writer.writerow(["Student UID", "Student Name", "Class Name", "Timestamp"])
        writer.writerows(records)
    
    print(f"Attendance exported to {filename}")

def view_all_students():
    """Display all registered students with their auto-generated IDs."""
    conn = database.create_connection()
    if conn is None:
        print("Error: Could not connect to the database.")
        return
    
    try:
        students_info = database.display_all_students(conn)
        print(students_info)
    except Exception as e:
        print(f"Error retrieving students: {e}")
    finally:
        conn.close()

def search_student_by_id():
    """Search for a student by their auto-generated ID."""
    student_uid = input("Enter student ID to search: ").strip().upper()
    
    conn = database.create_connection()
    if conn is None:
        print("Error: Could not connect to the database.")
        return
    
    try:
        student = database.get_student_by_uid(conn, student_uid)
        if student:
            print(f"\nStudent found:")
            print(f"ID: {student[1]}")
            print(f"Name: {student[2]}")
            print(f"Database ID: {student[0]}")
        else:
            print(f"No student found with ID: {student_uid}")
    except Exception as e:
        print(f"Error searching for student: {e}")
    finally:
        conn.close()

def main():
    """Main function to run the application."""
    # Create database and table if they don't exist
    conn = database.create_connection()
    if conn is not None:
        database.create_table(conn)
        conn.close()

    while True:
        print("\nMenu:")
        print("1. Add a new student")
        print("2. Recognize and mark attendance")
        print("3. View all registered students")
        print("4. Search student by ID")
        print("5. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            add_student()
        elif choice == '2':
            recognize_and_mark_attendance()
        elif choice == '3':
            view_all_students()
        elif choice == '4':
            search_student_by_id()
        elif choice == '5':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()