"""Two small charts drawn on a tkinter Canvas (no extra library needed)."""
import tkinter as tk

from settings import ACCENT, BORDER, MUTED, PANEL, TEXT, font


def make_chart(parent, draw_function, data):
    """Create a canvas and redraw it whenever its size changes."""
    canvas = tk.Canvas(parent, bg=PANEL, highlightthickness=0, height=125)
    canvas.bind("<Configure>", lambda e: draw_function(canvas, data))
    return canvas


def draw_status_chart(canvas, counts):
    """One stacked bar + legend. counts = [(label, number, colour), ...]"""
    canvas.delete("all")
    width = canvas.winfo_width()
    total = sum(number for _, number, _ in counts)

    if total == 0:
        canvas.create_text(8, 20, text="No equipment registered", anchor="w",
                           fill=MUTED, font=font(9))
        return

    x = 4
    for _, number, color in counts:
        if number:
            segment = (width - 8) * number / total
            canvas.create_rectangle(x, 8, x + segment, 28, fill=color,
                                    outline=PANEL, width=2)
            x += segment

    y = 52
    for label, number, color in counts:
        canvas.create_oval(4, y - 5, 14, y + 5, fill=color, outline="")
        canvas.create_text(22, y, text=label, anchor="w", fill=TEXT, font=font(9))
        canvas.create_text(width - 4, y, anchor="e", fill=MUTED, font=font(9),
                           text=f"{number}  ({number / total * 100:.0f}%)")
        y += 26


def draw_cost_chart(canvas, data):
    """Vertical bars. data = [("Oct", 1500.0), ...]"""
    canvas.delete("all")
    width, height = canvas.winfo_width(), canvas.winfo_height()
    biggest = max(cost for _, cost in data)

    if biggest <= 0:
        canvas.create_text(8, 20, text="No maintenance costs recorded yet",
                           anchor="w", fill=MUTED, font=font(9))
        return

    top, bottom_space = 20, 22
    base_y = height - bottom_space          # the line the bars stand on
    plot_height = base_y - top
    slot = (width - 20) / len(data)         # horizontal space per month
    bar_width = min(slot * 0.55, 46)

    canvas.create_line(10, base_y, width - 10, base_y, fill=BORDER)

    for index, (month, cost) in enumerate(data):
        center = 10 + slot * index + slot / 2
        bar_top = base_y - plot_height * cost / biggest
        if cost > 0:
            is_latest = index == len(data) - 1
            canvas.create_rectangle(
                center - bar_width / 2, bar_top, center + bar_width / 2, base_y,
                fill=ACCENT if is_latest else "#2B6E8F", outline="")
        label = f"{cost / 1000:.1f}k" if cost >= 1000 else f"{cost:.0f}"
        canvas.create_text(center, bar_top - 8, text=label, fill=TEXT, font=font(8))
        canvas.create_text(center, base_y + 11, text=month, fill=MUTED, font=font(8))

