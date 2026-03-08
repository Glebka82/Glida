import tkinter as tk
from tkinter import ttk
import math
import json
import os
from datetime import datetime
import sys
import subprocess
import operations

# ──────────────────────────────────────────────────────────────────────────────
# Color Palette (matching the design)
# ──────────────────────────────────────────────────────────────────────────────
DARK_BG = "#2d3436"
DARK_BG_LIGHTER = "#3d4446"
TEAL = "#3daa98"
TEAL_LIGHT = "#4dbfab"
TEAL_DARK = "#2e8a7a"
TEAL_BG = "#5bbfab"
WHITE = "#ffffff"
LIGHT_GRAY = "#c8d6d3"
OVERLAY_BG = "#2a2e30"
FOOTER_BG = "#232829"
TOGGLE_ON = "#3daa98"
TOGGLE_OFF = "#6b7578"


# ──────────────────────────────────────────────────────────────────────────────
# Helper: Rounded Rectangle on Canvas
# ──────────────────────────────────────────────────────────────────────────────
def rounded_rect(canvas, x1, y1, x2, y2, radius=20, **kwargs):
    """Draw a rounded rectangle on a Canvas widget."""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1, x2, y1, x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius, x2, y2, x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2, x1, y2, x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius, x1, y1, x1 + radius, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Custom Toggle Switch Widget
# ──────────────────────────────────────────────────────────────────────────────
class ToggleSwitch:
    """A custom on/off toggle switch drawn on a Canvas."""

    def __init__(self, parent, label_text, initial=False, bg=DARK_BG_LIGHTER):
        self.state = initial
        self.bg = bg

        # Container frame
        self.frame = tk.Frame(parent, bg=bg)

        # Canvas for the toggle pill
        self.canvas = tk.Canvas(self.frame, width=50, height=26,
                                bg=bg, highlightthickness=0)
        self.canvas.pack(side="left", padx=(0, 10))

        # Label text
        self.label = tk.Label(self.frame, text=label_text,
                              font=("Arial", 13), fg=WHITE, bg=bg)
        self.label.pack(side="left")

        self._draw()

        # Bind click events
        self.canvas.bind("<Button-1>", self._toggle)
        self.label.bind("<Button-1>", self._toggle)
        self.canvas.config(cursor="hand2")
        self.label.config(cursor="hand2")

    def _draw(self):
        """Redraw the toggle in its current state."""
        self.canvas.delete("all")
        color = TOGGLE_ON if self.state else TOGGLE_OFF

        # Pill background
        rounded_rect(self.canvas, 2, 3, 48, 23, radius=10,
                     fill=color, outline="")

        # Circular knob
        if self.state:
            # ON: knob on the LEFT (Hebrew RTL convention)
            self.canvas.create_oval(5, 5, 21, 21, fill=WHITE, outline="")
        else:
            # OFF: knob on the RIGHT
            self.canvas.create_oval(29, 5, 45, 21, fill=WHITE, outline="")

    def _toggle(self, event=None):
        """Toggle between ON and OFF."""
        self.state = not self.state
        self._draw()

    def get(self):
        """Return the current toggle state (True=ON, False=OFF)."""
        return self.state


