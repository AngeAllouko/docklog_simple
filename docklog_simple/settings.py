"""Settings: database file, lists of choices, colours, fonts and styles."""
import os
from tkinter import ttk

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docklog.db")
APP_TITLE = "DockLog | Naval Equipment Management"

STATUSES = ["Operational", "Under Maintenance", "Out of Service"]
OUTCOMES = ["Completed", "Partially Completed", "Requires Follow-up"]
DUE_SOON_DAYS = 7  # equipment due within this many days is shown in amber

# Colours
BG = "#0B1120"
SIDEBAR = "#111827"
PANEL = "#182235"
RAISED = "#1F2D45"
INPUT_BG = "#101827"
BORDER = "#2A3A55"
HOVER = "#263449"
SELECT = "#075985"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"
ACCENT = "#38BDF8"
GREEN = "#34D399"
RED = "#F87171"
ORANGE = "#FBBF24"

STATUS_COLORS = {
    "Operational": GREEN,
    "Under Maintenance": ORANGE,
    "Out of Service": RED,
}


def font(size, weight="normal"):
    return ("Segoe UI", size, weight)


def apply_styles(root):
    """Dark theme for tables, dropdowns and scrollbars."""
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure("Treeview", background=PANEL, foreground=TEXT,
                    fieldbackground=PANEL, rowheight=32, borderwidth=0,
                    bordercolor=BG, lightcolor=BG, darkcolor=BG, font=font(9))
    style.configure("Treeview.Heading", background=SIDEBAR, foreground=TEXT,
                    font=font(9, "bold"), padding=9, relief="flat")
    style.map("Treeview.Heading", background=[("active", HOVER)])
    style.map("Treeview", background=[("selected", SELECT)],
              foreground=[("selected", "#FFFFFF")])

    style.configure("TCombobox", fieldbackground=INPUT_BG, background=PANEL,
                    foreground=TEXT, arrowcolor=TEXT, bordercolor=BORDER,
                    lightcolor=INPUT_BG, darkcolor=INPUT_BG, padding=5)
    style.map("TCombobox",
              fieldbackground=[("readonly", INPUT_BG), ("disabled", INPUT_BG)],
              foreground=[("readonly", TEXT), ("disabled", MUTED)],
              selectbackground=[("readonly", INPUT_BG)],
              selectforeground=[("readonly", TEXT)])

    for name in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
        style.configure(name, background=BORDER, troughcolor=BG,
                        bordercolor=BG, arrowcolor=MUTED, lightcolor=BORDER,
                        darkcolor=BORDER, relief="flat", gripcount=0)
        style.map(name, background=[("active", "#3A4D6E"), ("pressed", ACCENT)])

    root.option_add("*TCombobox*Listbox.background", INPUT_BG)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", SELECT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
