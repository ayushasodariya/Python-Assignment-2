
import re
import sys
from html.parser import HTMLParser
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ProductHTMLParser(HTMLParser):
    """Extract products from HTML elements with product data attributes."""

    def __init__(self):
        super().__init__()
        self.products = []

    def handle_starttag(self, tag, attrs):
        # Convert attributes into a dictionary for easy lookup.
        attributes = dict(attrs)

        name = attributes.get("data-name")
        price = attributes.get("data-price")
        rating = attributes.get("data-rating")

        if name and price is not None and rating is not None:
            try:
                # Accept prices such as ₹499, $499.50 or 1,299.
                clean_price = re.sub(r"[^\d.]", "", price.replace(",", ""))
                numeric_price = Decimal(clean_price)
                numeric_rating = Decimal(rating)

                # Reject invalid or negative prices and out-of-range ratings.
                if (
                    not numeric_price.is_finite()
                    or not numeric_rating.is_finite()
                    or numeric_price < 0
                    or not Decimal("0") <= numeric_rating <= Decimal("5")
                ):
                    return

                self.products.append({
                    "name": name.strip(),
                    "price": numeric_price,
                    "rating": numeric_rating
                })

            except (InvalidOperation, ValueError):
                # Ignore product entries with invalid numeric values.
                return


def read_products(file_path):
    """Read an HTML file in chunks and extract its product records."""
    parser = ProductHTMLParser()

    try:
        with open(file_path, "r", encoding="utf-8",
                  errors="replace") as html_file:
            while True:
                chunk = html_file.read(65536)
                if not chunk:
                    break
                parser.feed(chunk)

        parser.close()
        return parser.products

    except OSError as error:
        print(f"Error reading '{file_path}': {error}", file=sys.stderr)
        return None


def select_unique_products(products):
    """Keep one best-ranked record for each product name."""
    unique_products = {}

    for product in products:
        name = product["name"]

        if not name:
            continue

        current = unique_products.get(name)

        # For duplicate names, retain the better-ranked entry.
        if current is None or (
            -product["rating"], product["price"], name
        ) < (
            -current["rating"], current["price"], name
        ):
            unique_products[name] = product

    return list(unique_products.values())


def rank_products(products, limit):
    """Sort products by rating, price and name, then select top K."""
    products.sort(
        key=lambda product: (
            -product["rating"],
            product["price"],
            product["name"].casefold()
        )
    )
    return products[:limit]


def format_number(number):
    """Print whole numbers without unnecessary decimal places."""
    if number == number.to_integral_value():
        return str(int(number))
    return format(number, "f")


def main():
    """Validate input, read pages and display the top K products."""
    try:
        first_line = input("Enter number of HTML files (p) and top K: ")
        values = first_line.split()

        if len(values) != 2:
            print("Error: Enter exactly two integers: p k.")
            return

        page_count, top_k = map(int, values)

        if not 1 <= page_count <= 5000:
            print("Error: p must be between 1 and 5000.")
            return

        if not 1 <= top_k <= 1000:
            print("Error: K must be between 1 and 1000.")
            return

        file_paths = []
        for index in range(page_count):
            path = input(f"Enter HTML file path {index + 1}: ").strip()

            if not path:
                print("Error: File path cannot be empty.")
                return

            if not Path(path).is_file():
                print(f"Error: File not found: {path}")
                return

            file_paths.append(path)

        all_products = []

        for file_path in file_paths:
            products = read_products(file_path)

            if products is None:
                return

            all_products.extend(products)

        unique_products = select_unique_products(all_products)
        top_products = rank_products(unique_products, top_k)

        if not top_products:
            print("No valid products found.")
            return

        for product in top_products:
            print(
                f"{product['name']} "
                f"{format_number(product['price'])} "
                f"{format_number(product['rating'])}"
            )

    except ValueError:
        print("Error: Please enter valid integer values.")
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.")


if __name__ == "__main__":
    main()