# ──────────────────────────────────────────────────────────────────────────────
# Main Application Class
# ──────────────────────────────────────────────────────────────────────────────
class IceCreamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("גלידה גנרית")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        self.root.configure(bg=DARK_BG)

        # Track state
        self.active_tab = "build"
        self.is_loading = False
        self.spinner_angle = 0
        self.spinner_job = None
        self.progress_value = 0
        self.progress_job = None
        self.selected_flavor = ""
        self.overlay = None
        self.dot_anim_job = None
        self.success_canvas = None

        # Build the UI
        self._build_main_ui()

    # ──────────────────────────────────────────────────────────────────────
    # Build the Main UI
    # ──────────────────────────────────────────────────────────────────────
    def _build_main_ui(self):
        """Construct the entire main window layout."""

        # ── Footer (pack first so it stays at bottom) ──
        self._build_footer()

        # ── Outer frame (dark background with subtle border effect) ──
        self.outer_frame = tk.Frame(self.root, bg=DARK_BG)
        self.outer_frame.pack(fill="both", expand=True, padx=8, pady=8)

        # ── Inner panel (slightly lighter, simulates the card look) ──
        self.inner_frame = tk.Frame(self.outer_frame, bg=DARK_BG_LIGHTER,
                                     highlightbackground="#4a5557",
                                     highlightthickness=1)
        self.inner_frame.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Header Area ──
        self._build_header()

        # ── Content Area ──
        self.content_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Bottom buttons area (used by config screen) ──
        self.bottom_buttons_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER)

        # Show flavor selection by default
        self._show_flavor_selection()

    def _build_header(self):
        """Build the title header with ice cream emojis."""
        self.header_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER, pady=20)
        self.header_frame.pack(fill="x")

        self.title_label = tk.Label(
            self.header_frame,
            text="\U0001F366  גלידה גנרית  \U0001F366",
            font=("Arial", 28, "bold"),
            fg=WHITE,
            bg=DARK_BG_LIGHTER
        )
        self.title_label.pack()

    def _build_footer(self):
        """Build the footer bar with version text."""
        self.footer = tk.Frame(self.root, bg=FOOTER_BG, height=35)
        self.footer.pack(fill="x", side="bottom")
        self.footer.pack_propagate(False)

        self.footer_label = tk.Label(
            self.footer,
            text="גרסה 1.0 - גלידה גנרית",
            font=("Arial", 10),
            fg=LIGHT_GRAY,
            bg=FOOTER_BG
        )
        self.footer_label.pack(expand=True)

    # ──────────────────────────────────────────────────────────────────────
    # Screen 1: Flavor Selection
    # ──────────────────────────────────────────────────────────────────────
    def _show_flavor_selection(self):
        """Show the main flavor selection screen."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        self.bottom_buttons_frame.pack_forget()

        # Destroy old tabs if they exist
        if hasattr(self, "tab_frame_widget") and self.tab_frame_widget.winfo_exists():
            self.tab_frame_widget.destroy()

        # Reset footer
        self.footer_label.config(text="גרסה 1.0 - גלידה גנרית")

        # Build tabs
        self._build_tabs()

        # Section title
        section_label = tk.Label(
            self.content_frame,
            text="בחירת טעמים",
            font=("Arial", 18, "bold"),
            fg=WHITE,
            bg=DARK_BG_LIGHTER
        )
        section_label.pack(pady=(10, 30))

        # Flavor buttons in 2x2 grid
        flavors_frame = tk.Frame(self.content_frame, bg=DARK_BG_LIGHTER)
        flavors_frame.pack(expand=True)

        flavors = [
            ("שוקולד", 0, 1),
            ("Disk", 0, 0),
            ("תות", 1, 1),
            ("בננה", 1, 0),
        ]

        for flavor_name, row, col in flavors:
            btn_canvas = self._create_flavor_button(flavors_frame, flavor_name)
            btn_canvas.grid(row=row, column=col, padx=8, pady=8)

    def _build_tabs(self):
        """Build the two tab buttons: Build Ice Cream / Disassemble Ice Cream."""
        self.tab_frame_widget = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER)
        self.tab_frame_widget.pack(after=self.header_frame, pady=(0, 10))

        self.tab_canvas = tk.Canvas(self.tab_frame_widget, width=380, height=45,
                                     bg=DARK_BG_LIGHTER, highlightthickness=0)
        self.tab_canvas.pack()

        # Background pill
        rounded_rect(self.tab_canvas, 0, 0, 380, 45, radius=22,
                      fill=TEAL_DARK, outline="")

        # "פירוק גלידה" (Disassemble) - RIGHT side
        self.tab_disassemble_bg = rounded_rect(
            self.tab_canvas, 195, 3, 377, 42, radius=20,
            fill=TEAL_DARK, outline="")
        self.tab_disassemble_text = self.tab_canvas.create_text(
            286, 22, text="פירוק גלידה",
            font=("Arial", 13, "bold"), fill=WHITE)

        # "בניית גלידה" (Build) - LEFT side
        self.tab_build_bg = rounded_rect(
            self.tab_canvas, 3, 3, 195, 42, radius=20,
            fill=TEAL_LIGHT, outline="")
        self.tab_build_text = self.tab_canvas.create_text(
            99, 22, text="בניית גלידה",
            font=("Arial", 13, "bold"), fill=WHITE)

        # Bind click events
        for item in [self.tab_build_bg, self.tab_build_text]:
            self.tab_canvas.tag_bind(item, "<Button-1>",
                                      lambda e: self._switch_tab("build"))
        for item in [self.tab_disassemble_bg, self.tab_disassemble_text]:
            self.tab_canvas.tag_bind(item, "<Button-1>",
                                      lambda e: self._switch_tab("disassemble"))

    def _switch_tab(self, tab_name):
        """Switch between Build and Disassemble tabs."""
        if self.is_loading:
            return
        self.active_tab = tab_name

        if tab_name == "build":
            self.tab_canvas.itemconfig(self.tab_build_bg, fill=TEAL_LIGHT)
            self.tab_canvas.itemconfig(self.tab_disassemble_bg, fill=TEAL_DARK)
            self._show_flavor_content()
        else:
            self.tab_canvas.itemconfig(self.tab_build_bg, fill=TEAL_DARK)
            self.tab_canvas.itemconfig(self.tab_disassemble_bg, fill=TEAL_LIGHT)
            self._show_disassemble_tab()

    def _show_flavor_content(self):
        """Re-show flavor buttons when switching back to Build tab."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        section_label = tk.Label(
            self.content_frame, text="בחירת טעמים",
            font=("Arial", 18, "bold"), fg=WHITE, bg=DARK_BG_LIGHTER)
        section_label.pack(pady=(10, 30))

        flavors_frame = tk.Frame(self.content_frame, bg=DARK_BG_LIGHTER)
        flavors_frame.pack(expand=True)

        flavors = [
            ("שוקולד", 0, 1), ("Disk", 0, 0),
            ("תות", 1, 1), ("בננה", 1, 0),
        ]
        for flavor_name, row, col in flavors:
            btn_canvas = self._create_flavor_button(flavors_frame, flavor_name)
            btn_canvas.grid(row=row, column=col, padx=8, pady=8)

    def _create_flavor_button(self, parent, text):
        """Create a single teal rounded flavor button with an arrow icon."""
        width, height = 240, 55
        canvas = tk.Canvas(parent, width=width, height=height,
                           bg=DARK_BG_LIGHTER, highlightthickness=0)

        # Shadow
        rounded_rect(canvas, 2, 3, width - 2, height - 1, radius=26,
                      fill=TEAL_DARK, outline="")
        # Body
        btn_bg = rounded_rect(canvas, 2, 2, width - 2, height - 4, radius=26,
                               fill=TEAL, outline="")
        # Text
        canvas.create_text(width // 2 + 15, height // 2 - 1, text=text,
                           font=("Arial", 15, "bold"), fill=WHITE)
        # Arrow icon
        canvas.create_text(35, height // 2 - 1, text="\u23ce",
                           font=("Arial", 16), fill=TEAL_DARK)

        def on_enter(e):
            canvas.itemconfig(btn_bg, fill=TEAL_LIGHT)

        def on_leave(e):
            canvas.itemconfig(btn_bg, fill=TEAL)

        def on_click(e):
            platform = text
            # self._start_making_ice_cream(text)
            drive_name = operations.get_first_user_from_disk(platform)
            print(drive_name)
            target_drive = operations.find_drive_from_ui_string(drive_name)

            if target_drive:
                print(f"🚀 Ready to send {target_drive} to the flashing function!")
            # subprocess.run([sys.executable, "backup.py"])


        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        canvas.config(cursor="hand2")
        return canvas

    def _show_disassemble_tab(self):
        """Show the 'Disassemble Ice Cream' tab (placeholder)."""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        label = tk.Label(
            self.content_frame,
            text="פירוק גלידה\n(בקרוב...)",
            font=("Arial", 18, "bold"),
            fg=LIGHT_GRAY,
            bg=DARK_BG_LIGHTER
        )
        label.pack(expand=True)

    # ──────────────────────────────────────────────────────────────────────
    # Screen 2: Loading Overlay
    # ──────────────────────────────────────────────────────────────────────
    def _start_making_ice_cream(self, flavor):
        """Show the loading overlay when a flavor is selected."""
        if self.is_loading:
            return
        self.is_loading = True
        self.selected_flavor = flavor
        self.progress_value = 0

        # Change background to teal
        self.inner_frame.configure(bg=TEAL_BG)
        self.header_frame.configure(bg=TEAL_BG)
        self.title_label.configure(bg=TEAL_BG)
        self.content_frame.configure(bg=TEAL_BG)

        # Create dark overlay
        self.overlay = tk.Frame(self.root, bg=OVERLAY_BG)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center",
                           width=350, height=320)

        self.overlay_canvas = tk.Canvas(self.overlay, width=350, height=320,
                                         bg=OVERLAY_BG, highlightthickness=0)
        self.overlay_canvas.pack(fill="both", expand=True)

        # Background rounded rectangle
        rounded_rect(self.overlay_canvas, 0, 0, 350, 320, radius=20,
                      fill=OVERLAY_BG, outline="#3a3e40")

        # ── Spinner (circle of dots) ──
        self.spinner_dots = []
        cx, cy = 175, 90
        num_dots, dot_radius, circle_radius = 12, 6, 40

        for i in range(num_dots):
            angle = math.radians(i * (360 / num_dots) - 90)
            x = cx + circle_radius * math.cos(angle)
            y = cy + circle_radius * math.sin(angle)
            dot = self.overlay_canvas.create_oval(
                x - dot_radius, y - dot_radius,
                x + dot_radius, y + dot_radius,
                fill=TEAL_DARK, outline="")
            self.spinner_dots.append(dot)

        # Text: "הגלידה בהכנה"
        self.overlay_canvas.create_text(
            175, 165, text="הגלידה בהכנה",
            font=("Arial", 20, "bold"), fill=WHITE)

        # Subtext: "אנא המתן"
        self.overlay_canvas.create_text(
            175, 200, text="אנא המתן",
            font=("Arial", 14), fill=LIGHT_GRAY)

        # ── Progress Bar ──
        bar_x1, bar_y, bar_x2, bar_height = 100, 235, 250, 12

        rounded_rect(self.overlay_canvas, bar_x1, bar_y,
                      bar_x2, bar_y + bar_height, radius=6,
                      fill="#1a1e20", outline="")

        self.progress_bar = rounded_rect(
            self.overlay_canvas, bar_x1, bar_y,
            bar_x1 + 2, bar_y + bar_height, radius=6,
            fill=TEAL, outline="")
        self.progress_bar_x1 = bar_x1
        self.progress_bar_y = bar_y
        self.progress_bar_x2 = bar_x2
        self.progress_bar_h = bar_height

        # ── Cancel Button: "ביטול" ──
        cancel_bg = rounded_rect(self.overlay_canvas, 130, 265, 220, 300,
                                   radius=15, fill="#4a5055", outline="")
        cancel_text = self.overlay_canvas.create_text(
            175, 282, text="ביטול",
            font=("Arial", 12, "bold"), fill=WHITE)

        def cancel_enter(e):
            self.overlay_canvas.itemconfig(cancel_bg, fill="#5a6065")

        def cancel_leave(e):
            self.overlay_canvas.itemconfig(cancel_bg, fill="#4a5055")

        def cancel_click(e):
            self._cancel_loading()

        for item in [cancel_bg, cancel_text]:
            self.overlay_canvas.tag_bind(item, "<Enter>", cancel_enter)
            self.overlay_canvas.tag_bind(item, "<Leave>", cancel_leave)
            self.overlay_canvas.tag_bind(item, "<Button-1>", cancel_click)

        # Start animations
        self._animate_spinner()
        self._animate_progress()

    def _animate_spinner(self):
        """Animate the circular spinner by cycling dot colors."""
        if not self.is_loading:
            return

        num_dots = len(self.spinner_dots)
        trail_length = 4

        for i in range(num_dots):
            distance = (self.spinner_angle - i) % num_dots
            if distance < trail_length:
                brightness = 1.0 - (distance / trail_length)
                r = int(61 + brightness * (77 - 61))
                g = int(78 + brightness * (191 - 78))
                b = int(74 + brightness * (171 - 74))
                color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                color = "#3a4e4a"
            self.overlay_canvas.itemconfig(self.spinner_dots[i], fill=color)

        self.spinner_angle = (self.spinner_angle + 1) % num_dots
        self.spinner_job = self.root.after(100, self._animate_spinner)

    def _animate_progress(self):
        """Animate the progress bar from 0% to 100%."""
        if not self.is_loading:
            return

        self.progress_value += 1
        if self.progress_value > 100:
            self._finish_loading()
            return

        bar_width = self.progress_bar_x2 - self.progress_bar_x1
        fill_width = max(2, int(bar_width * (self.progress_value / 100)))
        self.overlay_canvas.delete(self.progress_bar)
        self.progress_bar = rounded_rect(
            self.overlay_canvas, self.progress_bar_x1, self.progress_bar_y,
            self.progress_bar_x1 + fill_width,
            self.progress_bar_y + self.progress_bar_h,
            radius=6, fill=TEAL, outline="")
        self.progress_job = self.root.after(50, self._animate_progress)

    def _finish_loading(self):
        """Called when loading completes. Transition to config screen."""
        self._stop_animations()
        self.is_loading = False

        if self.overlay:
            self.overlay.place_forget()
            self.overlay.destroy()
            self.overlay = None

        self._restore_bg()

        # Remove tabs before showing config
        if hasattr(self, "tab_frame_widget") and self.tab_frame_widget.winfo_exists():
            self.tab_frame_widget.destroy()

        self._show_config_screen()

    def _cancel_loading(self):
        """Cancel the loading process and return to flavor selection."""
        self._stop_animations()
        self.is_loading = False

        if self.overlay:
            self.overlay.place_forget()
            self.overlay.destroy()
            self.overlay = None

        self._restore_bg()
        self._show_flavor_selection()

    def _stop_animations(self):
        """Cancel all running after() animation jobs."""
        if self.spinner_job:
            self.root.after_cancel(self.spinner_job)
            self.spinner_job = None
        if self.progress_job:
            self.root.after_cancel(self.progress_job)
            self.progress_job = None
        if self.dot_anim_job:
            self.root.after_cancel(self.dot_anim_job)
            self.dot_anim_job = None

    def _restore_bg(self):
        """Restore background colors after loading overlay is removed."""
        self.inner_frame.configure(bg=DARK_BG_LIGHTER)
        self.header_frame.configure(bg=DARK_BG_LIGHTER)
        self.title_label.configure(bg=DARK_BG_LIGHTER)
        self.content_frame.configure(bg=DARK_BG_LIGHTER)

    # ──────────────────────────────────────────────────────────────────────
    # Screen 3: Configuration Screen
    # ──────────────────────────────────────────────────────────────────────
    def _show_config_screen(self):
        """Show the ice cream configuration screen with dropdowns, spinbox, and toggles."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Configure ttk style for teal comboboxes
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Teal.TCombobox",
                        fieldbackground=TEAL_DARK, background=TEAL,
                        foreground=WHITE, borderwidth=1, arrowcolor=WHITE,
                        padding=6)
        style.map("Teal.TCombobox",
                  fieldbackground=[("readonly", TEAL_DARK)],
                  foreground=[("readonly", WHITE)],
                  selectbackground=[("readonly", TEAL_DARK)],
                  selectforeground=[("readonly", WHITE)])

        # ── Controls row (RTL: right-to-left) ──
        controls_row = tk.Frame(self.content_frame, bg=DARK_BG_LIGHTER)
        controls_row.pack(fill="x", pady=(10, 0), padx=10)

        # Use grid for precise 3-column layout
        controls_row.columnconfigure(0, weight=1)  # Left: אימון גלידה
        controls_row.columnconfigure(1, weight=1)  # Center: Spinbox
        controls_row.columnconfigure(2, weight=1)  # Right: גרסאות גלידה

        # RIGHT column: "גרסאות גלידה" (Ice Cream Versions)
        ver_frame = tk.Frame(controls_row, bg=DARK_BG_LIGHTER)
        ver_frame.grid(row=0, column=2, padx=5, sticky="e")
        self.version_var = tk.StringVar(value="גרסאות גלידה")
        version_dropdown = ttk.Combobox(
            ver_frame, textvariable=self.version_var,
            values=["גרסה 1", "גרסה 2", "גרסה 3"],
            state="readonly", style="Teal.TCombobox",
            font=("Arial", 12), width=14)
        version_dropdown.pack()
        tk.Label(ver_frame, text="בחירת גרסת גלידה",
                 font=("Arial", 9), fg=LIGHT_GRAY,
                 bg=DARK_BG_LIGHTER).pack(pady=(2, 0))

        # CENTER column: Spinbox for number of scoops
        spin_frame = tk.Frame(controls_row, bg=DARK_BG_LIGHTER)
        spin_frame.grid(row=0, column=1, padx=5)
        spinbox_border = tk.Frame(spin_frame, bg=TEAL, padx=2, pady=2)
        spinbox_border.pack()
        self.scoops_var = tk.IntVar(value=0)
        scoops_spinbox = tk.Spinbox(
            spinbox_border, from_=0, to=10,
            textvariable=self.scoops_var,
            font=("Arial", 16, "bold"), width=3, justify="center",
            bg=TEAL_DARK, fg=WHITE, buttonbackground=TEAL,
            insertbackground=WHITE, highlightthickness=0, relief="flat")
        scoops_spinbox.pack()
        tk.Label(spin_frame, text="מספר כדורים",
                 font=("Arial", 9), fg=LIGHT_GRAY,
                 bg=DARK_BG_LIGHTER).pack(pady=(2, 0))

        # LEFT column: "אימון גלידה" (Ice Cream Training)
        train_frame = tk.Frame(controls_row, bg=DARK_BG_LIGHTER)
        train_frame.grid(row=0, column=0, padx=5, sticky="w")
        self.training_var = tk.StringVar(value="אימון גלידה")
        training_dropdown = ttk.Combobox(
            train_frame, textvariable=self.training_var,
            values=["אימון 1", "אימון 2", "אימון 3"],
            state="readonly", style="Teal.TCombobox",
            font=("Arial", 12), width=14)
        training_dropdown.pack()
        tk.Label(train_frame, text="בחירת אימון גלידה",
                 font=("Arial", 9), fg=LIGHT_GRAY,
                 bg=DARK_BG_LIGHTER).pack(pady=(2, 0))

        # ── Label: "מספר כדורי גלידה" (Number of Ice Cream Scoops) ──
        scoops_label = tk.Label(
            self.content_frame,
            text="מספר כדורי גלידה",
            font=("Arial", 13),
            fg=LIGHT_GRAY,
            bg=DARK_BG_LIGHTER
        )
        scoops_label.pack(pady=(8, 12))

        # ── Separator line ──
        sep = tk.Frame(self.content_frame, bg="#4a5557", height=1)
        sep.pack(fill="x", padx=30, pady=(0, 10))

        # ── Section title: "קונפיגורציות גלידה" (Ice Cream Configurations) ──
        config_title = tk.Label(
            self.content_frame,
            text="קונפיגורציות גלידה",
            font=("Arial", 20, "bold"),
            fg=WHITE,
            bg=DARK_BG_LIGHTER
        )
        config_title.pack(pady=(5, 12))

        # ── Toggle Switches ──
        toggles_frame = tk.Frame(self.content_frame, bg=DARK_BG_LIGHTER)
        toggles_frame.pack()

        self.toggles = {}
        toggle_items = [
            ("פצפוצי שוקולד", True,  "הוספת פצפוצי שוקולד על הגלידה"),
            ("פצפוצי וניל", True,   "הוספת פצפוצי וניל על הגלידה"),
            ("מקופלת", False,        "הוספת חתיכות מקופלת"),
            ("קורנפלקס", True,      "הוספת קורנפלקס פריך"),
            ("תותים", False,         "הוספת תותים טריים"),
        ]

        for name, default_state, description in toggle_items:
            row_frame = tk.Frame(toggles_frame, bg=DARK_BG_LIGHTER)
            row_frame.pack(anchor="center", pady=5, fill="x")

            toggle = ToggleSwitch(row_frame, name,
                                  initial=default_state, bg=DARK_BG_LIGHTER)
            toggle.frame.pack(side="left", padx=(40, 0))

            # Description text on the right
            desc_label = tk.Label(row_frame, text=f"  -  {description}",
                                  font=("Arial", 10), fg="#8a9a96",
                                  bg=DARK_BG_LIGHTER)
            desc_label.pack(side="left", padx=(5, 0))

            self.toggles[name] = toggle

        # ── Bottom Buttons ──
        self.bottom_buttons_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER)
        self.bottom_buttons_frame.pack(fill="x", padx=15, pady=(12, 15))

        # Use grid for equal-width buttons
        self.bottom_buttons_frame.columnconfigure(0, weight=1)
        self.bottom_buttons_frame.columnconfigure(1, weight=1)

        # "סיום" (Done/Close) button - RIGHT side
        finish_canvas = tk.Canvas(self.bottom_buttons_frame, height=60,
                                  bg=DARK_BG_LIGHTER, highlightthickness=0)
        finish_canvas.grid(row=0, column=1, sticky="ew", padx=4)
        finish_canvas.update_idletasks()

        def _draw_finish_btn(event=None):
            finish_canvas.delete("all")
            w = finish_canvas.winfo_width() or 260
            rounded_rect(finish_canvas, 2, 3, w - 2, 58, radius=28,
                          fill=TEAL_DARK, outline="")
            self._finish_bg_id = rounded_rect(finish_canvas, 2, 2, w - 2, 56,
                                               radius=28, fill=TEAL, outline="")
            finish_canvas.create_text(w // 2, 28, text="סיום  ←",
                                      font=("Arial", 18, "bold"), fill=WHITE,
                                      tags="btn_text")

        finish_canvas.bind("<Configure>", _draw_finish_btn)

        def finish_enter(e):
            finish_canvas.itemconfig(self._finish_bg_id, fill=TEAL_LIGHT)

        def finish_leave(e):
            finish_canvas.itemconfig(self._finish_bg_id, fill=TEAL)

        def finish_click(e):
            self.bottom_buttons_frame.pack_forget()
            self._show_flavor_selection()

        finish_canvas.bind("<Enter>", finish_enter)
        finish_canvas.bind("<Leave>", finish_leave)
        finish_canvas.bind("<Button-1>", finish_click)
        finish_canvas.config(cursor="hand2")

        # "בצע הזמנה" (Place Order) button - LEFT side
        order_canvas = tk.Canvas(self.bottom_buttons_frame, height=60,
                                 bg=DARK_BG_LIGHTER, highlightthickness=0)
        order_canvas.grid(row=0, column=0, sticky="ew", padx=4)

        def _draw_order_btn(event=None):
            order_canvas.delete("all")
            w = order_canvas.winfo_width() or 260
            rounded_rect(order_canvas, 2, 3, w - 2, 58, radius=28,
                          fill=TEAL_DARK, outline="")
            self._order_bg_id = rounded_rect(order_canvas, 2, 2, w - 2, 56,
                                              radius=28, fill=TEAL, outline="")
            order_canvas.create_text(w // 2, 28, text="בצע הזמנה  ✓",
                                     font=("Arial", 18, "bold"), fill=WHITE,
                                     tags="btn_text")

        order_canvas.bind("<Configure>", _draw_order_btn)

        def order_enter(e):
            order_canvas.itemconfig(self._order_bg_id, fill=TEAL_LIGHT)

        def order_leave(e):
            order_canvas.itemconfig(self._order_bg_id, fill=TEAL)

        def order_click(e):
            self._save_order_to_json()
            self._show_order_success()

        order_canvas.bind("<Enter>", order_enter)
        order_canvas.bind("<Leave>", order_leave)
        order_canvas.bind("<Button-1>", order_click)
        order_canvas.config(cursor="hand2")

    def _save_order_to_json(self):
        """Save the current order configuration to a JSON file."""
        order_data = {
            "timestamp": datetime.now().isoformat(),
            "flavor": self.selected_flavor,
            "version": self.version_var.get(),
            "training": self.training_var.get(),
            "scoops": self.scoops_var.get(),
            "toppings": {}
        }

        for name, toggle in self.toggles.items():
            order_data["toppings"][name] = toggle.get()

        # Determine path: save next to the script file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(script_dir, "ice_cream_orders.json")

        # Load existing orders or start fresh
        orders = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    orders = json.load(f)
            except (json.JSONDecodeError, IOError):
                orders = []

        orders.append(order_data)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)

        self._last_json_path = json_path

    # ──────────────────────────────────────────────────────────────────────
    # Screen 4: Order Success Popup
    # ──────────────────────────────────────────────────────────────────────
    def _show_order_success(self):
        """Show the success popup with checkmark, animated dots, and progress bar."""

        # Update footer text
        self.footer_label.config(
            text="גלידה ע. ניתן לאסוף את הגלידה בדלפק.")

        # Create overlay
        self.overlay = tk.Frame(self.root, bg=OVERLAY_BG)
        self.overlay.place(relx=0.5, rely=0.45, anchor="center",
                           width=380, height=350)

        canvas = tk.Canvas(self.overlay, width=380, height=350,
                            bg=OVERLAY_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        self.success_canvas = canvas

        # Background
        rounded_rect(canvas, 0, 0, 380, 350, radius=20,
                      fill=OVERLAY_BG, outline="#3a3e40")

        # ── Checkmark Circle ──
        canvas.create_oval(155, 20, 225, 90, fill=TEAL, outline="#2e8a7a", width=3)
        canvas.create_oval(163, 28, 217, 82, fill=TEAL_LIGHT, outline="")
        canvas.create_text(190, 55, text="\u2713",
                           font=("Arial", 28, "bold"), fill=WHITE)

        # ── Success Text ──
        canvas.create_text(190, 120,
                           text="ההזמנה בוצעה בהצלחה",
                           font=("Arial", 18, "bold"), fill=WHITE)

        canvas.create_text(190, 155,
                           text=".ניתן לאסוף את הגלידה בדלפק",
                           font=("Arial", 12), fill=LIGHT_GRAY)

        # ── Animated Dots ──
        self.success_dots = []
        dot_y = 190
        for i in range(5):
            dot = canvas.create_oval(155 + i * 18, dot_y,
                                      165 + i * 18, dot_y + 10,
                                      fill=TEAL_DARK, outline="")
            self.success_dots.append(dot)

        self.success_dot_index = 0
        self._animate_success_dots()

        # ── Full Progress Bar (order complete) ──
        bar_x1, bar_y, bar_x2, bar_height = 90, 215, 290, 12
        rounded_rect(canvas, bar_x1, bar_y, bar_x2, bar_y + bar_height,
                      radius=6, fill="#1a1e20", outline="")
        rounded_rect(canvas, bar_x1, bar_y, bar_x2, bar_y + bar_height,
                      radius=6, fill=TEAL, outline="")

        # ── "אישור" (Confirm) Button ──
        confirm_bg = rounded_rect(canvas, 240, 260, 350, 305,
                                   radius=18, fill=TEAL, outline="")
        confirm_text = canvas.create_text(295, 282, text="אישור",
                                           font=("Arial", 14, "bold"), fill=WHITE)

        def confirm_enter(e):
            canvas.itemconfig(confirm_bg, fill=TEAL_LIGHT)

        def confirm_leave(e):
            canvas.itemconfig(confirm_bg, fill=TEAL)

        def confirm_click(e):
            self._stop_animations()
            self.success_canvas = None
            self.overlay.place_forget()
            self.overlay.destroy()
            self.overlay = None
            self.bottom_buttons_frame.pack_forget()
            self._show_flavor_selection()

        for item in [confirm_bg, confirm_text]:
            canvas.tag_bind(item, "<Enter>", confirm_enter)
            canvas.tag_bind(item, "<Leave>", confirm_leave)
            canvas.tag_bind(item, "<Button-1>", confirm_click)

    def _animate_success_dots(self):
        """Cycle through the 5 dots on the success popup."""
        if self.success_canvas is None:
            return
        try:
            for i, dot in enumerate(self.success_dots):
                if i == self.success_dot_index:
                    self.success_canvas.itemconfig(dot, fill=TEAL_LIGHT)
                elif i == (self.success_dot_index - 1) % len(self.success_dots):
                    self.success_canvas.itemconfig(dot, fill=TEAL)
                else:
                    self.success_canvas.itemconfig(dot, fill=TEAL_DARK)

            self.success_dot_index = (self.success_dot_index + 1) % len(self.success_dots)
            self.dot_anim_job = self.root.after(300, self._animate_success_dots)
        except tk.TclError:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Run the Application
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = IceCreamApp(root)
    root.mainloop()
