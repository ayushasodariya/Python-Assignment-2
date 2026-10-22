import re
import tkinter as tk
from tkinter import ttk, messagebox

import mysql.connector
from mysql.connector import Error


# Database settings: change these to match your MySQL installation.
DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "YOUR_PASSWORD"  # Replace with your MySQL password
DB_NAME = "contact_manager_db"


class ContactManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Contact Manager")
        self.root.geometry("1050x650")
        self.root.minsize(850, 550)

        self.connection = None
        self.selected_contact_id = None
        self.contact_ids = []

        # Create the database and table before opening the GUI.
        if not self.connect_database():
            self.root.destroy()
            return

        self.build_menu()
        self.build_gui()
        self.load_contacts()

        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def connect_database(self):
        """Connect to MySQL and create the required database/table."""
        try:
            # Connect without selecting a database so it can be created.
            server = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD
            )
            cursor = server.cursor()
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"
            )
            cursor.close()
            server.close()

            self.connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )

            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Contact (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(254) NOT NULL UNIQUE,
                    phone VARCHAR(20) NOT NULL,
                    category VARCHAR(30) NOT NULL,
                    notes TEXT,
                    INDEX idx_contact_name (name),
                    INDEX idx_contact_phone (phone)
                )
            """)
            self.connection.commit()
            cursor.close()
            return True

        except Error as error:
            messagebox.showerror(
                "Database Error",
                f"Could not connect to MySQL.\n\n{error}\n\n"
                "Check MySQL Server and your database credentials."
            )
            return False

    def build_menu(self):
        """Create a simple application menu."""
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(
            label="Refresh Contacts", command=self.load_contacts
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="Exit", command=self.close_application
        )

        menu_bar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menu_bar)

    def build_gui(self):
        """Create form controls, search options and contact list."""
        form = ttk.LabelFrame(
            self.root, text="Contact Details", padding=12
        )
        form.pack(fill="x", padx=12, pady=8)

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.category_var = tk.StringVar(value="Friend")

        ttk.Label(form, text="Name:").grid(
            row=0, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            form, textvariable=self.name_var, width=32
        ).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Email:").grid(
            row=0, column=2, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            form, textvariable=self.email_var, width=32
        ).grid(row=0, column=3, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Phone:").grid(
            row=1, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Entry(
            form, textvariable=self.phone_var, width=32
        ).grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Category:").grid(
            row=1, column=2, sticky="w", padx=5, pady=5
        )
        ttk.Combobox(
            form,
            textvariable=self.category_var,
            values=("Friend", "Family", "Faculty", "Work", "Other"),
            state="readonly",
            width=29
        ).grid(row=1, column=3, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Notes:").grid(
            row=2, column=0, sticky="nw", padx=5, pady=5
        )
        self.notes_text = tk.Text(form, height=3, width=65)
        self.notes_text.grid(
            row=2, column=1, columnspan=3,
            sticky="ew", padx=5, pady=5
        )

        # Radio buttons select the sort direction.
        self.sort_direction = tk.StringVar(value="ASC")

        ttk.Label(form, text="Sort direction:").grid(
            row=3, column=0, sticky="w", padx=5, pady=5
        )
        ttk.Radiobutton(
            form, text="A to Z", variable=self.sort_direction,
            value="ASC", command=self.load_contacts
        ).grid(row=3, column=1, sticky="w")

        ttk.Radiobutton(
            form, text="Z to A", variable=self.sort_direction,
            value="DESC", command=self.load_contacts
        ).grid(row=3, column=2, sticky="w")

        buttons = ttk.Frame(form)
        buttons.grid(
            row=4, column=0, columnspan=4, pady=10
        )

        ttk.Button(
            buttons, text="Add Contact", command=self.add_contact
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons, text="Update Selected",
            command=self.update_contact
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons, text="Delete Selected",
            command=self.delete_contact
        ).pack(side="left", padx=4)

        ttk.Button(
            buttons, text="Clear Form",
            command=self.clear_form
        ).pack(side="left", padx=4)

        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        # Search controls.
        search_frame = ttk.LabelFrame(
            self.root, text="Search Contacts", padding=10
        )
        search_frame.pack(fill="x", padx=12, pady=5)

        self.search_field = tk.StringVar(value="Name")
        self.search_var = tk.StringVar()

        ttk.Label(search_frame, text="Search by:").pack(
            side="left", padx=5
        )

        ttk.Combobox(
            search_frame,
            textvariable=self.search_field,
            values=("Name", "Email", "Phone"),
            state="readonly",
            width=10
        ).pack(side="left", padx=5)

        search_entry = ttk.Entry(
            search_frame, textvariable=self.search_var, width=35
        )
        search_entry.pack(side="left", padx=5)
        search_entry.bind(
            "<Return>", lambda event: self.search_contacts()
        )

        ttk.Button(
            search_frame, text="Search",
            command=self.search_contacts
        ).pack(side="left", padx=4)

        ttk.Button(
            search_frame, text="Show All",
            command=self.load_contacts
        ).pack(side="left", padx=4)

        # Listbox displays contacts and allows selection for editing.
        list_frame = ttk.LabelFrame(
            self.root, text="Saved Contacts (select a row to edit)",
            padding=10
        )
        list_frame.pack(
            fill="both", expand=True, padx=12, pady=8
        )

        self.contact_list = tk.Listbox(
            list_frame, font=("Consolas", 10),
            selectmode=tk.SINGLE
        )
        self.contact_list.pack(
            side="left", fill="both", expand=True
        )
        self.contact_list.bind(
            "<<ListboxSelect>>", self.select_contact
        )

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.contact_list.yview
        )
        scrollbar.pack(side="right", fill="y")
        self.contact_list.config(yscrollcommand=scrollbar.set)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            self.root, textvariable=self.status_var,
            anchor="w"
        ).pack(fill="x", padx=12, pady=4)

    def validate_contact(self):
        """Check the form before inserting or updating a contact."""
        name = self.name_var.get().strip()
        email = self.email_var.get().strip()
        phone = self.phone_var.get().strip()
        category = self.category_var.get().strip()
        notes = self.notes_text.get("1.0", "end-1c").strip()

        if not name:
            messagebox.showwarning("Validation", "Name is required.")
            return None

        if len(name) > 100:
            messagebox.showwarning(
                "Validation", "Name cannot exceed 100 characters."
            )
            return None

        # Validate a conventional email address using a regular expression.
        email_pattern = (
            r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        )
        if not re.fullmatch(email_pattern, email):
            messagebox.showwarning(
                "Validation", "Please enter a valid email address."
            )
            return None

        # Allow common phone formatting, but require 7 to 15 digits.
        if not re.fullmatch(r"[+0-9() -]+", phone):
            messagebox.showwarning(
                "Validation", "Phone contains invalid characters."
            )
            return None

        digit_count = sum(character.isdigit() for character in phone)
        if not 7 <= digit_count <= 15:
            messagebox.showwarning(
                "Validation", "Phone must contain 7 to 15 digits."
            )
            return None

        if category not in (
            "Friend", "Family", "Faculty", "Work", "Other"
        ):
            messagebox.showwarning(
                "Validation", "Select a valid category."
            )
            return None

        return name, email, phone, category, notes

    def add_contact(self):
        """Insert a new contact, rejecting duplicate email addresses."""
        data = self.validate_contact()
        if data is None:
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO Contact (name, email, phone, category, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, data)
            self.connection.commit()
            cursor.close()

            self.load_contacts()
            self.clear_form()
            messagebox.showinfo("Success", "Contact added successfully.")

        except mysql.connector.IntegrityError:
            self.connection.rollback()
            messagebox.showerror(
                "Duplicate Email",
                "A contact with this email already exists."
            )
        except Error as error:
            self.connection.rollback()
            messagebox.showerror("Database Error", str(error))

    def update_contact(self):
        """Update the selected contact using its database ID."""
        if self.selected_contact_id is None:
            messagebox.showwarning(
                "Selection", "Select a contact from the list first."
            )
            return

        data = self.validate_contact()
        if data is None:
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE Contact
                SET name=%s, email=%s, phone=%s, category=%s, notes=%s
                WHERE id=%s
            """, data + (self.selected_contact_id,))
            self.connection.commit()
            cursor.close()

            self.load_contacts()
            self.clear_form()
            messagebox.showinfo("Success", "Contact updated successfully.")

        except mysql.connector.IntegrityError:
            self.connection.rollback()
            messagebox.showerror(
                "Duplicate Email",
                "Another contact already uses this email."
            )
        except Error as error:
            self.connection.rollback()
            messagebox.showerror("Database Error", str(error))

    def delete_contact(self):
        """Delete a selected contact after confirmation."""
        if self.selected_contact_id is None:
            messagebox.showwarning(
                "Selection", "Select a contact to delete."
            )
            return

        if not messagebox.askyesno(
            "Confirm Delete", "Delete this contact permanently?"
        ):
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "DELETE FROM Contact WHERE id=%s",
                (self.selected_contact_id,)
            )
            self.connection.commit()
            cursor.close()

            self.load_contacts()
            self.clear_form()
            messagebox.showinfo("Success", "Contact deleted.")

        except Error as error:
            self.connection.rollback()
            messagebox.showerror("Database Error", str(error))

    def display_contacts(self, rows):
        """Refresh the listbox and preserve IDs for selected rows."""
        self.contact_list.delete(0, tk.END)
        self.contact_ids = []

        for row in rows:
            contact_id, name, email, phone, category, notes = row
            self.contact_ids.append(contact_id)

            # Notes are kept in the database but omitted from this row.
            line = (
                f"{contact_id:<5} {name[:20]:<21} "
                f"{email[:32]:<33} {phone:<17} {category}"
            )
            self.contact_list.insert(tk.END, line)

        self.status_var.set(f"{len(rows)} contact(s) displayed.")

    def load_contacts(self):
        """Display all contacts sorted by name."""
        if self.connection is None or not self.connection.is_connected():
            return

        try:
            direction = (
                "DESC" if self.sort_direction.get() == "DESC" else "ASC"
            )
            cursor = self.connection.cursor()
            # Direction is chosen from fixed allowed values, not user SQL.
            cursor.execute(f"""
                SELECT id, name, email, phone, category, notes
                FROM Contact
                ORDER BY name {direction}, id ASC
            """)
            rows = cursor.fetchall()
            cursor.close()
            self.display_contacts(rows)

        except Error as error:
            messagebox.showerror("Database Error", str(error))

    def search_contacts(self):
        """Search by name, email or phone using a parameterized query."""
        keyword = self.search_var.get().strip()
        field_map = {
            "Name": "name",
            "Email": "email",
            "Phone": "phone"
        }

        if not keyword:
            messagebox.showwarning(
                "Search", "Enter a name, email or phone number."
            )
            return

        column = field_map.get(self.search_field.get())
        if column is None:
            messagebox.showwarning("Search", "Select a valid search field.")
            return

        try:
            cursor = self.connection.cursor()
            # Only the whitelisted column is inserted into SQL;
            # the search text is passed safely as a parameter.
            cursor.execute(f"""
                SELECT id, name, email, phone, category, notes
                FROM Contact
                WHERE {column} LIKE %s
                ORDER BY name ASC, id ASC
            """, (f"%{keyword}%",))
            rows = cursor.fetchall()
            cursor.close()
            self.display_contacts(rows)

        except Error as error:
            messagebox.showerror("Database Error", str(error))

    def select_contact(self, event=None):
        """Fill the form with the selected contact's details."""
        selection = self.contact_list.curselection()
        if not selection:
            return

        index = selection[0]
        contact_id = self.contact_ids[index]

        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, name, email, phone, category, notes
                FROM Contact WHERE id=%s
            """, (contact_id,))
            row = cursor.fetchone()
            cursor.close()

            if row is None:
                return

            self.selected_contact_id = row[0]
            self.name_var.set(row[1])
            self.email_var.set(row[2])
            self.phone_var.set(row[3])
            self.category_var.set(row[4])

            self.notes_text.delete("1.0", tk.END)
            self.notes_text.insert("1.0", row[5] or "")

        except Error as error:
            messagebox.showerror("Database Error", str(error))

    def clear_form(self):
        """Clear the form and remove the current selection."""
        self.selected_contact_id = None
        self.name_var.set("")
        self.email_var.set("")
        self.phone_var.set("")
        self.category_var.set("Friend")
        self.notes_text.delete("1.0", tk.END)
        self.contact_list.selection_clear(0, tk.END)

    def close_application(self):
        """Close the database connection cleanly."""
        if self.connection is not None:
            if self.connection.is_connected():
                self.connection.close()
        self.root.destroy()


def main():
    """Application entry point."""
    root = tk.Tk()
    ContactManager(root)
    root.mainloop()


if __name__ == "__main__":
    main()
