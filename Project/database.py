
import sqlite3

def create_connection():
    """ create a database connection to the SQLite database
        specified by db_file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect('attendance.db')
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

def create_table(conn):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :return:
    """
    try:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                encoding BLOB NOT NULL
            );
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id)
            );
        ''')
    except sqlite3.Error as e:
        print(e)

def add_student(conn, name, encoding):
    """
    Add a new student into the students table
    :param conn:
    :param name:
    :param encoding:
    :return: project id
    """
    sql = ''' INSERT INTO students(name,encoding)
              VALUES(?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (name, encoding))
    conn.commit()
    return cur.lastrowid

def add_attendance(conn, student_id, class_name, timestamp):
    """
    Add a new attendance record
    :param conn:
    :param student_id:
    :param class_name:
    :param timestamp:
    :return:
    """
    sql = ''' INSERT INTO attendance(student_id,class_name,timestamp)
              VALUES(?,?,?)
          '''
    cur = conn.cursor()
    cur.execute(sql, (student_id, class_name, timestamp))
    conn.commit()
    return cur.lastrowid

def get_attendance_by_class(conn, class_name):
    """
    Query attendance by class name
    :param conn:
    :param class_name:
    :return:
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT s.name, a.class_name, a.timestamp
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.class_name = ?
    """, (class_name,))

    rows = cur.fetchall()
    return rows

def get_all_students(conn):
    """
    Query all rows in the students table
    :param conn: the Connection object
    :return:
    """
    cur = conn.cursor()
    cur.execute("SELECT * FROM students")

    rows = cur.fetchall()

    return rows