import tkinter as tk
from tkinter import messagebox, ttk
import os
import json
import sys

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller .exe """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Proper path to credentials.json
credentials_path = resource_path("credentials.json")

def open_dashboard():
    root = tk.Tk()
    root.title("👑 Admin Dashboard")
    root.geometry("700x450")
    root.configure(bg="#1e1e2f")

    tk.Label(root, text="📋 Registered Users", font=("Segoe UI", 16, "bold"), bg="#1e1e2f", fg="#00ffcc").pack(pady=10)

    table_frame = tk.Frame(root, bg="#1e1e2f")
    table_frame.pack(fill=tk.BOTH, expand=True, padx=10)

    columns = ("Username", "Company", "Access", "Actions")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor=tk.CENTER, width=150)

    tree.pack(fill=tk.BOTH, expand=True)

    button_frame = tk.Frame(root, bg="#1e1e2f")
    button_frame.pack(pady=10)

    def load_users():
        tree.delete(*tree.get_children())
        if not os.path.exists(credentials_path):
            messagebox.showerror("Missing File", f"credentials.json not found at\n{credentials_path}")
            return

        with open(credentials_path, "r") as f:
            try:
                data = json.load(f)
            except:
                messagebox.showerror("Error", "Invalid JSON format.")
                return

        for username, info in data.items():
            company = info.get("company", "N/A")
            access = info.get("access", "allowed")
            tree.insert("", tk.END, iid=username, values=(username, company, access, "Action"))

    def toggle_access():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select User", "Please select a user.")
            return
        username = selected[0]

        with open(credentials_path, "r") as f:
            data = json.load(f)

        current = data[username].get("access", "allowed")
        new_status = "denied" if current == "allowed" else "allowed"
        data[username]["access"] = new_status

        with open(credentials_path, "w") as f:
            json.dump(data, f, indent=4)

        messagebox.showinfo("Access Toggled", f"{username} is now {new_status.upper()}.")
        load_users()

    def delete_user():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Select User", "Please select a user to delete.")
            return
        username = selected[0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {username}?")
        if not confirm:
            return

        with open(credentials_path, "r") as f:
            data = json.load(f)

        if username in data:
            del data[username]
            with open(credentials_path, "w") as f:
                json.dump(data, f, indent=4)

            messagebox.showinfo("Deleted", f"{username} has been deleted.")
            load_users()
        else:
            messagebox.showerror("Error", "User not found in file.")

    tk.Button(button_frame, text="🔄 Refresh", command=load_users, bg="#00cec9", fg="white", font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="✅ Toggle Access", command=toggle_access, bg="#6c5ce7", fg="white", font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)
    tk.Button(button_frame, text="🗑️ Delete User", command=delete_user, bg="#d63031", fg="white", font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)

    load_users()
    root.mainloop()

if __name__ == "__main__":
    open_dashboard()
