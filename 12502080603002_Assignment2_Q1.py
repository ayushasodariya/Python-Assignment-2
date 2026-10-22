
import re
import sys
from collections import defaultdict


# Matches the username characters and the required domain format.
EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._+-])"
    r"([A-Za-z0-9._+-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*"
    r"\.(?:com|edu|org))"
    r"(?![A-Za-z0-9._+-])",
    re.IGNORECASE
)


def extract_emails(file_path):
    """Read a text file line by line and collect unique valid emails."""
    emails_by_domain = defaultdict(set)

    try:
        # Streaming avoids loading the entire file into memory.
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            for line in file:
                for match in EMAIL_PATTERN.finditer(line):
                    email = match.group(1).lower()

                    # Extract the domain part after '@'.
                    domain = email.rsplit("@", 1)[1]
                    emails_by_domain[domain].add(email)

    except OSError as error:
        print(f"Error reading file: {error}", file=sys.stderr)
        return None

    return emails_by_domain


def display_results(emails_by_domain):
    """Print each domain, its unique email count and smallest email."""
    for domain in sorted(emails_by_domain):
        unique_emails = emails_by_domain[domain]

        if unique_emails:
            smallest_email = min(unique_emails)
            print(f"{domain} {len(unique_emails)} {smallest_email}")


def main():
    """Get the file path, validate it and run the extractor."""
    file_path = input("Enter the text file path: ").strip()

    if not file_path:
        print("Error: File path cannot be empty.")
        return

    emails_by_domain = extract_emails(file_path)

    if emails_by_domain is not None:
        display_results(emails_by_domain)


if __name__ == "__main__":
    main()
