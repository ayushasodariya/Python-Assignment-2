import re
import sys
from collections import defaultdict, deque
from datetime import datetime


# Expected log format: HH:MM username IP FAIL/SUCCESS
LOG_PATTERN = re.compile(
    r"^(\d{2}:\d{2})\s+([A-Za-z0-9_.-]+)\s+"
    r"((?:\d{1,3}\.){3}\d{1,3})\s+(FAIL|SUCCESS)$"
)

IP_PATTERN = re.compile(
    r"^(?:\d{1,3}\.){3}\d{1,3}$"
)


def parse_timestamp(timestamp):
    """Validate a timestamp and convert it to minutes after midnight."""
    try:
        parsed_time = datetime.strptime(timestamp, "%H:%M")
        return parsed_time.hour * 60 + parsed_time.minute
    except ValueError:
        raise ValueError(f"Invalid timestamp: {timestamp}")


def validate_ip_address(ip_address):
    """Check that an IPv4 address has four valid octets."""
    if not IP_PATTERN.fullmatch(ip_address):
        return False

    octets = ip_address.split(".")
    return all(0 <= int(octet) <= 255 for octet in octets)


def parse_log_line(line):
    """Validate and parse one log record."""
    match = LOG_PATTERN.fullmatch(line.strip())

    if not match:
        raise ValueError(f"Invalid log format: {line}")

    timestamp, username, ip_address, status = match.groups()

    if not validate_ip_address(ip_address):
        raise ValueError(f"Invalid IP address: {ip_address}")

    timestamp_minutes = parse_timestamp(timestamp)

    return timestamp_minutes, timestamp, username, ip_address, status


def detect_suspicious_users(threshold, window_minutes, log_records):
    """
    Find the first suspicious success for each user.

    A success is suspicious if at least 'threshold' failed
    attempts occurred during the preceding window and the
    successful login uses a different IP from those failures.
    """
    failed_attempts = defaultdict(deque)
    suspicious_users = {}

    for minute, timestamp, username, ip_address, status in log_records:

        # Keep only failed attempts inside the sliding time window.
        attempts = failed_attempts[username]

        while attempts and minute - attempts[0][0] > window_minutes:
            attempts.popleft()

        if status == "FAIL":
            attempts.append((minute, ip_address))

        elif status == "SUCCESS" and username not in suspicious_users:
            # Check the threshold and whether any failure came
            # from a different IP than this successful login.
            if (
                len(attempts) >= threshold
                and any(
                    failed_ip != ip_address
                    for _, failed_ip in attempts
                )
            ):
                suspicious_users[username] = timestamp

    return suspicious_users


def main():
    """Read input, validate it, and print suspicious users."""
    try:
        first_line = input(
            "Enter X (failed attempts) and T (window minutes): "
        ).strip().split()

        if len(first_line) != 2:
            raise ValueError("Enter exactly two integers: X T.")

        threshold, window_minutes = map(int, first_line)

        if not 1 <= threshold <= 100:
            raise ValueError("X must be between 1 and 100.")

        if not 1 <= window_minutes <= 1440:
            raise ValueError("T must be between 1 and 1440.")

        number_line = input("Enter number of log records: ").strip()
        if not number_line.isdigit():
            raise ValueError("Number of log records must be an integer.")

        number_of_logs = int(number_line)

        if not 1 <= number_of_logs <= 2_000_000:
            raise ValueError("Number of logs must be between 1 and 2000000.")

        log_records = []

        for index in range(number_of_logs):
            line = input(f"Log {index + 1}: ")
            log_records.append(parse_log_line(line))

        # The assignment guarantees logs are timestamp-sorted.
        # Validate that assumption instead of silently changing input order.
        for index in range(1, len(log_records)):
            if log_records[index][0] < log_records[index - 1][0]:
                raise ValueError("Log records must be sorted by timestamp.")

        suspicious_users = detect_suspicious_users(
            threshold, window_minutes, log_records
        )

        # Required output order: lexicographical username order.
        if suspicious_users:
            for username in sorted(suspicious_users):
                print(username, suspicious_users[username])
        else:
            print("No suspicious users found.")

    except ValueError as error:
        print(f"Input error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
