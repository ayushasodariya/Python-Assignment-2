import json
import math
import os
import sys
from collections import defaultdict


def read_json_lines(file_path):
    """Yield one line at a time to keep memory usage low."""
    with open(file_path, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            # Skip blank lines instead of treating them as sensor records.
            if line.strip():
                yield line_number, line


def parse_sensor_records(file_path):
    """
    Parse each JSON line and yield (device_id, temperature, is_corrupted).

    If the device ID is available but another field is invalid, the
    corrupted record can still be counted against that device.
    """
    for line_number, line in read_json_lines(file_path):
        device_id = None

        try:
            record = json.loads(line)

            if not isinstance(record, dict):
                raise ValueError("Record must be a JSON object")

            raw_device_id = record.get("device_id")

            if isinstance(raw_device_id, str) and raw_device_id.strip():
                device_id = raw_device_id.strip()

            if device_id is None:
                raise ValueError("Missing or invalid device_id")

            # temperature_c must be numeric, finite and not a Boolean.
            raw_temperature = record.get("temperature_c")

            if isinstance(raw_temperature, bool):
                raise ValueError("Temperature cannot be Boolean")

            if not isinstance(raw_temperature, (int, float)):
                raise ValueError("Temperature must be numeric")

            temperature = float(raw_temperature)

            if not math.isfinite(temperature):
                raise ValueError("Temperature must be finite")

            # Humidity is required by the assignment's sensor record format.
            raw_humidity = record.get("humidity")

            if isinstance(raw_humidity, bool) or not isinstance(
                raw_humidity, (int, float)
            ):
                raise ValueError("Humidity must be numeric")

            humidity = float(raw_humidity)

            if not math.isfinite(humidity) or not 0 <= humidity <= 100:
                raise ValueError("Humidity must be between 0 and 100")

            # The assignment's sample reports temperature_c as Celsius,
            # so the pipeline retains that unit.
            yield device_id, temperature, False

        except (json.JSONDecodeError, ValueError, TypeError):
            # None means the record could not be assigned to a device.
            yield device_id, None, True


def process_sensor_file(file_path):
    """Aggregate readings by device while processing the file as a stream."""
    device_statistics = defaultdict(
        lambda: {
            "count": 0,
            "min": None,
            "max": None,
            "total": 0.0,
            "corrupted": 0,
        }
    )

    unassigned_corrupted = 0

    # This loop consumes the generator; the complete file is never stored.
    for device_id, temperature, is_corrupted in parse_sensor_records(file_path):
        if is_corrupted:
            if device_id is None:
                unassigned_corrupted += 1
            else:
                device_statistics[device_id]["corrupted"] += 1
            continue

        stats = device_statistics[device_id]
        stats["count"] += 1
        stats["total"] += temperature

        if stats["min"] is None or temperature < stats["min"]:
            stats["min"] = temperature

        if stats["max"] is None or temperature > stats["max"]:
            stats["max"] = temperature

    return device_statistics, unassigned_corrupted


def display_summary(device_statistics, unassigned_corrupted):
    """Print summary statistics in device ID order."""
    if not device_statistics:
        print("No records with a valid device ID were found.")

    for device_id in sorted(device_statistics):
        stats = device_statistics[device_id]
        count = stats["count"]

        if count:
            average = stats["total"] / count
            print(
                f"{device_id} count={count} "
                f"min={stats['min']:g} "
                f"max={stats['max']:g} "
                f"avg={average:.2f} "
                f"corrupted={stats['corrupted']}"
            )
        else:
            print(
                f"{device_id} count=0 min=N/A max=N/A "
                f"avg=N/A corrupted={stats['corrupted']}"
            )

    if unassigned_corrupted:
        print(
            "Unassigned corrupted records="
            f"{unassigned_corrupted}"
        )


def main():
    """Validate the file path and run the ETL pipeline."""
    file_path = input("Enter the path of the JSONL file: ").strip()

    if not file_path:
        print("Input error: File path cannot be empty.", file=sys.stderr)
        return

    if not os.path.isfile(file_path):
        print("Input error: File does not exist.", file=sys.stderr)
        return

    try:
        process_results, unassigned_corrupted = process_sensor_file(file_path)
        display_summary(process_results, unassigned_corrupted)

    except (OSError, UnicodeError) as error:
        print(f"File error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
