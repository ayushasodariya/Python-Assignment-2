import json
import os
import sys
from dataclasses import dataclass


MAX_INT64 = 9_223_372_036_854_775_807


def validate_non_negative_integer(value, field_name):
    """Validate stock as a non-negative integer within 64-bit range."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer.")

    if not 0 <= value <= MAX_INT64:
        raise ValueError(
            f"{field_name} must be between 0 and {MAX_INT64}."
        )

    return value


def validate_price(value, field_name):
    """Validate a price as a finite, non-negative number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field_name} must be numeric.")

    # Prices are kept as integers or floats as supplied in the JSON file.
    if value < 0 or value != value or value == float("inf"):
        raise ValueError(f"{field_name} must be finite and non-negative.")

    if value == float("-inf"):
        raise ValueError(f"{field_name} must be finite and non-negative.")

    return value


@dataclass
class Product:
    """Represent one product stored in an inventory."""

    product_id: str
    name: str
    stock: int
    purchase_price: float
    selling_price: float

    def __post_init__(self):
        self.product_id = str(self.product_id).strip()
        self.name = str(self.name).strip()

        if not self.product_id:
            raise ValueError("Product ID cannot be empty.")

        if len(self.product_id) > 100:
            raise ValueError("Product ID cannot exceed 100 characters.")

        if not self.name:
            raise ValueError("Product name cannot be empty.")

        if len(self.name) > 200:
            raise ValueError("Product name cannot exceed 200 characters.")

        self.stock = validate_non_negative_integer(self.stock, "Stock")
        self.purchase_price = validate_price(
            self.purchase_price, "Purchase price"
        )
        self.selling_price = validate_price(
            self.selling_price, "Selling price"
        )

    def to_dict(self):
        """Convert the product to a JSON-compatible dictionary."""
        return {
            "product_id": self.product_id,
            "name": self.name,
            "stock": self.stock,
            "purchase_price": self.purchase_price,
            "selling_price": self.selling_price,
        }


