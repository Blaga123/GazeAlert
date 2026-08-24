"""
Modern Frameless Floating Desktop Widget for GazeAlert.
Provides a sleek, borderless, semi-transparent, drag-and-drop Always-on-Top pill widget.
Requires 0 external dependencies (uses native tkinter + Windows DWM).
"""

import threading
import time
import tkinter as tk
from typing import Callable, Optional


class FloatingPillWidget:
    """True frameless floating Windows desktop widget with drag-and-drop."""
    def __init__(
        self,
        on_calibrate: Optional[Callable[[], None]] = None,
        on_toggle_pomodoro: Optional[Callable[[], None]] = None,
        on_toggle_sound: Optional[Callable[[], None]] = None,
        on_open_report: Optional[Callable[[], None]] = None,
        on_exit: Optional[Callable[[], None]] = None,
    ):
        self.on_calibrate = on_calibrate
        self.on_toggle_pomodoro = on_toggle_pomodoro
        self.on_toggle_sound = on_toggle_sound
        self.on_open_report = on_open_report
        self.on_exit = on_exit

        self.root: Optional[tk.Tk] = None
        self.is_visible = False
        self.is_running = True
        self._thread: Optional[threading.Thread] = None

        # Data variables
        self._state_text = "FOCUS (100%)"
        self._sub_text = "Pomodoro: 25:00"
        self._orb_color = "#00FF78"
        self._progress_pct = 100

        # UI elements
        self.canvas: Optional[tk.Canvas] = None
        self.orb_item = None
        self.title_item = None
        self.sub_item = None
        self.bar_bg = None
        self.bar_fill = None

        self._drag_start_x = 0
        self._drag_start_y = 0

    def start(self):
        """Start widget thread."""
        self._thread = threading.Thread(target=self._run_tk, daemon=True)
        self._thread.start()

    def _run_tk(self):
        self.root = tk.Tk()
        self.root.title("GazeAlert Widget")
        self.root.overrideredirect(True)      # Remove standard Windows border/titlebar
        self.root.attributes("-topmost", True)  # Always on top
        self.root.attributes("-alpha", 0.92)    # Modern glass opacity

        w, h = 340, 68
        screen_w = self.root.winfo_screenwidth()
        x = screen_w - w - 40
        y = 40
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.configure(bg="#11141a")

        # Drag and Drop bindings
        self.root.bind("<ButtonPress-1>", self._on_drag_start)
        self.root.bind("<B1-Motion>", self._on_drag_motion)
        self.root.bind("<Button-3>", self._show_context_menu)

        # Drawing Canvas
        self.canvas = tk.Canvas(self.root, width=w, height=h, bg="#11141a", highlightthickness=1, highlightbackground="#2d3748")
        self.canvas.pack(fill="both", expand=True)

        # Draw Glowing Orb
        self.orb_item = self.canvas.create_oval(14, 18, 44, 48, fill=self._orb_color, outline="#ffffff", width=1)

        # Text Items
        self.title_item = self.canvas.create_text(56, 24, text=self._state_text, fill="#ffffff", font=("Segoe UI", 10, "bold"), anchor="w")
        self.sub_item = self.canvas.create_text(56, 44, text=self._sub_text, fill="#00dcff", font=("Segoe UI", 8), anchor="w")

        # Progress bar
        self.bar_bg = self.canvas.create_line(56, 56, 320, 56, fill="#242b35", width=3)
        self.bar_fill = self.canvas.create_line(56, 56, 320, 56, fill="#00ff78", width=3)

        # Context Menu
        self.menu = tk.Menu(self.root, tearoff=0, bg="#1a202c", fg="#ffffff", activebackground="#2b6cb0")
        self.menu.add_command(label="🎯 Calibreaza Centru (C)", command=lambda: self.on_calibrate() if self.on_calibrate else None)
        self.menu.add_command(label="⏱️ Toggle Pomodoro (P)", command=lambda: self.on_toggle_pomodoro() if self.on_toggle_pomodoro else None)
        self.menu.add_command(label="🔔 Toggle Sunet (S)", command=lambda: self.on_toggle_sound() if self.on_toggle_sound else None)
        self.menu.add_separator()
        self.menu.add_command(label="📊 Deschide Raport", command=lambda: self.on_open_report() if self.on_open_report else None)
        self.menu.add_command(label="❌ Ascunde Widget", command=self.hide)

        # Hide initially until user activates it
        self.root.withdraw()
        self.root.mainloop()

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        if self.root:
            deltax = event.x - self._drag_start_x
            deltay = event.y - self._drag_start_y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        if self.menu:
            self.menu.post(event.x_root, event.y_root)

    def show(self):
        self.is_visible = True
        if self.root:
            self.root.after(0, self.root.deiconify)

    def hide(self):
        self.is_visible = False
        if self.root:
            self.root.after(0, self.root.withdraw)

    def toggle(self) -> bool:
        if self.is_visible:
            self.hide()
        else:
            self.show()
        return self.is_visible

    def update_metrics(self, title: str, sub: str, orb_hex: str, progress_pct: float):
        """Update metrics thread-safely in Tkinter canvas."""
        if not self.is_visible or not self.root or not self.canvas:
            return

        def _update():
            try:
                self.canvas.itemconfig(self.title_item, text=title)
                self.canvas.itemconfig(self.sub_item, text=sub)
                self.canvas.itemconfig(self.orb_item, fill=orb_hex)
                
                # Update bar width
                bar_len = int(56 + (320 - 56) * max(0.0, min(1.0, progress_pct / 100.0)))
                self.canvas.coords(self.bar_fill, 56, 56, bar_len, 56)
                self.canvas.itemconfig(self.bar_fill, fill=orb_hex)
            except Exception:
                pass

        try:
            self.root.after(0, _update)
        except Exception:
            pass

    def stop(self):
        self.is_running = False
        if self.root:
            try:
                self.root.after(0, self.root.quit)
            except Exception:
                pass
