"""Small tools shared by all pages: dates, buttons, cards, tables, CSV."""
import csv
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

from settings import *  # colours, fonts, STATUSES, ...


# ------------------------------------------------------------------- dates

def parse_date(text):
    """Turn 'YYYY-MM-DD' into a date. Raises ValueError if it is invalid."""
    parsed = datetime.strptime(text, "%Y-%m-%d").date()
    if parsed.isoformat() != text:  # rejects things like 2026-1-5
        raise ValueError(text)
    return parsed


def days_until(iso_date):
    return (date.fromisoformat(iso_date) - date.today()).days


def due_text(status, iso_date):
    """'3 d overdue', 'Today', 'in 15 d' or 'In progress'."""
    if status == "Under Maintenance":
        return "In progress"
    days = days_until(iso_date)
    if days < 0:
        return f"{-days} d overdue"
    if days == 0:
        return "Today"
    return f"in {days} d"


def is_overdue(status, iso_date):
    return status != "Under Maintenance" and days_until(iso_date) < 0


def row_tag(status, iso_date):
    """Row colour: 'overdue' (red), 'soon' (amber), 'out' or '' (normal)."""
    if status == "Under Maintenance":
        return ""
    days = days_until(iso_date)
    if days < 0:
        return "overdue"
    if days <= DUE_SOON_DAYS:
        return "soon"
    return "out" if status == "Out of Service" else ""


def money(value):
    return f"₹{value:,.2f}"


# ---------------------------------------------------------------- widgets

BUTTON_COLORS = {  # kind: (background, text, background when hovered)
    "primary": (ACCENT, BG, "#7DD3FC"),
    "secondary": (HOVER, TEXT, "#33445F"),
    "danger": ("#7F1D1D", "#FFFFFF", "#991B1B"),
}


def make_button(parent, text, command, kind="primary"):
    bg, fg, hover = BUTTON_COLORS[kind]
    button = tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                       activebackground=hover, activeforeground=fg,
                       relief="flat", bd=0, padx=14, pady=8,
                       highlightthickness=0, font=font(9, "bold"),
                       cursor="hand2")
    button.bind("<Enter>", lambda e: button.configure(bg=hover))
    button.bind("<Leave>", lambda e: button.configure(bg=bg))
    return button


def make_entry(parent, **options):
    return tk.Entry(parent, bg=INPUT_BG, fg=TEXT, insertbackground=TEXT,
                    disabledbackground=INPUT_BG, disabledforeground=MUTED,
                    relief="flat", font=font(10), highlightthickness=1,
                    highlightbackground=BORDER, highlightcolor=ACCENT,
                    **options)


def page_heading(parent, title, subtitle):
    tk.Label(parent, text=title, bg=BG, fg=TEXT,
             font=font(24, "bold")).pack(anchor="w", padx=28, pady=(23, 3))
    tk.Label(parent, text=subtitle, bg=BG, fg=MUTED,
             font=font(9)).pack(anchor="w", padx=29, pady=(0, 16))


def section_title(parent, text, pady=(10, 2)):
    tk.Label(parent, text=text, bg=BG, fg=TEXT,
             font=font(13, "bold")).pack(anchor="w", padx=28, pady=pady)


def stat_card(parent, title, value, color, caption=""):
    """A dashboard card with a coloured top edge."""
    card = tk.Frame(parent, bg=PANEL)
    tk.Frame(card, bg=color, height=3).pack(fill="x")
    inner = tk.Frame(card, bg=PANEL, padx=14, pady=12)
    inner.pack(fill="both", expand=True)
    tk.Label(inner, text=title.upper(), bg=PANEL, fg=MUTED,
             font=font(8, "bold")).pack(anchor="w")
    tk.Label(inner, text=str(value), bg=PANEL, fg=color,
             font=font(18, "bold")).pack(anchor="w", pady=(6, 0))
    tk.Label(inner, text=caption, bg=PANEL, fg=MUTED,
             font=font(8)).pack(anchor="w", pady=(2, 0))
    return card


def card_row(parent, cards):
    """Show several stat cards side by side. cards = list of argument tuples."""
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", padx=28, pady=(0, 14))
    for index, card_args in enumerate(cards):
        row.grid_columnconfigure(index, weight=1, uniform="cards")
        stat_card(row, *card_args).grid(
            row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 7, 0))


def make_panel(parent, title):
    frame = tk.Frame(parent, bg=PANEL, padx=16, pady=12)
    tk.Label(frame, text=title, bg=PANEL, fg=TEXT,
             font=font(11, "bold")).pack(anchor="w", pady=(0, 8))
    return frame


# ------------------------------------------------------------------ tables

def make_tree(parent, columns, headings, widths, pady=(8, 22)):
    """A table with scrollbars. Click a heading to sort by that column."""
    wrapper = tk.Frame(parent, bg=BG)
    wrapper.pack(fill="both", expand=True, padx=28, pady=pady)

    tree = ttk.Treeview(wrapper, columns=columns, show="headings",
                        selectmode="browse")
    for column, heading, width in zip(columns, headings, widths):
        tree.heading(column, text=heading, anchor="w",
                     command=lambda c=column: sort_tree(tree, c, False))
        tree.column(column, width=width, minwidth=65, anchor="w")

    y_scroll = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
    x_scroll = ttk.Scrollbar(wrapper, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    tree.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="ew")
    wrapper.grid_rowconfigure(0, weight=1)
    wrapper.grid_columnconfigure(0, weight=1)

    # Row colours (used with tags=("overdue",) when inserting a row)
    tree.tag_configure("overdue", background="#3B1D26", foreground="#FCA5A5")
    tree.tag_configure("soon", background="#3A2F12", foreground="#FCD34D")
    tree.tag_configure("out", foreground=RED)
    tree.tag_configure("followup", foreground=ORANGE)
    return tree


def sort_tree(tree, column, reverse):
    def sort_key(item):
        text = tree.set(item, column).replace(",", "")
        try:
            return (0, float(text), "")      # numbers first, sorted as numbers
        except ValueError:
            return (1, 0, text.lower())      # then text, sorted alphabetically

    items = sorted(tree.get_children(""), key=sort_key, reverse=reverse)
    for position, item in enumerate(items):
        tree.move(item, "", position)
    # Next click on this heading sorts the other way round
    tree.heading(column, command=lambda: sort_tree(tree, column, not reverse))


def insert_row(tree, values, tag="", iid=None):
    tree.insert("", "end", iid=iid, values=values, tags=(tag,) if tag else ())


# --------------------------------------------------------------------- CSV

def save_csv(name, tables, first_line=None):
    """Ask where to save, then write tables = [(title, headings, rows), ...]."""
    path = filedialog.asksaveasfilename(
        defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
        initialfile=f"{name}_{date.today().isoformat()}.csv")
    if not path:
        return None

    try:
        # utf-8-sig lets Excel show the ₹ sign correctly
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            if first_line:
                writer.writerow([first_line])
            for title, headings, rows in tables:
                writer.writerow([])
                writer.writerow([title])
                writer.writerow(headings)
                writer.writerows(rows)
    except OSError as error:
        messagebox.showerror("Export Error", str(error))
        return None
    return path
