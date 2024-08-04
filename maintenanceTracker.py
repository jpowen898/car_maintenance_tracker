#!/bin/python3
import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import sqlite3
import tkinter.font as font

FIRST_COLUMN_WIDTH = 20
COLUMN_WIDTH = 20


class ScrollableFrame(tk.Frame):
    """
    A scrollable frame for adding scrolling capability to a tkinter frame.
    """

    def __init__(self, container, *args, **kwargs):
        """
        Initializes the ScrollableFrame.

        Args:
            container (tk.Widget): The parent widget.
        """
        super().__init__(container, *args, **kwargs)
        self.canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel events to the self.canvas for scrolling
        # Windows scroll bind
        container.bind("<MouseWheel>", self._on_mousewheel)
        # Linux scoll binds
        container.bind("<Button-4>", self._on_mousewheel)
        container.bind("<Button-5>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        """
        Handles mouse wheel scrolling.

        Args:
            event (tk.Event): The event object.
        """
        # Determine the scroll direction and amount
        if event.num == 5 or event.delta == -120:
            delta = 1
        if event.num == 4 or event.delta == 120:
            delta = -1
        self.winfo_children()[0].yview_scroll(delta, "units")


class CarMaintenanceApp:
    """
    A car maintenance tracking application.
    """

    def __init__(self, root):
        """
        Initializes the CarMaintenanceApp.

        Args:
            root (tk.Tk): The root tkinter window.
        """
        self.root = root
        self.root.title("Car Maintenance Tracker")
        self.load_config()
        self.current_mileage = tk.IntVar(value=self.get_latest_mileage())
        self.bold_font = font.Font(weight="bold")
        self.create_widgets()
        self.update_task_status()

    def load_config(self):
        """
        Loads the maintenance tasks configuration from a JSON file.
        """
        with open("config.json", "r") as file:
            self.config = json.load(file)["maintenance_tasks"]

    def get_latest_mileage(self):
        """
        Retrieves the latest mileage from the database.

        Returns:
            int: The latest mileage.
        """
        conn = sqlite3.connect("car_maintenance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(mileage) FROM maintenance")
        result = cursor.fetchone()
        conn.close()
        return result[0] if result[0] is not None else 0

    def create_widgets(self):
        """
        Creates and arranges the widgets in the main window.
        """
        baseframe = tk.Frame(self.root, padx=COLUMN_WIDTH, pady=5)
        baseframe.pack(fill=tk.X)
        first_column_font = font.Font(weight="bold")
        bold_font = font.Font(weight="bold", size=9)

        # Create and pack the header labels
        tk.Label(
            baseframe,
            font=first_column_font,
            text="Maintenance Task:",
            width=FIRST_COLUMN_WIDTH,
        ).pack(side=tk.LEFT)
        tk.Label(
            baseframe, font=bold_font, text="Last done date:", width=COLUMN_WIDTH
        ).pack(side=tk.LEFT)
        tk.Label(
            baseframe, font=bold_font, text="Last done miles:", width=COLUMN_WIDTH
        ).pack(side=tk.LEFT)
        tk.Label(
            baseframe, font=bold_font, text="Next due miles:", width=COLUMN_WIDTH
        ).pack(side=tk.LEFT)
        tk.Label(
            baseframe, font=bold_font, text="Current Mileage:", width=COLUMN_WIDTH
        ).pack(side=tk.LEFT)

        # Create and pack the mileage entry widget
        self.mileage_entry = ttk.Entry(baseframe, width=FIRST_COLUMN_WIDTH)
        self.mileage_entry.pack(side=tk.LEFT)
        self.mileage_entry.insert(0, str(self.current_mileage.get()))
        self.mileage_entry.bind("<Return>", lambda event: self.update_mileage())

        # Create and pack the scrollable frame for tasks
        self.scrollable_frame = ScrollableFrame(self.root)
        self.scrollable_frame.pack(fill="both", expand=True)

        self.task_frames = []
        for task in self.config:
            frame = tk.Frame(
                self.scrollable_frame.scrollable_frame, padx=COLUMN_WIDTH, pady=5
            )
            frame.pack(fill=tk.X)
            tk.Label(
                frame,
                text=task["task"],
                width=FIRST_COLUMN_WIDTH,
                font=first_column_font,
            ).pack(side=tk.LEFT)
            self.create_task_status_widgets(frame, task)
            self.task_frames.append(frame)
        self.set_window_size(self.root, self.scrollable_frame, 40)

    def create_task_status_widgets(self, frame, task):
        """
        Creates and arranges the widgets for each task's status.

        Args:
            frame (tk.Frame): The frame to contain the widgets.
            task (dict): The task configuration.
        """
        last_done_date_label = tk.Label(frame, text="N/A", width=COLUMN_WIDTH)
        last_done_miles_label = tk.Label(frame, text="N/A", width=COLUMN_WIDTH)
        last_done_date_label.pack(side=tk.LEFT)
        last_done_miles_label.pack(side=tk.LEFT)
        next_due_label = tk.Label(frame, text="N/A", width=COLUMN_WIDTH)
        next_due_label.pack(side=tk.LEFT)
        status_label = tk.Label(frame, text="Status", width=10)
        status_label.pack(side=tk.LEFT, padx=5)
        tk.Button(
            frame, text="Mark as Done", command=lambda t=task: self.mark_as_done(t)
        ).pack(side=tk.RIGHT)
        tk.Button(
            frame, text="View History", command=lambda t=task: self.view_history(t)
        ).pack(side=tk.RIGHT)
        frame.last_done_date_label = last_done_date_label
        frame.last_done_miles_label = last_done_miles_label
        frame.next_due_label = next_due_label
        frame.status_label = status_label

    def mark_as_done(self, task):
        """
        Marks a task as done by inserting a new record in the database.

        Args:
            task (dict): The task configuration.
        """
        date = datetime.now().strftime("%Y-%m-%d")
        mileage = int(self.current_mileage.get())
        conn = sqlite3.connect("car_maintenance.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO maintenance (task, date, mileage) VALUES (?, ?, ?)",
            (task["task"], date, mileage),
        )
        conn.commit()
        conn.close()
        self.update_task_status()

    def update_task_status(self):
        """
        Updates the status labels for all tasks.
        """
        conn = sqlite3.connect("car_maintenance.db")
        cursor = conn.cursor()
        for frame, task in zip(self.task_frames, self.config):
            cursor.execute(
                "SELECT date, mileage FROM maintenance WHERE task = ? ORDER BY id DESC LIMIT 1",
                (task["task"],),
            )
            result = cursor.fetchone()
            if result:
                last_done_date, last_done_mileage = result
                frame.last_done_date_label.config(text=last_done_date)
                frame.last_done_miles_label.config(text=last_done_mileage)
                next_due_mileage = last_done_mileage + task["frequency_miles"]
                frame.next_due_label.config(text=str(next_due_mileage))
                self.update_status_label(frame, last_done_mileage, task)
            else:
                frame.last_done_date_label.config(text="N/A")
                frame.last_done_miles_label.config(text="0")
                last_done_mileage = 0
                next_due_mileage = last_done_mileage + task["frequency_miles"]
                frame.next_due_label.config(text=str(next_due_mileage))
                self.update_status_label(frame, last_done_mileage, task)
        conn.close()

    def update_status_label(self, frame, last_done_mileage, task):
        """
        Updates the status label based on the task's mileage.

        Args:
            frame (tk.Frame): The frame containing the status label.
            last_done_mileage (int): The mileage at which the task was last done.
            task (dict): The task configuration.
        """
        current_mileage = int(self.current_mileage.get())
        if current_mileage >= last_done_mileage + task["frequency_max_miles"]:
            frame.status_label.config(text="ASAP", bg="red")
        elif current_mileage >= last_done_mileage + task["frequency_miles"]:
            frame.status_label.config(text="Soon", bg="yellow")
        else:
            frame.status_label.config(text="OK", bg="green")

    def update_mileage(self):
        """
        Updates the current mileage based on the entry widget's value.
        """
        try:
            value = int(self.mileage_entry.get())
            self.current_mileage.set(value)
            self.mileage_entry.delete(0, tk.END)
            self.mileage_entry.insert(0, str(value))
            self.update_task_status()
        except ValueError:
            print("Invalid mileage input")

    def view_history(self, task):
        """
        Opens a new window to view the history of a task.

        Args:
            task (dict): The task configuration.
        """
        conn = sqlite3.connect("car_maintenance.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, date, mileage FROM maintenance WHERE task = ? ORDER BY id DESC",
            (task["task"],),
        )
        records = cursor.fetchall()
        conn.close()

        self.history_window = tk.Toplevel(self.root)
        self.history_window.title(f"{task['task']} History")

        self.history_scroll_frame = ScrollableFrame(self.history_window)
        self.history_scroll_frame.pack(fill="both", expand=True)

        for record in records:
            record_frame = tk.Frame(self.history_scroll_frame.scrollable_frame)
            record_frame.pack(fill=tk.X)

            date_entry = tk.Entry(record_frame, width=10)
            date_entry.insert(0, record[1])
            date_entry.pack(side=tk.LEFT, padx=5, pady=5)

            mileage_entry = tk.Entry(record_frame, width=10)
            mileage_entry.insert(0, record[2])
            mileage_entry.pack(side=tk.LEFT, padx=5, pady=5)

            save_button = tk.Button(
                record_frame,
                text="Save",
                command=lambda rid=record[
                    0
                ], de=date_entry, me=mileage_entry: self.save_record(
                    rid, de.get(), me.get()
                ),
            )
            save_button.pack(side=tk.LEFT, padx=5, pady=5)

            delete_button = tk.Button(
                record_frame,
                text="Delete",
                command=lambda rid=record[0], rf=record_frame: self.delete_record(
                    rid, rf
                ),
            )
            delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.set_window_size(self.history_window, self.history_scroll_frame)

    def save_record(self, record_id, date, mileage):
        """
        Saves the updated record to the database.

        Args:
            record_id (int): The ID of the record to update.
            date (str): The updated date.
            mileage (str): The updated mileage.
        """
        try:
            mileage = int(mileage)
            conn = sqlite3.connect("car_maintenance.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE maintenance SET date = ?, mileage = ? WHERE id = ?",
                (date, mileage, record_id),
            )
            conn.commit()
            conn.close()
            self.update_task_status()
            self.set_window_size(self.history_window, self.history_scroll_frame)
        except ValueError:
            messagebox.showerror("Error", "Invalid mileage input")

    def delete_record(self, record_id, frame):
        """
        Deletes a record from the database.

        Args:
            record_id (int): The ID of the record to delete.
            frame (tk.Frame): The frame containing the record's widgets.
        """
        conn = sqlite3.connect("car_maintenance.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()
        frame.destroy()
        self.update_task_status()
        self.set_window_size(self.history_window, self.history_scroll_frame)

    def set_window_size(self, window, scroll_frame, header_size=0):
        """
        Sets the window size based on the content or display height.

        Args:
            window (tk.Toplevel): The window to resize.
            scroll_frame (ScrollableFrame): The scrollable frame within the window.
        """
        window.update_idletasks()
        screen_height = window.winfo_screenheight()
        window_height = scroll_frame.scrollable_frame.winfo_reqheight() + header_size
        height = min(screen_height, window_height)
        window.geometry(f"{window.winfo_width()}x{height}")


if __name__ == "__main__":
    root = tk.Tk()
    app = CarMaintenanceApp(root)
    root.mainloop()
