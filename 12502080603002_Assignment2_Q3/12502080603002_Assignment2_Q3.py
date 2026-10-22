
import csv
import getpass
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

import mysql.connector
from mysql.connector import Error


BATCH_SIZE = 1000


def create_tables(connection):
    """Create the required tables and indexes if they do not exist."""
    statements = [
        """
        CREATE TABLE IF NOT EXISTS Student (
            student_id VARCHAR(30) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            spi DECIMAL(4, 2) NOT NULL,
            CHECK (spi >= 0 AND spi <= 10)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS CourseRegistration (
            student_id VARCHAR(30) NOT NULL,
            course_id VARCHAR(30) NOT NULL,
            PRIMARY KEY (student_id, course_id),
            FOREIGN KEY (student_id)
                REFERENCES Student(student_id)
                ON DELETE CASCADE,
            INDEX idx_course_id (course_id)
        )
        """
    ]

    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    finally:
        cursor.close()


def import_students(connection, csv_path):
    """Import student records in batches; skip invalid CSV rows."""
    insert_query = """
        INSERT INTO Student (student_id, name, spi)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            spi = VALUES(spi)
    """

    imported = 0
    skipped = 0
    batch = []
    cursor = connection.cursor()

    try:
        with open(csv_path, "r", encoding="utf-8-sig",
                  newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            required = {"student_id", "name", "spi"}
            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                raise ValueError(
                    "student.csv must contain: student_id,name,spi"
                )

            for row in reader:
                try:
                    student_id = row["student_id"].strip()
                    name = row["name"].strip()
                    spi = Decimal(row["spi"].strip())

                    if (
                        not student_id
                        or len(student_id) > 30
                        or not name
                        or len(name) > 100
                        or not spi.is_finite()
                        or not Decimal("0") <= spi <= Decimal("10")
                    ):
                        skipped += 1
                        continue

                    batch.append((student_id, name, spi))

                    if len(batch) >= BATCH_SIZE:
                        cursor.executemany(insert_query, batch)
                        imported += len(batch)
                        batch.clear()

                except (ValueError, InvalidOperation, TypeError):
                    skipped += 1

            if batch:
                cursor.executemany(insert_query, batch)
                imported += len(batch)

        connection.commit()
        print(f"Student records processed: {imported}")
        print(f"Invalid student rows skipped: {skipped}")

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def import_registrations(connection, csv_path):
    """Import course registrations in batches."""
    insert_query = """
        INSERT IGNORE INTO CourseRegistration (student_id, course_id)
        VALUES (%s, %s)
    """

    imported = 0
    skipped = 0
    batch = []
    cursor = connection.cursor()

    try:
        with open(csv_path, "r", encoding="utf-8-sig",
                  newline="") as csv_file:
            reader = csv.DictReader(csv_file)

            required = {"student_id", "course_id"}
            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                raise ValueError(
                    "registration.csv must contain: student_id,course_id"
                )

            for row in reader:
                student_id = (row.get("student_id") or "").strip()
                course_id = (row.get("course_id") or "").strip()

                if (
                    not student_id
                    or len(student_id) > 30
                    or not course_id
                    or len(course_id) > 30
                ):
                    skipped += 1
                    continue

                batch.append((student_id, course_id))

                if len(batch) >= BATCH_SIZE:
                    cursor.executemany(insert_query, batch)
                    imported += len(batch)
                    batch.clear()

            if batch:
                cursor.executemany(insert_query, batch)
                imported += len(batch)

        connection.commit()
        print(f"Registration records processed: {imported}")
        print(f"Invalid registration rows skipped: {skipped}")

    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def display_course_students(connection, course_id, spi_threshold):
    """Display matching students in the required sorting order."""
    query = """
        SELECT s.student_id, s.name, s.spi, r.course_id
        FROM Student AS s
        INNER JOIN CourseRegistration AS r
            ON s.student_id = r.student_id
        WHERE r.course_id = %s AND s.spi > %s
        ORDER BY s.spi DESC, s.student_id ASC
    """

    cursor = connection.cursor()
    try:
        # Parameterized values help prevent SQL injection.
        cursor.execute(query, (course_id, spi_threshold))
        rows = cursor.fetchall()

        if not rows:
            print("No students found matching the criteria.")
            return

        print("\nStudent ID | Name | SPI | Course ID")
        print("-" * 45)

        for student_id, name, spi, registered_course in rows:
            print(
                f"{student_id} | {name} | "
                f"{spi:.2f} | {registered_course}"
            )
    finally:
        cursor.close()


def main():
    """Collect inputs, connect to MySQL and run the analytics."""
    connection = None

    try:
        student_file = input("Student CSV path: ").strip()
        registration_file = input("Registration CSV path: ").strip()

        if not student_file or not Path(student_file).is_file():
            print("Error: Student CSV file does not exist.")
            return

        if not registration_file or not Path(registration_file).is_file():
            print("Error: Registration CSV file does not exist.")
            return

        course_id = input("Enter course ID: ").strip()
        if not course_id or len(course_id) > 30:
            print("Error: Course ID must contain 1-30 characters.")
            return

        try:
            threshold = Decimal(input("Enter SPI threshold (0-10): ").strip())
            if not threshold.is_finite() or not (
                Decimal("0") <= threshold <= Decimal("10")
            ):
                print("Error: SPI threshold must be between 0 and 10.")
                return
        except InvalidOperation:
            print("Error: Enter a valid numeric SPI threshold.")
            return

        # Enter credentials at runtime rather than storing passwords in code.
        host = input("MySQL host [localhost]: ").strip() or "localhost"
        username = input("MySQL username: ").strip()
        password = getpass.getpass("MySQL password: ")
        database = input("Existing database name: ").strip()

        if not username or not database:
            print("Error: Username and database name are required.")
            return

        connection = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )

        if not connection.is_connected():
            print("Could not connect to MySQL.")
            return

        print("\nConnected to MySQL successfully.")
        create_tables(connection)

        import_students(connection, student_file)
        import_registrations(connection, registration_file)

        display_course_students(connection, course_id, threshold)

    except (Error, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled.")
    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("MySQL connection closed.")


if __name__ == "__main__":
    main()
