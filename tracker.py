"""A simple desktop expense tracker with date-based category reports."""

from __future__ import annotations

import calendar
import tkinter as tk
from dataclasses import dataclass
from datetime import date, timedelta
from tkinter import messagebox, simpledialog, ttk


BACKGROUND = "#0a162d"
CARD = "#120a0a"
TEXT = "#FFFFFF"
MUTED = "#718096"
ACCENT = "#5367e8"
GRID = "#e8ebf2"


@dataclass
class Expense:
    spent_on: date
    item: str
    category: str
    amount: float
    notes: str


class ExpenseTracker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Expense Tracker - Reports")
        self.root.geometry("1020x740")
        self.root.minsize(780, 620)
        self.root.configure(bg=BACKGROUND)

        self.period = tk.StringVar(value="Daily")
        self.report_date = tk.StringVar(value=date.today().isoformat())
        self.category_filter = tk.StringVar(value="All categories")
        self.categories = ["Food", "Transport", "Shopping"]
        self.items = ["Groceries", "Bus fare", "Other"]
        self.records: list[Expense] = []
        self._configure_styles()
        self._build_screen()

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Report.Treeview",
            background=CARD,
            fieldbackground=CARD,
            foreground=TEXT,
            rowheight=36,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Report.Treeview.Heading",
            background=CARD,
            foreground=MUTED,
            font=("Segoe UI", 9, "bold"),
            borderwidth=0,
        )
        style.map("Report.Treeview", background=[("selected", "#e9edff")])

    def _build_screen(self) -> None:
        page = tk.Frame(self.root, bg=BACKGROUND, padx=36, pady=28)
        page.pack(fill="both", expand=True)

        header = tk.Frame(page, bg=BACKGROUND)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Reports",
            bg=BACKGROUND,
            fg=TEXT,
            font=("Segoe UI", 25, "bold"),
        ).pack(side="left")
        tk.Button(
            header,
            text="+  Add New Record",
            command=self._open_record_form,
            bg=ACCENT,
            fg="white",
            activebackground="#4355d0",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=17,
            pady=11,
        ).pack(side="right")

        period_bar = tk.Frame(page, bg=BACKGROUND)
        period_bar.pack(fill="x", pady=(23, 18))
        self.period_buttons: dict[str, tk.Button] = {}
        for period in ("Daily", "Weekly", "Monthly", "Yearly"):
            button = tk.Button(
                period_bar,
                text=period,
                command=lambda selected=period: self._select_period(selected),
                relief="flat",
                cursor="hand2",
                font=("Segoe UI", 10, "bold"),
                padx=17,
                pady=9,
            )
            button.pack(side="left", padx=(0, 9))
            self.period_buttons[period] = button

        report_card = tk.Frame(page, bg=CARD, padx=20, pady=17)
        report_card.pack(fill="both", expand=True)

        filter_bar = tk.Frame(report_card, bg=CARD)
        filter_bar.pack(fill="x", pady=(0, 14))
        self.report_title = tk.Label(
            filter_bar,
            text="Daily Report",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 15, "bold"),
        )
        self.report_title.pack(side="left", padx=(0, 16))

        self._label(filter_bar, "Select date").pack(side="left", padx=(0, 7))
        self.date_entry = tk.Entry(
            filter_bar,
            textvariable=self.report_date,
            width=12,
            relief="solid",
            bd=1,
            font=("Segoe UI", 9),
        )
        self.date_entry.pack(side="left", ipady=5)
        self.date_entry.bind(
            "<Return>",
            lambda event: self._update_report()
            if event.widget is self.date_entry
            else None,
        )
        self.date_entry.bind(
            "<FocusOut>",
            lambda event: self._update_report()
            if event.widget is self.date_entry
            else None,
        )
        tk.Button(
            filter_bar,
            text="▦",
            command=lambda: self._open_date_picker(self.report_date),
            bg=CARD,
            fg=ACCENT,
            relief="solid",
            bd=1,
            cursor="hand2",
            font=("Segoe UI", 11),
            padx=7,
            pady=2,
        ).pack(side="left", padx=(5, 15))

        self._label(filter_bar, "Category").pack(side="left", padx=(0, 7))
        self.category_combo = ttk.Combobox(
            filter_bar,
            textvariable=self.category_filter,
            state="readonly",
            width=17,
            values=["All categories", *self.categories],
        )
        self.category_combo.pack(side="left", ipady=3)
        self.category_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self._update_report()
            if event.widget is self.category_combo
            else None,
        )

        body = tk.Frame(report_card, bg=CARD)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        breakdown = tk.Frame(body, bg=CARD)
        breakdown.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        tk.Label(
            breakdown,
            text="Total Expenses / Category",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))
        columns = ("category", "amount")
        self.category_table = ttk.Treeview(
            breakdown,
            columns=columns,
            show="headings",
            height=7,
            style="Report.Treeview",
        )
        self.category_table.heading("category", text="CATEGORY")
        self.category_table.heading("amount", text="TOTAL")
        self.category_table.column("category", width=140, anchor="w")
        self.category_table.column("amount", width=100, anchor="e")
        self.category_table.pack(fill="x")
        self.total_label = tk.Label(
            breakdown,
            text="Total Expenses for Day\n$0.00",
            bg=CARD,
            fg=TEXT,
            justify="left",
            font=("Segoe UI", 13, "bold"),
        )
        self.total_label.pack(anchor="w", pady=(20, 0))

        chart_panel = tk.Frame(body, bg=CARD)
        chart_panel.grid(row=0, column=1, sticky="nsew")
        tk.Label(
            chart_panel,
            text="Expense Report Per Category",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w", pady=(0, 12))
        self.chart = tk.Canvas(
            chart_panel,
            bg=CARD,
            highlightthickness=0,
            height=300,
        )
        self.chart.pack(fill="both", expand=True)
        self.chart.bind(
            "<Configure>",
            lambda event: self._update_report() if event.width > 0 else None,
        )

        tk.Label(
            report_card,
            text="Amounts are grouped by category for the selected date range.",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(10, 0))
        self._update_period_buttons()
        self._update_report()

    @staticmethod
    def _label(parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(
            parent,
            text=text,
            bg=parent.cget("bg"),
            fg=MUTED,
            font=("Segoe UI", 9, "bold"),
        )

    def _select_period(self, period: str) -> None:
        self.period.set(period)
        self._update_period_buttons()
        self._update_report()

    def _update_period_buttons(self) -> None:
        for period, button in self.period_buttons.items():
            selected = period == self.period.get()
            button.configure(
                bg=ACCENT if selected else CARD,
                fg="white" if selected else MUTED,
                activebackground="#4355d0" if selected else "#e9edff",
                activeforeground="white" if selected else ACCENT,
            )

    def _open_date_picker(self, variable: tk.StringVar) -> None:
        try:
            selected = date.fromisoformat(variable.get())
        except ValueError:
            selected = date.today()

        popup = tk.Toplevel(self.root)
        popup.title("Select Date")
        popup.configure(bg=CARD)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        state = {"year": selected.year, "month": selected.month}

        calendar_frame = tk.Frame(popup, bg=CARD, padx=12, pady=12)
        calendar_frame.pack()
        heading = tk.Frame(calendar_frame, bg=CARD)
        heading.pack(fill="x", pady=(0, 8))
        month_label = tk.Label(
            heading, bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")
        )
        month_label.pack(side="left", expand=True)

        days_frame = tk.Frame(calendar_frame, bg=CARD)
        days_frame.pack()

        def draw_month() -> None:
            for child in days_frame.winfo_children():
                child.destroy()
            month_label.configure(
                text=f"{calendar.month_name[state['month']]} {state['year']}"
            )
            for column, weekday in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
                tk.Label(
                    days_frame,
                    text=weekday,
                    width=4,
                    bg=CARD,
                    fg=MUTED,
                    font=("Segoe UI", 8, "bold"),
                ).grid(row=0, column=column, pady=(0, 4))
            for row, week in enumerate(
                calendar.monthcalendar(state["year"], state["month"]), start=1
            ):
                for column, day_number in enumerate(week):
                    if day_number:
                        tk.Button(
                            days_frame,
                            text=str(day_number),
                            width=3,
                            command=lambda day=day_number: choose_day(day),
                            bg=CARD,
                            fg=TEXT,
                            relief="flat",
                            cursor="hand2",
                        ).grid(row=row, column=column, padx=1, pady=1)

        def change_month(step: int) -> None:
            month_index = state["year"] * 12 + state["month"] - 1 + step
            state["year"], zero_based_month = divmod(month_index, 12)
            state["month"] = zero_based_month + 1
            draw_month()

        def choose_day(day_number: int) -> None:
            variable.set(
                date(state["year"], state["month"], day_number).isoformat()
            )
            if variable is self.report_date:
                self._update_report()
            popup.destroy()

        tk.Button(
            heading, text="‹", command=lambda: change_month(-1), bg=CARD, relief="flat"
        ).pack(side="left")
        tk.Button(
            heading, text="›", command=lambda: change_month(1), bg=CARD, relief="flat"
        ).pack(side="right")
        draw_month()

    def _open_record_form(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Record")
        dialog.configure(bg=CARD)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        form = tk.Frame(dialog, bg=CARD, padx=24, pady=20)
        form.pack(fill="both", expand=True)
        tk.Label(
            form,
            text="Add New Record",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 15))
        form.columnconfigure(1, weight=1)

        tk.Label(form, text="Date", bg=CARD, fg=MUTED).grid(
            row=1, column=0, sticky="w", pady=6, padx=(0, 15)
        )
        record_date = tk.StringVar(value=date.today().isoformat())
        date_input = tk.Entry(form, textvariable=record_date, width=22)
        date_input.grid(row=1, column=1, sticky="ew", pady=6)
        tk.Button(
            form,
            text="▦",
            command=lambda: self._open_date_picker(record_date),
            bg=CARD,
            relief="solid",
            bd=1,
            cursor="hand2",
        ).grid(row=1, column=2, padx=(6, 0), pady=6)

        tk.Label(form, text="Category", bg=CARD, fg=MUTED).grid(
            row=2, column=0, sticky="w", pady=6, padx=(0, 15)
        )
        category = tk.StringVar(value=self.categories[0])
        category_combo = ttk.Combobox(
            form,
            textvariable=category,
            state="readonly",
            values=self.categories,
        )
        category_combo.grid(row=2, column=1, columnspan=2, sticky="ew", pady=6)

        tk.Label(form, text="Item", bg=CARD, fg=MUTED).grid(
            row=3, column=0, sticky="w", pady=6, padx=(0, 15)
        )
        item = tk.StringVar(value=self.items[0])
        item_combo = ttk.Combobox(
            form,
            textvariable=item,
            values=self.items,
        )
        item_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=6)

        tk.Label(form, text="Amount", bg=CARD, fg=MUTED).grid(
            row=4, column=0, sticky="w", pady=6, padx=(0, 15)
        )
        amount = tk.Entry(form)
        amount.grid(row=4, column=1, columnspan=2, sticky="ew", pady=6)

        tk.Label(form, text="Notes / Description", bg=CARD, fg=MUTED).grid(
            row=5, column=0, sticky="nw", pady=6, padx=(0, 15)
        )
        notes = tk.Text(form, width=32, height=3, wrap="word")
        notes.grid(row=5, column=1, columnspan=2, sticky="ew", pady=6)

        def add_item() -> None:
            value = simpledialog.askstring(
                "Add New Item", "Item name:", parent=dialog
            )
            if value and value.strip():
                value = value.strip()
                if value not in self.items:
                    self.items.append(value)
                    item_combo.configure(values=self.items)
                item.set(value)

        def add_category() -> None:
            value = simpledialog.askstring(
                "Add New Category", "Category name:", parent=dialog
            )
            if value and value.strip():
                value = value.strip()
                if value not in self.categories:
                    self.categories.append(value)
                    category_combo.configure(values=self.categories)
                    self.category_combo.configure(
                        values=["All categories", *self.categories]
                    )
                category.set(value)

        utility_buttons = tk.Frame(form, bg=CARD)
        utility_buttons.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 0))
        tk.Button(
            utility_buttons,
            text="Add New Item",
            command=add_item,
            bg="#eef0ff",
            fg=ACCENT,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=7,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            utility_buttons,
            text="Add New Category",
            command=add_category,
            bg="#eef0ff",
            fg=ACCENT,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=7,
        ).pack(side="left")

        actions = tk.Frame(form, bg=CARD)
        actions.grid(row=7, column=0, columnspan=3, sticky="e", pady=(18, 0))

        def save_record() -> None:
            try:
                spent_on = date.fromisoformat(record_date.get().strip())
            except ValueError:
                messagebox.showerror(
                    "Invalid date",
                    "Enter a valid date in YYYY-MM-DD format.",
                    parent=dialog,
                )
                return
            try:
                value = float(amount.get().strip())
                if value <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid amount",
                    "Enter an amount greater than zero.",
                    parent=dialog,
                )
                return
            item_name = item.get().strip()
            category_name = category.get().strip()
            if not item_name or not category_name:
                messagebox.showerror(
                    "Missing information",
                    "Choose or enter both an item and a category.",
                    parent=dialog,
                )
                return
            if item_name not in self.items:
                self.items.append(item_name)
            if category_name not in self.categories:
                self.categories.append(category_name)
                self.category_combo.configure(
                    values=["All categories", *self.categories]
                )
            self.records.append(
                Expense(
                    spent_on=spent_on,
                    item=item_name,
                    category=category_name,
                    amount=value,
                    notes=notes.get("1.0", "end").strip(),
                )
            )
            self.report_date.set(spent_on.isoformat())
            self.category_filter.set("All categories")
            self._update_report()
            dialog.destroy()

        tk.Button(
            actions,
            text="Exit",
            command=dialog.destroy,
            bg="#eef0f4",
            fg=MUTED,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=9,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            actions,
            text="Save Record",
            command=save_record,
            bg=ACCENT,
            fg="white",
            activebackground="#4355d0",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=9,
        ).pack(side="left")
        item_combo.focus_set()

    def _date_in_period(self, spent_on: date, selected: date) -> bool:
        period = self.period.get()
        if period == "Daily":
            return spent_on == selected
        if period == "Weekly":
            start = selected - timedelta(days=selected.weekday())
            return start <= spent_on < start + timedelta(days=7)
        if period == "Monthly":
            return spent_on.year == selected.year and spent_on.month == selected.month
        return spent_on.year == selected.year

    def _update_report(self) -> None:
        try:
            selected = date.fromisoformat(self.report_date.get().strip())
        except ValueError:
            self.report_title.configure(text=f"{self.period.get()} Report")
            self.total_label.configure(text="Enter a valid date (YYYY-MM-DD)")
            self._populate_breakdown({})
            self._draw_chart({})
            return

        period = self.period.get()
        self.report_title.configure(text=f"{period} Report")
        matching = [
            record
            for record in self.records
            if self._date_in_period(record.spent_on, selected)
        ]
        category = self.category_filter.get()
        if category != "All categories":
            matching = [record for record in matching if record.category == category]

        totals: dict[str, float] = {}
        for record in matching:
            totals[record.category] = totals.get(record.category, 0.0) + record.amount

        self._populate_breakdown(totals)
        total = sum(totals.values())
        period_names = {
            "Daily": "Day",
            "Weekly": "Week",
            "Monthly": "Month",
            "Yearly": "Year",
        }
        self.total_label.configure(
            text=f"Total Expenses for {period_names[period]}\n${total:,.2f}"
        )
        self._draw_chart(totals)

    def _populate_breakdown(self, totals: dict[str, float]) -> None:
        for row in self.category_table.get_children():
            self.category_table.delete(row)
        for category, amount in sorted(totals.items()):
            self.category_table.insert(
                "", "end", values=(category, f"${amount:,.2f}")
            )
        if not totals:
            self.category_table.insert("", "end", values=("No expenses", "$0.00"))

    def _draw_chart(self, totals: dict[str, float]) -> None:
        self.chart.delete("all")
        width = max(self.chart.winfo_width(), 320)
        height = max(self.chart.winfo_height(), 260)
        left, right, top, bottom = 48, width - 18, 15, height - 52
        self.chart.create_line(left, top, left, bottom, fill=GRID)
        self.chart.create_line(left, bottom, right, bottom, fill=GRID)

        max_amount = max(totals.values(), default=0.0)
        if max_amount <= 0:
            self.chart.create_text(
                (left + right) / 2,
                (top + bottom) / 2,
                text="No expenses for this period",
                fill=MUTED,
                font=("Segoe UI", 10),
            )
            return

        for tick in range(5):
            y = bottom - (bottom - top) * tick / 4
            amount = max_amount * tick / 4
            self.chart.create_line(left, y, right, y, fill=GRID)
            self.chart.create_text(
                left - 7,
                y,
                text=f"${amount:,.0f}",
                anchor="e",
                fill=MUTED,
                font=("Segoe UI", 8),
            )

        entries = list(totals.items())
        slot = (right - left) / len(entries)
        bar_width = min(58, slot * 0.58)
        for index, (category, amount) in enumerate(entries):
            center = left + slot * (index + 0.5)
            bar_top = bottom - (bottom - top) * amount / max_amount
            self.chart.create_rectangle(
                center - bar_width / 2,
                bar_top,
                center + bar_width / 2,
                bottom,
                fill=ACCENT,
                outline="",
            )
            self.chart.create_text(
                center,
                bottom + 19,
                text=category[:12],
                fill=MUTED,
                font=("Segoe UI", 8),
            )


def main() -> None:
    root = tk.Tk()
    ExpenseTracker(root)
    root.mainloop()


if __name__ == "__main__":
    main()