class Inventory:
    """Manage products using product ID as the dictionary key."""

    def __init__(self, products=None):
        self.products = {}

        if products:
            for product in products:
                self.add_product(product)

    def add_product(self, product):
        """Add a product only when its ID does not already exist."""
        if not isinstance(product, Product):
            raise ValueError("Expected a Product object.")

        if product.product_id in self.products:
            raise ValueError(
                f"Product ID {product.product_id} already exists."
            )

        self.products[product.product_id] = product

    def delete_product(self, product_id):
        """Remove a product by its ID."""
        product_id = product_id.strip()

        if product_id not in self.products:
            raise ValueError(f"Product ID {product_id} was not found.")

        del self.products[product_id]

    def update_stock(self, product_id, new_stock):
        """Update the stock quantity of an existing product."""
        product_id = product_id.strip()

        if product_id not in self.products:
            raise ValueError(f"Product ID {product_id} was not found.")

        new_stock = validate_non_negative_integer(new_stock, "Stock")
        self.products[product_id].stock = new_stock

    def total_value(self):
        """Calculate the inventory's total selling value."""
        return sum(
            product.stock * product.selling_price
            for product in self.products.values()
        )

    def __add__(self, other):
        """
        Merge two inventories using the + operator.

        For matching IDs, stock is added, the lower purchase price
        is kept, and the higher selling price is kept.
        """
        if not isinstance(other, Inventory):
            return NotImplemented

        merged = Inventory()

        # Copy the first inventory so the original is not modified.
        for product in self.products.values():
            merged.add_product(
                Product(
                    product.product_id,
                    product.name,
                    product.stock,
                    product.purchase_price,
                    product.selling_price,
                )
            )

        # Merge the second inventory into the copied inventory.
        for product in other.products.values():
            if product.product_id not in merged.products:
                merged.add_product(
                    Product(
                        product.product_id,
                        product.name,
                        product.stock,
                        product.purchase_price,
                        product.selling_price,
                    )
                )
            else:
                existing = merged.products[product.product_id]

                if existing.name != product.name:
                    raise ValueError(
                        f"Conflicting names for product ID "
                        f"{product.product_id}."
                    )

                combined_stock = existing.stock + product.stock

                if combined_stock > MAX_INT64:
                    raise ValueError(
                        f"Merged stock exceeds the 64-bit limit for "
                        f"{product.product_id}."
                    )

                existing.stock = combined_stock
                existing.purchase_price = min(
                    existing.purchase_price, product.purchase_price
                )
                existing.selling_price = max(
                    existing.selling_price, product.selling_price
                )

        return merged

    def compare_inventory(self, other):
        """Compare inventories using their total selling value."""
        first_value = self.total_value()
        second_value = other.total_value()

        if first_value > second_value:
            return "First inventory has greater total value."
        if first_value < second_value:
            return "Second inventory has greater total value."
        return "Both inventories have equal total value."

    def display(self):
        """Print a readable summary of the inventory."""
        if not self.products:
            print("Inventory is empty.")
            return

        print("\nProduct ID | Name | Stock | Purchase | Selling")
        print("-" * 65)

        for product_id in sorted(self.products):
            product = self.products[product_id]
            print(
                f"{product.product_id} | {product.name} | "
                f"{product.stock} | {product.purchase_price:g} | "
                f"{product.selling_price:g}"
            )

        print(f"Total selling value: {self.total_value():g}")

    def save_to_file(self, file_path):
        """Save the inventory to a JSON file."""
        data = [
            self.products[product_id].to_dict()
            for product_id in sorted(self.products)
        ]

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    @classmethod
    def load_from_file(cls, file_path):
        """Load and validate an inventory from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("Inventory JSON must contain a list of products.")

        products = []

        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Product record {index} must be an object.")

            required_fields = {
                "product_id", "name", "stock",
                "purchase_price", "selling_price"
            }

            if not required_fields.issubset(item):
                raise ValueError(
                    f"Product record {index} is missing required fields."
                )

            products.append(
                Product(
                    product_id=item["product_id"],
                    name=item["name"],
                    stock=item["stock"],
                    purchase_price=item["purchase_price"],
                    selling_price=item["selling_price"],
                )
            )

        return cls(products)


def read_positive_integer(prompt, minimum, maximum):
    """Read an integer within a specified range."""
    raw_value = input(prompt).strip()

    try:
        value = int(raw_value)
    except ValueError:
        raise ValueError("Please enter a valid integer.")

    if not minimum <= value <= maximum:
        raise ValueError(f"Value must be between {minimum} and {maximum}.")

    return value


def read_product():
    """Read and validate details for a new product."""
    product_id = input("Product ID: ").strip()
    name = input("Product name: ").strip()

    stock = read_positive_integer(
        "Stock quantity (0 or more): ", 0, MAX_INT64
    )

    try:
        purchase_price = float(input("Purchase price: ").strip())
        selling_price = float(input("Selling price: ").strip())
    except ValueError:
        raise ValueError("Prices must be valid numbers.")

    return Product(
        product_id, name, stock, purchase_price, selling_price
    )


def main():
    """Load two inventories and execute the requested operations."""
    try:
        first_path = input("Path of first inventory JSON file: ").strip()
        second_path = input("Path of second inventory JSON file: ").strip()

        if not first_path or not second_path:
            raise ValueError("Both inventory file paths are required.")

        if not os.path.isfile(first_path):
            raise ValueError(f"File not found: {first_path}")

        if not os.path.isfile(second_path):
            raise ValueError(f"File not found: {second_path}")

        inventory_a = Inventory.load_from_file(first_path)
        inventory_b = Inventory.load_from_file(second_path)

        operation_count = read_positive_integer(
            "Number of operations (1 to 300000): ", 1, 300000
        )

        for _ in range(operation_count):
            print(
                "\nOperations: ADD, DELETE, UPDATE, MERGE, "
                "COMPARE, DISPLAY_A, DISPLAY_B, SAVE, EXIT"
            )
            operation = input("Enter operation: ").strip().upper()

            try:
                if operation == "ADD":
                    target = input("Target inventory (A/B): ").strip().upper()
                    inventory = {
                        "A": inventory_a,
                        "B": inventory_b
                    }.get(target)

                    if inventory is None:
                        raise ValueError("Target must be A or B.")

                    inventory.add_product(read_product())
                    print("Product added successfully.")

                elif operation == "DELETE":
                    target = input("Target inventory (A/B): ").strip().upper()
                    inventory = {
                        "A": inventory_a,
                        "B": inventory_b
                    }.get(target)

                    if inventory is None:
                        raise ValueError("Target must be A or B.")

                    product_id = input("Product ID to delete: ").strip()
                    inventory.delete_product(product_id)
                    print("Product deleted successfully.")

                elif operation == "UPDATE":
                    target = input("Target inventory (A/B): ").strip().upper()
                    inventory = {
                        "A": inventory_a,
                        "B": inventory_b
                    }.get(target)

                    if inventory is None:
                        raise ValueError("Target must be A or B.")

                    product_id = input("Product ID to update: ").strip()
                    new_stock = read_positive_integer(
                        "New stock quantity: ", 0, MAX_INT64
                    )
                    inventory.update_stock(product_id, new_stock)
                    print("Stock updated successfully.")

                elif operation == "MERGE":
                    merged = inventory_a + inventory_b
                    merged.display()

                    save_choice = input(
                        "Save merged inventory? (y/n): "
                    ).strip().lower()

                    if save_choice == "y":
                        output_path = input(
                            "Output JSON filename: "
                        ).strip()

                        if not output_path:
                            raise ValueError("Output path cannot be empty.")

                        merged.save_to_file(output_path)
                        print("Merged inventory saved.")

                elif operation == "COMPARE":
                    print(inventory_a.compare_inventory(inventory_b))

                elif operation == "DISPLAY_A":
                    inventory_a.display()

                elif operation == "DISPLAY_B":
                    inventory_b.display()

                elif operation == "SAVE":
                    target = input("Inventory to save (A/B): ").strip().upper()
                    inventory = {
                        "A": inventory_a,
                        "B": inventory_b
                    }.get(target)

                    if inventory is None:
                        raise ValueError("Target must be A or B.")

                    output_path = input("Output JSON filename: ").strip()
                    if not output_path:
                        raise ValueError("Output path cannot be empty.")

                    inventory.save_to_file(output_path)
                    print("Inventory saved successfully.")

                elif operation == "EXIT":
                    print("Exiting inventory manager.")
                    break

                else:
                    print("Unknown operation. Please try again.")

            except (ValueError, OSError) as error:
                print(f"Operation failed: {error}")

    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"Input or file error: {error}", file=sys.stderr)


if __name__ == "__main__":
    main()
