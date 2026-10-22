import sys

MOD = 1_000_000_007
MIN_SCORE = -1_000_000
MAX_SCORE = 1_000_000


def parse_matrix_input():
    """Read and validate the matrix dimensions and cell values."""
    first_line = input("Enter number of rows and columns (n m): ").split()

    if len(first_line) != 2:
        raise ValueError("Enter exactly two integers: n m.")

    try:
        rows, columns = map(int, first_line)
    except ValueError:
        raise ValueError("Rows and columns must be integers.")

    if not (1 <= rows <= 2000 and 1 <= columns <= 2000):
        raise ValueError("Rows and columns must be between 1 and 2000.")

    matrix = []

    for row_index in range(rows):
        values = input(
            f"Enter row {row_index + 1} ({columns} values): "
        ).split()

        if len(values) != columns:
            raise ValueError(
                f"Row {row_index + 1} must contain exactly "
                f"{columns} values."
            )

        validated_row = []

        for value in values:
            if value.upper() == "X":
                validated_row.append(None)
            else:
                try:
                    score = int(value)
                except ValueError:
                    raise ValueError(
                        f"Invalid cell value: {value}. "
                        "Use an integer or X."
                    )

                if not MIN_SCORE <= score <= MAX_SCORE:
                    raise ValueError(
                        f"Cell scores must be between "
                        f"{MIN_SCORE} and {MAX_SCORE}."
                    )

                validated_row.append(score)

        matrix.append(validated_row)

    return rows, columns, matrix


def find_maximum_score_path(rows, columns, matrix):
    """
    Return (maximum score, number of maximum-score paths).

    Only the previous DP row and current DP row are stored.
    A None score means the cell cannot be reached.
    """
    # Each DP entry contains (best score, number of best paths).
    previous_row = [(None, 0)] * columns

    for row_index in range(rows):
        current_row = [(None, 0)] * columns

        for column_index in range(columns):
            cell_score = matrix[row_index][column_index]

            # Blocked cells cannot be part of any valid path.
            if cell_score is None:
                continue

            # The starting cell has exactly one path: itself.
            if row_index == 0 and column_index == 0:
                current_row[column_index] = (cell_score, 1)
                continue

            predecessors = []

            # From the left: move right into the current cell.
            if column_index > 0:
                predecessors.append(current_row[column_index - 1])

            # From above: move down into the current cell.
            if row_index > 0:
                predecessors.append(previous_row[column_index])

            # From the upper-left: move diagonally down-right.
            if row_index > 0 and column_index > 0:
                predecessors.append(previous_row[column_index - 1])

            reachable = [
                (score, count)
                for score, count in predecessors
                if score is not None
            ]

            if not reachable:
                continue

            # Find the best predecessor score.
            best_predecessor_score = max(
                score for score, _ in reachable
            )

            # Count every best path that reaches this cell.
            number_of_best_paths = sum(
                count
                for score, count in reachable
                if score == best_predecessor_score
            ) % MOD

            current_row[column_index] = (
                best_predecessor_score + cell_score,
                number_of_best_paths
            )

        previous_row = current_row

    # The bottom-right cell contains the final answer.
    maximum_score, path_count = previous_row[-1]

    if maximum_score is None:
        return None

    return maximum_score, path_count


def main():
    """Run the program and display the requested result."""
    try:
        rows, columns, matrix = parse_matrix_input()

        result = find_maximum_score_path(rows, columns, matrix)

        if result is None:
            print("IMPOSSIBLE")
        else:
            maximum_score, path_count = result
            print(maximum_score, path_count)

    except (ValueError, EOFError) as error:
        print(f"Input error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
