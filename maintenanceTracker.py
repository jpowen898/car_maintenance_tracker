#!/bin/python3
import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import sqlite3

FIRST_COLUMN_WIDTH = 20
COLUMN_WIDTH = 20

class CarMaintenanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Car Maintenance Tracker")
        self.load_config()
        self.create_widgets()
        self.update_task_status()

    def load_config(self):
        with open('config.json', 'r') as file:
            self.config = json.load(file)['maintenance_tasks']

    def create_widgets(self):
        baseframe = tk.Frame(self.root, padx=COLUMN_WIDTH, pady=COLUMN_WIDTH)
        baseframe.pack(fill=tk.X)

        self.current_mileage = tk.IntVar(value=115000)
        self.mileage_entry = ttk.Entry(baseframe, width=FIRST_COLUMN_WIDTH)
        self.mileage_entry.pack(side=tk.LEFT)
        self.mileage_entry.insert(0, str(self.current_mileage.get()))
        self.mileage_entry.bind("<Return>", lambda event: self.update_mileage())

        tk.Label(baseframe, text="Last done date:", width=COLUMN_WIDTH).pack(side=tk.LEFT)
        tk.Label(baseframe, text="Last done miles:", width=COLUMN_WIDTH).pack(side=tk.LEFT)
        tk.Label(baseframe, text="Next due miles:", width=COLUMN_WIDTH).pack(side=tk.LEFT)

        self.task_frames = []
        for task in self.config:
            frame = tk.Frame(self.root, padx=COLUMN_WIDTH, pady=5)
            frame.pack(fill=tk.X)
            tk.Label(frame, text=task['task'], width=FIRST_COLUMN_WIDTH).pack(side=tk.LEFT)
            self.create_task_status_widgets(frame, task)
            self.task_frames.append(frame)

    def create_task_status_widgets(self, frame, task):
        last_done_date_label = tk.Label(frame, text="N/A", width=COLUMN_WIDTH)
        last_done_miles_label = tk.Label(frame, text="N/A", width=COLUMN_WIDTH)
        last_done_date_label.pack(side=tk.LEFT)
        last_done_miles_label.pack(side=tk.LEFT)
        next_due_label = tk.Label(frame, text="N/A", width=COLUMN_WIDTH)
        next_due_label.pack(side=tk.LEFT)
        status_label = tk.Label(frame, text="Status", width=10)
        status_label.pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Mark as Done", command=lambda t=task: self.mark_as_done(t)).pack(side=tk.RIGHT)
        tk.Button(frame, text="View History", command=lambda t=task: self.view_history(t)).pack(side=tk.RIGHT)
        frame.last_done_date_label = last_done_date_label
        frame.last_done_miles_label = last_done_miles_label
        frame.next_due_label = next_due_label
        frame.status_label = status_label

    def mark_as_done(self, task):
        date = datetime.now().strftime("%Y-%m-%d")
        mileage = int(self.current_mileage.get())
        conn = sqlite3.connect('car_maintenance.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO maintenance (task, date, mileage) VALUES (?, ?, ?)', (task['task'], date, mileage))
        conn.commit()
        conn.close()
        self.update_task_status()

    def update_task_status(self):
        conn = sqlite3.connect('car_maintenance.db')
        cursor = conn.cursor()
        for frame, task in zip(self.task_frames, self.config):
            cursor.execute('SELECT date, mileage FROM maintenance WHERE task = ? ORDER BY id DESC LIMIT 1', (task['task'],))
            result = cursor.fetchone()
            if result:
                last_done_date, last_done_mileage = result
                frame.last_done_date_label.config(text=last_done_date)
                frame.last_done_miles_label.config(text=last_done_mileage)
                next_due_mileage = last_done_mileage + task['frequency_miles']
                frame.next_due_label.config(text=str(next_due_mileage))
                self.update_status_label(frame,  last_done_mileage, task)
            else:
                frame.last_done_date_label.config(text="N/A")
                frame.last_done_miles_label.config(text="0")
                last_done_mileage = 0
                next_due_mileage = last_done_mileage + task['frequency_miles']
                frame.next_due_label.config(text=str(next_due_mileage))
                self.update_status_label(frame,  last_done_mileage, task)
        conn.close()

    def update_status_label(self, frame, last_done_mileage, task):
        current_mileage = int(self.current_mileage.get())
        if current_mileage >= last_done_mileage + task['frequency_max_miles']:
            frame.status_label.config(text="ASAP", bg="red")
        elif current_mileage >= last_done_mileage + task['frequency_miles']:
            frame.status_label.config(text="Soon", bg="yellow")
        else:
            frame.status_label.config(text="OK", bg="green")

    def update_mileage(self):
        try:
            value = int(self.mileage_entry.get())
            self.current_mileage.set(value)
            self.mileage_entry.delete(0, tk.END)
            self.mileage_entry.insert(0, str(value))
            self.update_task_status()
        except ValueError:
            print("Invalid mileage input")

    def view_history(self, task):
        conn = sqlite3.connect('car_maintenance.db')
        cursor = conn.cursor()
        cursor.execute('SELECT date, mileage FROM maintenance WHERE task = ? ORDER BY id DESC', (task['task'],))
        records = cursor.fetchall()
        conn.close()

        history_window = tk.Toplevel(self.root)
        history_window.title(f"{task['task']} History")

        for record in records:
            tk.Label(history_window, text=f"Date: {record[0]}, Mileage: {record[1]}").pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = CarMaintenanceApp(root)
    root.mainloop()
