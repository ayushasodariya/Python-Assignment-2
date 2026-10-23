# 🐍 Python Assignment 2

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-Connector-4479A1?logo=mysql&logoColor=white)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-informational)
![Status](https://img.shields.io/badge/Status-Completed-brightgreen)

A collection of 10 Python programs for the course **Programming with Python (202044504)**. The problems cover regular expressions, web scraping, MySQL programming, a Tkinter GUI, sliding-window log analysis, generators, dynamic programming, object-oriented design, and data visualization.

| | |
|---|---|
| **Author** | Ayush Asodariya ([@ayushasodariya](https://github.com/ayushasodariya)) |
| **Enrollment No.** | 12502080603002 |
| **Course** | Programming with Python (202044504), Assignment 2 |
| **Program** | B.Tech Information Technology, Semester V |
| **Institute** | A.D. Patel Institute of Technology, CVM University |

---

## 📑 Table of Contents

- [Project Structure](#-project-structure)
- [Problem Summary](#-problem-summary)
- [Getting Started](#-getting-started)
- [Detailed Program Guide](#-detailed-program-guide)
- [Key Concepts Demonstrated](#-key-concepts-demonstrated)
- [Author](#-author)

---

## 📂 Project Structure

```text
Python-Assignment-2/
├── 12502080603002_Assignment2_Q1.py     # Email extractor (regex)
├── 12502080603002_Assignment2_Q2/       # Offline web scraping ranker
├── 12502080603002_Assignment2_Q3/       # MySQL student-course analytics
├── 12502080603002_Assignment2_Q4.py     # SQL join query builder
├── 12502080603002_Assignment2_Q5.py     # Contact Manager (Tkinter + MySQL)
├── 12502080603002_Assignment2_Q6.py     # Suspicious login detector
├── 12502080603002_Assignment2_Q7/       # Generator-based JSON ETL pipeline
├── 12502080603002_Assignment2_Q8.py     # Max-score path in a grid
├── 12502080603002_Assignment2_Q9/       # OOP inventory merger
├── 12502080603002_Assignment2_Q10/      # Data visualization dashboard exporter
├── .gitignore
└── README.md
```

---

## 🧩 Problem Summary

| Q. No. | Topic | Key Technique | Location |
|:------:|-------|---------------|----------|
| 1 | Extract and group email addresses from a text file | Regex, `defaultdict`, file streaming | `Q1.py` |
| 2 | Rank products scraped from saved HTML pages | HTML parsing / regex, sorting, de-duplication | `Q2/` |
| 3 | Student-course analytics on MySQL | CSV loading, parameterized queries, exception handling | `Q3/` |
| 4 | Safe SQL JOIN query builder with validation | Whitelisting, parameterized queries, MySQL | `Q4.py` |
| 5 | Contact Manager desktop application | Tkinter GUI, MySQL CRUD, input validation | `Q5.py` |
| 6 | Detect suspicious logins from server logs | Sliding window, `deque` | `Q6.py` |
| 7 | ETL pipeline for large JSON-lines sensor data | Generators, JSON, aggregation | `Q7/` |
| 8 | Maximum-score path and path count in a grid | Dynamic programming, modulo arithmetic | `Q8.py` |
| 9 | Inventory manager with merge support | OOP, operator overloading, dictionaries | `Q9/` |
| 10 | Student marks dashboard with charts | CSV cleaning, statistics, data visualization | `Q10/` |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10 or newer**
- **MySQL Server** (Q3, Q4, Q5)
- **mysql-connector-python** (Q3, Q4, Q5)
- **matplotlib** and **pandas** (Q10, only if used in your solution; see the note in the Q10 section)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ayushasodariya/Python-Assignment-2.git

# 2. Move into the project folder
cd Python-Assignment-2

# 3. (Optional) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# 4. Install the required packages
pip install mysql-connector-python
pip install matplotlib pandas   # only needed for Q10
```

### Running a program

Single-file questions run directly with Python:

```bash
python 12502080603002_Assignment2_Q1.py
```

For folder-based questions (Q2, Q3, Q7, Q9, Q10), open the folder and run its main script:

```bash
cd 12502080603002_Assignment2_Q2
python <main_script_name>.py
```

---

## 📖 Detailed Program Guide

### Q1: Email Extractor

Reads a text file line by line and finds every valid email address ending in `.com`, `.edu`, or `.org`. Emails are grouped by domain and de-duplicated, ignoring upper/lower case. Malformed addresses such as `root@@bad.com` are ignored.

**Output format (one line per domain, sorted A to Z):**
`domain  unique_email_count  smallest_email`

**Example**

Input file contents:
```text
Contact a.b+1@adit.edu, root@@bad.com, test-user@x.org and a.b+1@adit.edu
```

Output:
```text
adit.edu 1 a.b+1@adit.edu
x.org 1 test-user@x.org
```

---

### Q2: Offline Web Scraping Ranker

Reads several saved HTML pages of product listings and extracts each product's **name, price, and rating**. Duplicate products (by name) are removed, prices are normalized, and the top **K** products are printed.

**Ranking rule:** highest rating first. Ties are broken by lower price, then by product name in alphabetical order.

**Input:** `p k` on the first line, followed by `p` HTML file paths.

**Example**
```text
2 2
page1.html
page2.html
```
Output:
```text
Python Book 499 4.8
USB Keyboard 799 4.7
```

---

### Q3: MySQL Student-Course Analytics

Connects to MySQL, creates the `Student` and `CourseRegistration` tables if they do not exist, loads records from CSV files, and lists the students registered for a given course whose SPI is above a threshold. All queries are **parameterized** and database errors are handled.

**Input:** database credentials, `student.csv`, `registration.csv`, a course id, and an SPI threshold.

**Output:** student id, name, SPI, and course id, sorted by SPI (highest first) and then by student id.

**Example** (`course_id = PY101`, `spi_threshold = 8.0`)
```text
2201 Asha 9.1 PY101
2207 Dev 8.4 PY101
```

---

### Q4: SQL Join Query Builder and Validator

Takes a JSON description of a query, validates it, and builds a safe `SELECT ... JOIN` statement across three tables: `Student`, `CourseRegistration`, and `Course`. It then optionally runs the query on a MySQL database.

**Security features**
- Columns and operators are checked against fixed **whitelists**, so users can never inject raw SQL.
- Filter values are sent as **parameters** (`%s`), not pasted into the SQL text.
- The row limit must be an integer from 1 to 1000.

**Supported options:** `columns`, `filters` (`=`, `>`, `<`, `>=`, `<=`, `!=`, `LIKE`), `order_by`, `limit`.

**Example input**
```json
{"columns": ["student.name", "course.name"],
 "filters": [{"column": "student.spi", "operator": ">", "value": 8}],
 "order_by": [{"column": "student.name", "direction": "ASC"}],
 "limit": 5}
```

The program prints `SQL_OK`, the generated SQL template, and its parameters. It then asks for MySQL connection details before running the query.

---

### Q5: Contact Manager (Tkinter + MySQL)

A desktop application to store and manage contacts, with full **Create, Read, Update, Delete** support.

**Features**
- Add, update, and delete contacts (with a delete confirmation).
- Search by **name, email, or phone**.
- Sort the list **A to Z** or **Z to A**.
- Input validation for name, email format (regex), phone digits (7 to 15), and category.
- Duplicate emails are rejected.
- The database and `Contact(id, name, email, phone, category, notes)` table are created automatically on first run.

**Before running**, open `12502080603002_Assignment2_Q5.py` and set your own MySQL details:

```python
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "YOUR_PASSWORD"   # Replace with your MySQL password
DB_NAME = "contact_manager_db"
```

> ⚠️ Never commit your real password to GitHub.

---

### Q6: Suspicious Login Detector

Scans a list of login attempts and flags users who have at least **X failed logins within T minutes**, followed by a **successful login from a different IP address**.

**Input**
1. `X T`: the number of failed attempts (X) inside a time window of T minutes.
2. The number of log records.
3. The log lines, in `HH:MM username IP FAIL/SUCCESS` format. They must be sorted by time.

**Output:** each suspicious user and the time of their first suspicious success, in alphabetical order. If nobody is suspicious, it prints `No suspicious users found.`

**Example**
```text
Enter X (failed attempts) and T (window minutes): 3 10
Enter number of log records: 5
Log 1: 00:00 u1 1.1.1.1 FAIL
Log 2: 00:03 u1 1.1.1.1 FAIL
Log 3: 00:05 u1 1.1.1.1 FAIL
Log 4: 00:07 u1 2.2.2.2 SUCCESS
Log 5: 00:08 u2 3.3.3.3 SUCCESS
```
Output:
```text
u1 00:07
```
`u1` had 3 failures within 10 minutes, then a success from a new IP. `u2` had no failures, so it is not flagged.

---

### Q7: Generator-Based JSON ETL Pipeline

An ETL (Extract, Transform, Load) pipeline built from **generator functions**. It reads a very large JSON-lines file of sensor records one line at a time, so the whole file is never loaded into memory. Corrupted records (missing fields or non-numeric values) are skipped and counted.

**Input:** path of the JSONL file. Each line has `device_id`, `timestamp`, `temperature_c`, and `humidity`.

**Output:** for each device, the record count, minimum, maximum, and average temperature, and the number of corrupted records.

**Example**
```text
{"device_id":"D1","temperature_c":30,"humidity":50}
{"device_id":"D1","temperature_c":"bad","humidity":45}
```
Output:
```text
D1 count=1 min=30 max=30 avg=30.00 corrupted=1
```
The second record is corrupted because its temperature is not a number.

---

### Q8: Maximum Score Path in a Grid

Given an `n × m` grid, find the path from the top-left to the bottom-right cell with the **highest total score**, and count how many paths reach that score.

**Rules**
- Allowed moves: **right**, **down**, and **diagonal (down-right)**.
- Cells marked `X` are blocked.
- The number of best paths is reported **modulo 1,000,000,007**.
- If no path exists, the program prints `IMPOSSIBLE`.

**Example**
```text
Enter number of rows and columns (n m): 3 3
Enter row 1 (3 values): 1 2 3
Enter row 2 (3 values): 4 X 6
Enter row 3 (3 values): 7 8 9
```
Output:
```text
29 1
```
The best path is 1 → 4 → 7 → 8 → 9 (total 29), and it is the only path with that score.

**Efficiency:** only two rows of the DP table are stored at a time, so memory use stays small even for 2000 × 2000 grids.

---

### Q9: OOP Inventory Merger

Uses `Product` and `Inventory` classes to manage stock. An inventory supports adding, deleting, and updating products, comparing two inventories by **total value**, and **merging** two inventories using **operator overloading**.

**Merge rule:** when the same product id appears in both inventories, the stock quantities are added, the **lower purchase price** is kept, and the **higher selling price** is kept.

**Operations:** `ADD`, `DELETE`, `UPDATE`, `MERGE`, `COMPARE`.

**Example**
```text
Inventory A: P1 Pen 10 5 8
Inventory B: P1 Pen 7 4 9
Operation: MERGE
```
Output:
```text
P1 Pen stock=17 purchase=4 selling=9
```

---

### Q10: Data Visualization Dashboard Exporter

Reads a CSV file of student marks, cleans missing values, calculates **subject-wise statistics**, and exports charts as image files.

**Input:** path of the marks CSV (`enrollment, name, Python, DBMS, OS, ...`) and an output folder.

**Output files**
| File | Description |
|------|-------------|
| `cleaned_marks.csv` | Marks data after cleaning |
| `summary.csv` | Subject-wise statistics |
| `grade_distribution.png` | Chart of how grades are spread |
| `subject_average.png` | Average marks per subject |
| `top_performers.png` | Chart of the top students |

> 📝 Note: add which libraries your solution uses (for example `pandas` and `matplotlib`) and remove any you did not use from the Prerequisites list.

---

## 💡 Key Concepts Demonstrated

- Regular expressions and text processing
- Web scraping and data cleaning
- Efficient file reading (streaming line by line, generators)
- Dictionaries, sets, `defaultdict`, and `deque`
- Sliding-window technique
- Dynamic programming with space optimization
- Object-oriented design and operator overloading
- SQL injection prevention (whitelists and parameterized queries)
- Database programming with `mysql-connector-python`
- GUI development with Tkinter
- Data analysis and visualization
- Input validation and error handling

---

## 👤 Author

**Ayush Asodariya**
- GitHub: [@ayushasodariya](https://github.com/ayushasodariya)
- Enrollment No.: 12502080603002
