"""DockLog - start the program with:  python main.py"""
import sqlite3
import tkinter as tk
from tkinter import messagebox

import database as db
from app import DockLogApp

try:
    db.initialize_database()
except sqlite3.Error as error:
    messagebox.showerror("Database Error", f"Could not start DockLog:\n{error}")
    raise SystemExit

root = tk.Tk()
DockLogApp(root)
root.mainloop()
