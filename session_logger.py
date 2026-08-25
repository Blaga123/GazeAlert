"""
Automatic Session Logger & SQLite History for GazeAlert.
Saves every completed study session to local JSON and SQLite database.
"""

import json
import os
import sqlite3
import time
from typing import Any, Dict, List

def _get_writable_dir() -> str:
    try:
        local_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(local_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("1")
        os.remove(test_file)
        return local_dir
    except Exception:
        appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        target = os.path.join(appdata, "GazeAlert")
        os.makedirs(target, exist_ok=True)
        return target

DB_PATH = os.path.join(_get_writable_dir(), "study_history.db")
JSON_PATH = os.path.join(_get_writable_dir(), "study_history.json")


class SessionLogger:
    """Logs and persists study session metrics across days and restarts."""
    def __init__(self):
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        date_str TEXT,
                        total_minutes REAL,
                        pure_focus_minutes REAL,
                        distraction_minutes REAL,
                        efficiency_pct INTEGER,
                        phone_count INTEGER,
                        yawn_count INTEGER,
                        grade TEXT
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[!] Info: SQLite init: {e}")

    def save_session(
        self,
        total_seconds: float,
        pure_focus_seconds: float,
        distraction_seconds: float,
        efficiency_pct: int,
        phone_count: int,
        yawn_count: int,
        grade: str = "A+"
    ):
        now = time.time()
        date_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
        tot_min = round(total_seconds / 60.0, 2)
        foc_min = round(pure_focus_seconds / 60.0, 2)
        dis_min = round(distraction_seconds / 60.0, 2)

        record = {
            "timestamp": now,
            "date": date_str,
            "total_minutes": tot_min,
            "pure_focus_minutes": foc_min,
            "distraction_minutes": dis_min,
            "efficiency_pct": efficiency_pct,
            "phone_distractions_count": phone_count,
            "yawn_count": yawn_count,
            "grade": grade
        }

        # 1. Append to JSON log
        try:
            history: List[Dict[str, Any]] = []
            if os.path.exists(JSON_PATH):
                try:
                    with open(JSON_PATH, "r", encoding="utf-8") as f:
                        history = json.load(f)
                except Exception:
                    history = []
            history.append(record)
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            print(f"[+] Sesiune salvata automat in {JSON_PATH}")
        except Exception as e:
            print(f"[!] Eroare salvare JSON log: {e}")

        # 2. Insert into SQLite
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        timestamp, date_str, total_minutes, pure_focus_minutes,
                        distraction_minutes, efficiency_pct, phone_count, yawn_count, grade
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (now, date_str, tot_min, foc_min, dis_min, efficiency_pct, phone_count, yawn_count, grade))
                conn.commit()
            print(f"[+] Sesiune salvata in baza de date SQLite ({DB_PATH})")
        except Exception as e:
            print(f"[!] Eroare salvare SQLite: {e}")

    def export_to_csv(self, filepath: str = "study_sessions.csv") -> str:
        """Export all historical study sessions to a clean CSV spreadsheet."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date_str, total_minutes, pure_focus_minutes, distraction_minutes,
                           efficiency_pct, phone_count, yawn_count, grade
                    FROM sessions ORDER BY id ASC
                """)
                rows = cursor.fetchall()

            full_path = os.path.abspath(filepath)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write("Data si Ora,Timp Total (min),Focus Pur (min),Timp Distras (min),Eficienta (%),Distrageri Telefon,Cascat (Oboseala),Calificativ\n")
                for r in rows:
                    f.write(f'"{r[0]}",{r[1]},{r[2]},{r[3]},{r[4]},{r[5]},{r[6]},"{r[7]}"\n')
            print(f"[+] Export CSV realizat cu succes: {full_path}")
            return full_path
        except Exception as e:
            print(f"[!] Eroare la export CSV: {e}")
            return ""

    def export_to_json(self, filepath: str = "study_sessions.json") -> str:
        """Export all historical sessions to structured JSON."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, date_str, total_minutes, pure_focus_minutes,
                           distraction_minutes, efficiency_pct, phone_count, yawn_count, grade
                    FROM sessions ORDER BY id ASC
                """)
                rows = cursor.fetchall()

            records = []
            for r in rows:
                records.append({
                    "session_id": r[0],
                    "timestamp": r[1],
                    "date": r[2],
                    "total_minutes": r[3],
                    "pure_focus_minutes": r[4],
                    "distraction_minutes": r[5],
                    "efficiency_pct": r[6],
                    "phone_distractions": r[7],
                    "yawn_count": r[8],
                    "grade": r[9]
                })

            full_path = os.path.abspath(filepath)
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
            print(f"[+] Export JSON realizat cu succes: {full_path}")
            return full_path
        except Exception as e:
            print(f"[!] Eroare la export JSON: {e}")
            return ""
