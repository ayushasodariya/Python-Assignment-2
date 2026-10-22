import csv
import math
import os
import sys
from collections import Counter

import matplotlib
matplotlib.use("Agg")  # Save charts without requiring a display.
import matplotlib.pyplot as plt


MIN_MARKS = 0
MAX_MARKS = 100
MAX_SUBJECTS = 20


def read_marks_csv(file_path):
    """Read the CSV file and validate its required columns."""
    with open(file_path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames:
            raise ValueError("The CSV file is empty or has no header.")

        # Remove accidental spaces from column names.
        reader.fieldnames = [name.strip() for name in reader.fieldnames]

        required_columns = {"enrollment", "name"}
        if not required_columns.issubset(reader.fieldnames):
            raise ValueError(
                "CSV must contain 'enrollment' and 'name' columns."
            )

        subject_columns = [
            column for column in reader.fieldnames
            if column not in required_columns
        ]

        if not subject_columns:
            raise ValueError("At least one subject column is required.")

        if len(subject_columns) > MAX_SUBJECTS:
            raise ValueError("A maximum of 20 subjects is allowed.")

        students = []
        seen_enrollments = set()

        for row_number, row in enumerate(reader, start=2):
            enrollment = (row.get("enrollment") or "").strip()
            name = (row.get("name") or "").strip()

            if not enrollment or not name:
                raise ValueError(
                    f"Row {row_number}: enrollment and name are required."
                )

            if enrollment in seen_enrollments:
                raise ValueError(
                    f"Row {row_number}: duplicate enrollment {enrollment}."
                )

            seen_enrollments.add(enrollment)

            cleaned_row = {
                "enrollment": enrollment,
                "name": name,
            }

            for subject in subject_columns:
                raw_mark = (row.get(subject) or "").strip()

                # Missing marks are handled later using the subject average.
                if raw_mark == "":
                    cleaned_row[subject] = None
                    continue

                try:
                    mark = float(raw_mark)
                except ValueError:
                    raise ValueError(
                        f"Row {row_number}: invalid mark for {subject}."
                    )

                if not math.isfinite(mark):
                    raise ValueError(
                        f"Row {row_number}: mark must be finite."
                    )

                if not MIN_MARKS <= mark <= MAX_MARKS:
                    raise ValueError(
                        f"Row {row_number}: marks must be between 0 and 100."
                    )

                cleaned_row[subject] = mark

            students.append(cleaned_row)

        if not students:
            raise ValueError("The CSV contains no student records.")

        return students, subject_columns


def calculate_subject_averages(students, subjects):
    """Calculate each subject's mean using its available marks."""
    averages = {}

    for subject in subjects:
        valid_marks = [
            student[subject]
            for student in students
            if student[subject] is not None
        ]

        # If an entire subject is missing, use 0 as a documented fallback.
        averages[subject] = (
            sum(valid_marks) / len(valid_marks) if valid_marks else 0.0
        )

    return averages


def clean_missing_marks(students, subjects, averages):
    """Replace missing marks with the corresponding subject average."""
    cleaned_students = []

    for student in students:
        cleaned_row = student.copy()

        for subject in subjects:
            if cleaned_row[subject] is None:
                cleaned_row[subject] = round(averages[subject], 2)

        cleaned_students.append(cleaned_row)

    return cleaned_students


def get_grade(mark):
    """Assign a grade using the chosen percentage bands."""
    if mark >= 90:
        return "A+"
    if mark >= 80:
        return "A"
    if mark >= 70:
        return "B"
    if mark >= 60:
        return "C"
    if mark >= 50:
        return "D"
    return "F"


def export_cleaned_csv(students, subjects, output_folder):
    """Export student records with missing marks filled."""
    output_path = os.path.join(output_folder, "cleaned_marks.csv")
    columns = ["enrollment", "name"] + subjects

    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()

        for student in students:
            row = student.copy()

            for subject in subjects:
                row[subject] = f"{row[subject]:.2f}"

            writer.writerow(row)

    return output_path


def export_summary_csv(students, subjects, output_folder):
    """Export count, minimum, maximum and average for each subject."""
    summary_path = os.path.join(output_folder, "summary.csv")

    with open(summary_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            ["Subject", "Count", "Minimum", "Maximum", "Average"]
        )

        for subject in subjects:
            marks = [student[subject] for student in students]

            writer.writerow([
                subject,
                len(marks),
                f"{min(marks):.2f}",
                f"{max(marks):.2f}",
                f"{sum(marks) / len(marks):.2f}",
            ])

    return summary_path


def export_grade_distribution(students, subjects, output_folder):
    """Create a bar chart showing the distribution of grades."""
    grade_counts = Counter()

    for student in students:
        for subject in subjects:
            grade_counts[get_grade(student[subject])] += 1

    grade_order = ["A+", "A", "B", "C", "D", "F"]
    counts = [grade_counts[grade] for grade in grade_order]

    plt.figure(figsize=(8, 5))
    plt.bar(grade_order, counts)
    plt.title("Student Grade Distribution")
    plt.xlabel("Grade")
    plt.ylabel("Number of Marks")
    plt.tight_layout()

    output_path = os.path.join(output_folder, "grade_distribution.png")
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def export_subject_average_chart(students, subjects, output_folder):
    """Create a chart comparing average marks across subjects."""
    subject_averages = [
        sum(student[subject] for student in students) / len(students)
        for subject in subjects
    ]

    plt.figure(figsize=(9, 5))
    plt.bar(subjects, subject_averages)
    plt.title("Subject-wise Average Marks")
    plt.xlabel("Subject")
    plt.ylabel("Average Marks")
    plt.ylim(0, 100)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()

    output_path = os.path.join(output_folder, "subject_average.png")
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def export_top_performers_chart(students, subjects, output_folder):
    """Create a chart of the five highest-scoring students."""
    # The overall score is the average across all subjects.
    performers = []

    for student in students:
        average = sum(student[s] for s in subjects) / len(subjects)
        performers.append((student["name"], average, student["enrollment"]))

    # Enrollment number provides a consistent tie-breaker.
    performers.sort(key=lambda item: (-item[1], item[2]))
    top_performers = performers[:5]

    names = [
        f"{name} ({enrollment})"
        for name, _, enrollment in top_performers
    ]
    averages = [average for _, average, _ in top_performers]

    plt.figure(figsize=(9, 5))
    plt.barh(names[::-1], averages[::-1])
    plt.title("Top 5 Student Performers")
    plt.xlabel("Average Marks")
    plt.xlim(0, 100)
    plt.tight_layout()

    output_path = os.path.join(output_folder, "top_performers.png")
    plt.savefig(output_path, dpi=150)
    plt.close()

    return output_path


def main():
    """Coordinate CSV processing, cleaning, statistics and chart exports."""
    file_path = input("Enter the path of the marks CSV file: ").strip()
    output_folder = input("Enter the output folder path: ").strip()

    if not file_path:
        print("Input error: CSV path cannot be empty.", file=sys.stderr)
        return

    if not output_folder:
        print("Input error: Output folder cannot be empty.", file=sys.stderr)
        return

    if not os.path.isfile(file_path):
        print("Input error: CSV file does not exist.", file=sys.stderr)
        return

    try:
        os.makedirs(output_folder, exist_ok=True)

        if not os.path.isdir(output_folder):
            raise ValueError("Output path is not a directory.")

        students, subjects = read_marks_csv(file_path)

        # Compute means before replacing missing marks.
        averages = calculate_subject_averages(students, subjects)
        cleaned_students = clean_missing_marks(
            students, subjects, averages
        )

        generated_files = [
            export_cleaned_csv(cleaned_students, subjects, output_folder),
            export_summary_csv(cleaned_students, subjects, output_folder),
            export_grade_distribution(
                cleaned_students, subjects, output_folder
            ),
            export_subject_average_chart(
                cleaned_students, subjects, output_folder
            ),
            export_top_performers_chart(
                cleaned_students, subjects, output_folder
            ),
        ]

        print("\nDashboard files generated successfully:")
        for output_path in generated_files:
            print(output_path)

    except (ValueError, OSError, csv.Error) as error:
        print(f"Processing error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
