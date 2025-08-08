
# * This file contains the database functions for the attendance system.

import sqlite3
import uuid
from typing import List, Optional, Tuple

DB_PATH = "attendance.db"


def create_connection() -> (
    sqlite3.Connection
):  # Create a database connection to the SQLite database.
    return sqlite3.connect(DB_PATH)


def create_table(
    conn: sqlite3.Connection,
) -> None:  # Create tables if they do not exist (idempotent).
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_uid TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            encoding BLOB NOT NULL
        );
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_uid TEXT NOT NULL,
            class_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (student_uid) REFERENCES students (student_uid)
        );
        """
    )

    conn.commit()


def reset_database(
    conn: sqlite3.Connection,
) -> None:  # Drop and recreate all tables. This will WIPE ALL DATA.
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS attendance")
    cursor.execute("DROP TABLE IF EXISTS students")
    conn.commit()
    create_table(conn)


def generate_unique_student_id(
    conn: sqlite3.Connection,
) -> str:  # Generate a unique 8-char student UID that does not exist in DB
    cursor = conn.cursor()
    while True:
        candidate = str(uuid.uuid4())[:8].upper()
        cursor.execute(
            "SELECT 1 FROM students WHERE student_uid = ? LIMIT 1", (candidate,)
        )
        if cursor.fetchone() is None:
            return candidate


def add_student(
    conn: sqlite3.Connection, name: str, encoding: bytes
) -> Tuple[int, str]:
    """Insert a new student with an auto-generated unique student_uid. Returns a tuple of (student_db_id, student_uid)."""
    student_uid = generate_unique_student_id(conn)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO students (student_uid, name, encoding) VALUES (?, ?, ?)",
        (student_uid, name, encoding),
    )
    conn.commit()
    return cursor.lastrowid, student_uid


def add_attendance(
    conn: sqlite3.Connection, student_uid: str, class_name: str, timestamp: str
) -> (
    int
):  # Insert a new attendance record using student_uid. Returns the inserted row id.
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO attendance (student_uid, class_name, timestamp) VALUES (?, ?, ?)",
        (student_uid, class_name, timestamp),
    )
    conn.commit()
    return cursor.lastrowid


def get_attendance_by_class(
    conn: sqlite3.Connection, class_name: str
) -> List[
    Tuple[str, str, str, str]
    # Return attendance rows (student_uid, student_name, class_name, timestamp) for a class.
]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT a.student_uid, s.name, a.class_name, a.timestamp
        FROM attendance a
        JOIN students s ON a.student_uid = s.student_uid
        WHERE a.class_name = ?
        """,
        (class_name,),
    )
    return cursor.fetchall()


def get_all_students(
    conn: sqlite3.Connection,
) -> List[
    Tuple[int, str, str, bytes]
]:  # Return all students as (id, student_uid, name, encoding).
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_uid, name, encoding FROM students ORDER BY id ASC"
    )
    return cursor.fetchall()


def get_student_by_uid(
    conn: sqlite3.Connection, student_uid: str
) -> Optional[
    Tuple[int, str, str, bytes]
]:  # Return a single student row (id, student_uid, name, encoding) or None.
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, student_uid, name, encoding FROM students WHERE student_uid = ?",
        (student_uid,),
    )
    return cursor.fetchone()


def display_all_students(
    conn: sqlite3.Connection,
    # Return a formatted string listing all students with their IDs and names.
) -> str:
    students = get_all_students(conn)
    if not students:
        return "No students found in the database."

    header = f"{'ID':<12} {'Name':<30} {'Database ID':<12}\n"
    divider = "-" * 50 + "\n"
    lines = ["Registered Students:\n", divider, header, divider]
    for student_db_id, student_uid, name, _ in students:
        lines.append(f"{student_uid:<12} {name:<30} {student_db_id:<12}\n")
    return "".join(lines)
