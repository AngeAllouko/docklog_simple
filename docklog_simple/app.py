"""Main window: sidebar, page switching and status bar."""
import os
import tkinter as tk
from datetime import date

import database as db
from helpers import *
from pages.dashboard import DashboardPage
from pages.equipment import EquipmentPage
from pages.maintenance import MaintenancePage
from pages.maintenance_log import MaintenanceLogPage
from pages.reports import ReportsPage

# (name shown in the sidebar, icon, page class)
PAGES = [
    ("Dashboard", "◈", DashboardPage),
    ("Equipment", "⚙", EquipmentPage),
    ("Maintenance", "⚠", MaintenancePage),
    ("Maintenance Log", "☰", MaintenanceLogPage),
    ("Reports", "▤", ReportsPage),
]


class DockLogApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1250x780")
        root.minsize(1000, 680)
        root.configure(bg=BG)
        apply_styles(root)

        self.page = None          # the page currently shown
        self.current_name = None
        self.nav = {}             # page name -> (accent bar, button)

        self.build_sidebar()
        self.build_main_area()
        self.show_page("Dashboard")

    def build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=SIDEBAR, width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="⚓ DockLog", bg=SIDEBAR, fg=ACCENT,
                 font=font(23, "bold")).pack(anchor="w", padx=20, pady=(28, 3))
        tk.Label(sidebar, text="EQUIPMENT MANAGEMENT", bg=SIDEBAR, fg=MUTED,
                 font=font(8, "bold")).pack(anchor="w", padx=22, pady=(0, 30))

        for name, icon, _ in PAGES:
            row = tk.Frame(sidebar, bg=SIDEBAR)
            row.pack(fill="x", padx=(0, 9), pady=2)
            bar = tk.Frame(row, bg=SIDEBAR, width=4)   # cyan bar when active
            bar.pack(side="left", fill="y")
            button = tk.Button(
                row, text=f"  {icon}   {name}", anchor="w",
                command=lambda n=name: self.show_page(n),
                bg=SIDEBAR, fg=TEXT, activebackground=HOVER,
                activeforeground=ACCENT, relief="flat", bd=0,
                highlightthickness=0, font=font(10), cursor="hand2",
                padx=12, pady=12)
            button.pack(side="left", fill="x", expand=True)
            button.bind("<Enter>", lambda e, n=name: self.hover(n, HOVER))
            button.bind("<Leave>", lambda e, n=name: self.hover(n, SIDEBAR))
            self.nav[name] = (bar, button)

        tk.Label(sidebar, text="NAVAL OPERATIONS\nEquipment tracking system",
                 bg=SIDEBAR, fg=MUTED, justify="left",
                 font=font(9)).pack(side="bottom", anchor="w", padx=20, pady=20)

    def build_main_area(self):
        right = tk.Frame(self.root, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        statusbar = tk.Frame(right, bg=SIDEBAR)
        statusbar.pack(side="bottom", fill="x")
        self.status_left = tk.Label(statusbar, bg=SIDEBAR, fg=MUTED, font=font(8))
        self.status_left.pack(side="left", padx=14, pady=5)
        self.status_right = tk.Label(statusbar, bg=SIDEBAR, fg=MUTED, font=font(8))
        self.status_right.pack(side="right", padx=14, pady=5)

        self.content = tk.Frame(right, bg=BG)
        self.content.pack(fill="both", expand=True)

    def hover(self, name, color):
        if name != self.current_name:
            self.nav[name][1].configure(bg=color)

    def show_page(self, name):
        self.root.unbind("<Control-n>")   # each page sets its own shortcut
        if self.page is not None:
            self.page.destroy()

        page_class = [cls for n, _, cls in PAGES if n == name][0]
        self.current_name = name
        self.page = page_class(self.content, self)
        self.page.pack(fill="both", expand=True)

        for page_name, (bar, button) in self.nav.items():
            active = page_name == name
            bar.configure(bg=ACCENT if active else SIDEBAR)
            button.configure(bg=RAISED if active else SIDEBAR,
                             fg=ACCENT if active else TEXT,
                             font=font(10, "bold" if active else "normal"))
        self.refresh_statusbar()

    def refresh_statusbar(self, message=None):
        """Bottom bar. A message is shown for 4 seconds, then it resets."""
        alerts = sum(1 for r in db.fetch_equipment() if is_overdue(r[4], r[5]))
        self.status_left.configure(
            text=message or f"Database: {os.path.basename(DB_NAME)}",
            fg=GREEN if message else MUTED)
        self.status_right.configure(
            text=f"{date.today():%A, %d %B %Y}   |   {alerts} overdue alert(s)",
            fg=RED if alerts else MUTED)
        if message:
            self.root.after(4000, self.refresh_statusbar)
