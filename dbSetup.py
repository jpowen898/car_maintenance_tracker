#!/bin/python3
import sqlite3


def setup_database():
    conn = sqlite3.connect("car_maintenance.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            date TEXT NOT NULL,
            mileage INTEGER NOT NULL
        )
    """
    )
    conn.commit()
    conn.close()


setup_database()
