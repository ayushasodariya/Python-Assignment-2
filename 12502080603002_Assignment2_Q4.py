
import json
import getpass
import sys

import mysql.connector
from mysql.connector import Error


# Only these columns can be used in the query.
ALLOWED_COLUMNS = {
    "student.student_id": "s.student_id",
    "student.name": "s.name",
    "student.spi": "s.spi",
    "course.course_id": "c.course_id",
    "course.name": "c.name",
    "registration.student_id": "r.student_id",
    "registration.course_id": "r.course_id",
}

# SQL operators are selected from this whitelist, never from raw SQL input.
ALLOWED_OPERATORS = {
    "=": "=",
    ">": ">",
    "<": "<",
    ">=": ">=",
    "<=": "<=",
    "!=": "!=",
    "LIKE": "LIKE",
}


def validate_query_input(data):
    """Validate selected columns, filters, ordering and row limit."""
    if not isinstance(data, dict):
        raise ValueError("Input must be a JSON object.")

    columns = data.get("columns")
    filters = data.get("filters", [])
    order_by = data.get("order_by", [])
    limit = data.get("limit", 10)

    if not isinstance(columns, list) or not columns:
        raise ValueError("Select at least one column.")

    if any(
        not isinstance(column, str) or column not in ALLOWED_COLUMNS
        for column in columns
    ):
        raise ValueError("One or more selected columns are invalid.")

    if len(set(columns)) != len(columns):
        raise ValueError("Duplicate selected columns are not allowed.")

    if not isinstance(filters, list):
        raise ValueError("Filters must be a list.")

    if not isinstance(order_by, list):
        raise ValueError("order_by must be a list.")

    if type(limit) is not int or not 1 <= limit <= 1000:
        raise ValueError("Limit must be an integer from 1 to 1000.")

    for condition in filters:
        if not isinstance(condition, dict):
            raise ValueError("Each filter must be a JSON object.")

        column = condition.get("column")
        operator = condition.get("operator")
        value = condition.get("value")

        if column not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid filter column: {column}")

        if operator not in ALLOWED_OPERATORS:
            raise ValueError(f"Unsupported operator: {operator}")

        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise ValueError("Filter values must be strings or numbers.")

        if isinstance(value, float):
            import math
            if not math.isfinite(value):
                raise ValueError("Filter values must be finite numbers.")

        if operator == "LIKE" and not isinstance(value, str):
            raise ValueError("LIKE requires a string value.")

    for item in order_by:
        if not isinstance(item, dict):
            raise ValueError("Each order_by entry must be an object.")

        if item.get("column") not in ALLOWED_COLUMNS:
            raise ValueError("Invalid ORDER BY column.")

        if item.get("direction", "ASC").upper() not in ("ASC", "DESC"):
            raise ValueError("Sort direction must be ASC or DESC.")

    return columns, filters, order_by, limit


def build_sql_query(columns, filters, order_by, limit):
    """Build a safe JOIN query and return SQL plus parameters."""
    selected_columns = ", ".join(
        ALLOWED_COLUMNS[column] for column in columns
    )

    query = f"""
        SELECT {selected_columns}
        FROM Student AS s
        INNER JOIN CourseRegistration AS r
            ON s.student_id = r.student_id
        INNER JOIN Course AS c
            ON r.course_id = c.course_id
    """

    parameters = []

    # Filter values are passed separately as parameters.
    if filters:
        conditions = []

        for condition in filters:
            column = ALLOWED_COLUMNS[condition["column"]]
            operator = ALLOWED_OPERATORS[condition["operator"]]

            conditions.append(f"{column} {operator} %s")
            parameters.append(condition["value"])

        query += " WHERE " + " AND ".join(conditions)

    # Column names and directions are taken only from validated options.
    if order_by:
        sort_conditions = []

        for item in order_by:
            column = ALLOWED_COLUMNS[item["column"]]
            direction = item.get("direction", "ASC").upper()
            sort_conditions.append(f"{column} {direction}")

        query += " ORDER BY " + ", ".join(sort_conditions)

    query += " LIMIT %s"
    parameters.append(limit)

    return query, parameters


def execute_query(connection, query, parameters):
    """Execute the query and return its column names and result rows."""
    cursor = connection.cursor()

    try:
        cursor.execute(query, parameters)
        column_names = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        return column_names, rows
    finally:
        cursor.close()


def display_results(column_names, rows):
    """Print query results in a readable table-like format."""
    if not rows:
        print("No matching records found.")
        return

    print("\n" + " | ".join(column_names))
    print("-" * 60)

    for row in rows:
        print(" | ".join(str(value) for value in row))


def main():
    """Read query configuration, validate it and access MySQL."""
    connection = None

    try:
        print("SQL Join Query Builder and Validator")
        print("Enter query configuration as a single JSON object.")

        raw_input = input("Query JSON: ").strip()

        if not raw_input:
            raise ValueError("Query input cannot be empty.")

        data = json.loads(raw_input)
        columns, filters, order_by, limit = validate_query_input(data)

        query, parameters = build_sql_query(
            columns, filters, order_by, limit
        )

        # Display the generated query before connecting to the database.
        print("\nSQL_OK")
        print("\nGenerated SQL template:")
        print(query.strip())
        print("\nParameters:")
        print(parameters)

        host = input("\nMySQL host [localhost]: ").strip() or "localhost"
        username = input("MySQL username: ").strip()
        password = getpass.getpass("MySQL password: ")
        database = input("Existing database name: ").strip()

        if not username or not database:
            raise ValueError("Username and database name are required.")

        connection = mysql.connector.connect(
            host=host,
            user=username,
            password=password,
            database=database
        )

        column_names, rows = execute_query(
            connection, query, parameters
        )
        display_results(column_names, rows)

    except json.JSONDecodeError:
        print("Error: Enter valid JSON.", file=sys.stderr)
    except ValueError as error:
        print(f"Input error: {error}", file=sys.stderr)
    except Error as error:
        print(f"MySQL error: {error}", file=sys.stderr)
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled.")
    finally:
        if connection is not None and connection.is_connected():
            connection.close()
            print("\nMySQL connection closed.")


if __name__ == "__main__":
    main()
