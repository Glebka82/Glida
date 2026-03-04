"""
גלידה גנרית - Generic Ice Cream GUI
=====================================
A Hebrew ice cream maker GUI built with Tkinter.

How to run in PyCharm:
  1. Create a new Python file (File > New > Python File)
  2. Paste this entire code into the file
  3. Right-click the file and select "Run"

Requires: Python 3.7+ (Tkinter is built-in, no extra installs needed)
"""

import tkinter as tk
import math
import subprocess
import sys

# ──────────────────────────────────────────────────────────────────────────────
# Color Palette (matching the design)
# ──────────────────────────────────────────────────────────────────────────────
DARK_BG = "#2d3436"           # Main dark background
DARK_BG_LIGHTER = "#3d4446"   # Slightly lighter dark (for inner panel border)
TEAL = "#3daa98"              # Primary teal/green color
TEAL_LIGHT = "#4dbfab"        # Lighter teal (button hover / active tab)
TEAL_DARK = "#2e8a7a"         # Darker teal (button border / shadow)
TEAL_BG = "#5bbfab"           # Teal background for "building" mode
WHITE = "#ffffff"
LIGHT_GRAY = "#c8d6d3"
OVERLAY_BG = "#2a2e30"        # Dark overlay modal background
FOOTER_BG = "#232829"         # Footer bar


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
# Main Application Class
# ──────────────────────────────────────────────────────────────────────────────
class IceCreamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("גלידה גנרית")
        self.root.geometry("600x650")
        self.root.resizable(False, False)
        self.root.configure(bg=DARK_BG)

        # Track state
        self.active_tab = "build"     # "build" or "disassemble"
        self.is_loading = False
        self.spinner_angle = 0
        self.spinner_job = None
        self.progress_value = 0
        self.progress_job = None

        # Build the UI
        self._build_main_ui()

    # ──────────────────────────────────────────────────────────────────────
    # Build the Main UI
    # ──────────────────────────────────────────────────────────────────────
    def _build_main_ui(self):
        """Construct the entire main window layout."""

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

        # ── Tab Buttons ──
        self._build_tabs()

        # ── Content Area (flavor buttons or disassemble) ──
        self.content_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER)
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self._show_build_tab()

        # ── Footer ──
        self._build_footer()

    def _build_header(self):
        """Build the title header with ice cream emojis."""
        header_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER, pady=20)
        header_frame.pack(fill="x")

        # Title with ice cream emojis
        title_label = tk.Label(
            header_frame,
            text="\U0001F366  גלידה גנרית  \U0001F366",
            font=("Arial", 28, "bold"),
            fg=WHITE,
            bg=DARK_BG_LIGHTER
        )
        title_label.pack()

    def _build_tabs(self):
        """Build the two tab buttons: Build Ice Cream / Disassemble Ice Cream."""
        tab_frame = tk.Frame(self.inner_frame, bg=DARK_BG_LIGHTER)
        tab_frame.pack(pady=(0, 10))

        # Tab container canvas for rounded look
        self.tab_canvas = tk.Canvas(tab_frame, width=380, height=45,
                                     bg=DARK_BG_LIGHTER, highlightthickness=0)
        self.tab_canvas.pack()

        # Draw background pill shape
        rounded_rect(self.tab_canvas, 0, 0, 380, 45, radius=22,
                      fill=TEAL_DARK, outline="")

        # "פירוק גלידה" (Disassemble) - RIGHT side (Hebrew RTL)
        self.tab_disassemble_bg = rounded_rect(
            self.tab_canvas, 195, 3, 377, 42, radius=20,
            fill=TEAL_DARK, outline=""
        )
        self.tab_disassemble_text = self.tab_canvas.create_text(
            286, 22, text="פירוק גלידה", font=("Arial", 13, "bold"),
            fill=WHITE
        )

        # "בניית גלידה" (Build) - LEFT side
        self.tab_build_bg = rounded_rect(
            self.tab_canvas, 3, 3, 195, 42, radius=20,
            fill=TEAL_LIGHT, outline=""
        )
        self.tab_build_text = self.tab_canvas.create_text(
            99, 22, text="בניית גלידה", font=("Arial", 13, "bold"),
            fill=WHITE
        )

        # Bind click events on the tab areas
        self.tab_canvas.tag_bind(self.tab_build_bg, "<Button-1>",
                                  lambda e: self._switch_tab("build"))
        self.tab_canvas.tag_bind(self.tab_build_text, "<Button-1>",
                                  lambda e: self._switch_tab("build"))
        self.tab_canvas.tag_bind(self.tab_disassemble_bg, "<Button-1>",
                                  lambda e: self._switch_tab("disassemble"))
        self.tab_canvas.tag_bind(self.tab_disassemble_text, "<Button-1>",
                                  lambda e: self._switch_tab("disassemble"))

    def _switch_tab(self, tab_name):
        """Switch between Build and Disassemble tabs."""
        if self.is_loading:
            return  # Don't switch while loading

        self.active_tab = tab_name

        if tab_name == "build":
            self.tab_canvas.itemconfig(self.tab_build_bg, fill=TEAL_LIGHT)
            self.tab_canvas.itemconfig(self.tab_disassemble_bg, fill=TEAL_DARK)
            self._show_build_tab()
        else:
            self.tab_canvas.itemconfig(self.tab_build_bg, fill=TEAL_DARK)
            self.tab_canvas.itemconfig(self.tab_disassemble_bg, fill=TEAL_LIGHT)
            self._show_disassemble_tab()

    def _show_build_tab(self):
        """Show the 'Build Ice Cream' tab with flavor selection."""
        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Section title: "בחירת טעמים" (Choose Flavors)
        section_label = tk.Label(
            self.content_frame,
            text="בחירת טעמים",
            font=("Arial", 18, "bold"),
            fg=WHITE,
            bg=DARK_BG_LIGHTER
        )
        section_label.pack(pady=(10, 30))

        # Flavor buttons in 2x2 grid
        # Hebrew is RTL, so right column = שוקולד, תות; left column = וניל, בננה
        flavors_frame = tk.Frame(self.content_frame, bg=DARK_BG_LIGHTER)
        flavors_frame.pack(expand=True)

        flavors = [
            ("שוקולד", 0, 1),    # Chocolate - row 0, right col
            ("וניל", 0, 0),      # Vanilla - row 0, left col
            ("תות", 1, 1),       # Strawberry - row 1, right col
            ("בננה", 1, 0),      # Banana - row 1, left col
        ]

        self.flavor_buttons = []
        for flavor_name, row, col in flavors:
            btn_canvas = self._create_flavor_button(flavors_frame, flavor_name)
            btn_canvas.grid(row=row, column=col, padx=8, pady=8)
            self.flavor_buttons.append(btn_canvas)

    def _create_flavor_button(self, parent, text):
        """Create a single teal rounded flavor button with an arrow icon."""
        width = 240
        height = 55
        canvas = tk.Canvas(parent, width=width, height=height,
                           bg=DARK_BG_LIGHTER, highlightthickness=0)

        # Button shadow (slight offset for 3D effect)
        rounded_rect(canvas, 2, 3, width - 2, height - 1, radius=26,
                      fill=TEAL_DARK, outline="")

        # Button body
        btn_bg = rounded_rect(canvas, 2, 2, width - 2, height - 4, radius=26,
                               fill=TEAL, outline="")

        # Flavor name text (centered-right for Hebrew)
        btn_text = canvas.create_text(width // 2 + 15, height // 2 - 1,
                                       text=text,
                                       font=("Arial", 15, "bold"),
                                       fill=WHITE)

        # Arrow icon on the left side: ↵ style icon using text
        arrow_text = canvas.create_text(35, height // 2 - 1,
                                         text="⏎",
                                         font=("Arial", 16),
                                         fill=TEAL_DARK)

        # Hover & click effects
        def on_enter(e):
            canvas.itemconfig(btn_bg, fill=TEAL_LIGHT)

        def on_leave(e):
            canvas.itemconfig(btn_bg, fill=TEAL)

        def on_click(e):
            print(self.content_frame)
            subprocess.run([sys.executable, "backup.py"])

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

    def _build_footer(self):
        """Build the footer bar with version text."""
        footer = tk.Frame(self.root, bg=FOOTER_BG, height=35)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        footer_text = tk.Label(
            footer,
            text="גרסה 1.0 - גלידה גנרית",
            font=("Arial", 10),
            fg=LIGHT_GRAY,
            bg=FOOTER_BG
        )
        footer_text.pack(expand=True)

    # ──────────────────────────────────────────────────────────────────────
    # Loading Overlay (Screen 2)
    # ──────────────────────────────────────────────────────────────────────
    def _start_making_ice_cream(self, flavor):
        """Show the loading overlay when a flavor is selected."""
        if self.is_loading:
            return
        self.is_loading = True
        self.selected_flavor = flavor
        self.progress_value = 0

        # Change background to teal (as shown in the second screenshot)
        self.inner_frame.configure(bg=TEAL_BG)
        for widget in self.inner_frame.winfo_children():
            try:
                widget.configure(bg=TEAL_BG)
            except tk.TclError:
                pass

        # Create a dark semi-transparent overlay using a Toplevel-like approach
        # We'll overlay a Frame on top of the content
        self.overlay = tk.Frame(self.root, bg=OVERLAY_BG)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center",
                           width=350, height=320)

        # Round the overlay appearance with a Canvas
        self.overlay_canvas = tk.Canvas(self.overlay, width=350, height=320,
                                         bg=OVERLAY_BG, highlightthickness=0)
        self.overlay_canvas.pack(fill="both", expand=True)

        # Background rounded rectangle
        rounded_rect(self.overlay_canvas, 0, 0, 350, 320, radius=20,
                      fill=OVERLAY_BG, outline="#3a3e40")

        # ── Spinner (circle of dots) ──
        self.spinner_dots = []
        cx, cy = 175, 90  # Center of spinner
        num_dots = 12
        dot_radius = 6
        circle_radius = 40

        for i in range(num_dots):
            angle = math.radians(i * (360 / num_dots) - 90)
            x = cx + circle_radius * math.cos(angle)
            y = cy + circle_radius * math.sin(angle)
            dot = self.overlay_canvas.create_oval(
                x - dot_radius, y - dot_radius,
                x + dot_radius, y + dot_radius,
                fill=TEAL_DARK, outline=""
            )
            self.spinner_dots.append(dot)

        # ── Text: "הגלידה בהכנה" (Ice Cream Is Being Made) ──
        self.overlay_canvas.create_text(
            175, 165,
            text="הגלידה בהכנה",
            font=("Arial", 20, "bold"),
            fill=WHITE
        )

        # ── Subtext: "אנא המתן" (Please Wait) ──
        self.overlay_canvas.create_text(
            175, 200,
            text="אנא המתן",
            font=("Arial", 14),
            fill=LIGHT_GRAY
        )

        # ── Progress Bar ──
        bar_x1, bar_y, bar_x2 = 100, 235, 250
        bar_height = 12

        # Progress bar background
        rounded_rect(self.overlay_canvas, bar_x1, bar_y,
                      bar_x2, bar_y + bar_height, radius=6,
                      fill="#1a1e20", outline="")

        # Progress bar fill (will be updated)
        self.progress_bar = rounded_rect(
            self.overlay_canvas, bar_x1, bar_y,
            bar_x1 + 2, bar_y + bar_height, radius=6,
            fill=TEAL, outline=""
        )
        self.progress_bar_x1 = bar_x1
        self.progress_bar_y = bar_y
        self.progress_bar_x2 = bar_x2
        self.progress_bar_h = bar_height

        # ── Cancel Button: "ביטול" ──
        cancel_bg = rounded_rect(self.overlay_canvas, 130, 265, 220, 300,
                                   radius=15, fill="#4a5055", outline="")
        cancel_text = self.overlay_canvas.create_text(
            175, 282,
            text="ביטול",
            font=("Arial", 12, "bold"),
            fill=WHITE
        )

        # Cancel button hover effects
        def cancel_enter(e):
            self.overlay_canvas.itemconfig(cancel_bg, fill="#5a6065")

        def cancel_leave(e):
            self.overlay_canvas.itemconfig(cancel_bg, fill="#4a5055")

        def cancel_click(e):
            self._cancel_loading()

        self.overlay_canvas.tag_bind(cancel_bg, "<Enter>", cancel_enter)
        self.overlay_canvas.tag_bind(cancel_bg, "<Leave>", cancel_leave)
        self.overlay_canvas.tag_bind(cancel_bg, "<Button-1>", cancel_click)
        self.overlay_canvas.tag_bind(cancel_text, "<Enter>", cancel_enter)
        self.overlay_canvas.tag_bind(cancel_text, "<Leave>", cancel_leave)
        self.overlay_canvas.tag_bind(cancel_text, "<Button-1>", cancel_click)

        # Start animations
        self._animate_spinner()
        self._animate_progress()

    def _animate_spinner(self):
        """Animate the circular spinner by cycling dot colors."""
        if not self.is_loading:
            return

        num_dots = len(self.spinner_dots)
        trail_length = 4  # Number of dots that appear "lit up"

        for i in range(num_dots):
            # Calculate distance from the "head" of the spinner
            distance = (self.spinner_angle - i) % num_dots
            if distance < trail_length:
                # Gradient from bright to dim
                brightness = 1.0 - (distance / trail_length)
                r = int(61 + brightness * (77 - 61))
                g = int(78 + brightness * (191 - 78))
                b = int(74 + brightness * (171 - 74))
                color = f"#{r:02x}{g:02x}{b:02x}"
            else:
                color = "#3a4e4a"  # Dim dot

            self.overlay_canvas.itemconfig(self.spinner_dots[i], fill=color)

        self.spinner_angle = (self.spinner_angle + 1) % num_dots
        self.spinner_job = self.root.after(100, self._animate_spinner)

    def _animate_progress(self):
        """Animate the progress bar filling up."""
        if not self.is_loading:
            return

        self.progress_value += 1
        max_val = 100
        if self.progress_value > max_val:
            # Done! Show completion
            self._finish_loading()
            return

        # Calculate fill width
        bar_width = self.progress_bar_x2 - self.progress_bar_x1
        fill_width = max(2, int(bar_width * (self.progress_value / max_val)))

        # Remove old progress bar and draw new one
        self.overlay_canvas.delete(self.progress_bar)
        self.progress_bar = rounded_rect(
            self.overlay_canvas,
            self.progress_bar_x1, self.progress_bar_y,
            self.progress_bar_x1 + fill_width,
            self.progress_bar_y + self.progress_bar_h,
            radius=6, fill=TEAL, outline=""
        )

        # Update every 50ms → ~5 seconds total
        self.progress_job = self.root.after(50, self._animate_progress)

    def _finish_loading(self):
        """Called when the progress bar completes."""
        self._stop_animations()
        self.is_loading = False

        # Remove overlay
        if self.overlay:
            self.overlay.place_forget()
            self.overlay.destroy()
            self.overlay = None

        # Restore background
        self.inner_frame.configure(bg=DARK_BG_LIGHTER)
        for widget in self.inner_frame.winfo_children():
            try:
                widget.configure(bg=DARK_BG_LIGHTER)
            except tk.TclError:
                pass

        # Show completion message
        self._show_completion_message()

    def _cancel_loading(self):
        """Cancel the ice cream making process."""
        self._stop_animations()
        self.is_loading = False

        # Remove overlay
        if self.overlay:
            self.overlay.place_forget()
            self.overlay.destroy()
            self.overlay = None

        # Restore background
        self.inner_frame.configure(bg=DARK_BG_LIGHTER)
        for widget in self.inner_frame.winfo_children():
            try:
                widget.configure(bg=DARK_BG_LIGHTER)
            except tk.TclError:
                pass

        # Re-show build tab
        self._show_build_tab()

    def _stop_animations(self):
        """Stop all running animations."""
        if self.spinner_job:
            self.root.after_cancel(self.spinner_job)
            self.spinner_job = None
        if self.progress_job:
            self.root.after_cancel(self.progress_job)
            self.progress_job = None

    def _show_completion_message(self):
        """Show a completion overlay after ice cream is done."""
        self.overlay = tk.Frame(self.root, bg=OVERLAY_BG)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center",
                           width=350, height=220)

        canvas = tk.Canvas(self.overlay, width=350, height=220,
                            bg=OVERLAY_BG, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        rounded_rect(canvas, 0, 0, 350, 220, radius=20,
                      fill=OVERLAY_BG, outline="#3a3e40")

        # Ice cream emoji
        canvas.create_text(175, 45, text="\U0001F366",
                            font=("Arial", 36))

        # "!הגלידה מוכנה" (The ice cream is ready!)
        canvas.create_text(175, 100,
                            text="!הגלידה מוכנה",
                            font=("Arial", 20, "bold"),
                            fill=WHITE)

        # Show selected flavor
        canvas.create_text(175, 135,
                            text=f"טעם: {self.selected_flavor}",
                            font=("Arial", 14),
                            fill=LIGHT_GRAY)

        # OK button
        ok_bg = rounded_rect(canvas, 135, 165, 215, 200, radius=15,
                               fill=TEAL, outline="")
        ok_text = canvas.create_text(175, 182, text="אישור",
                                      font=("Arial", 12, "bold"),
                                      fill=WHITE)

        def ok_enter(e):
            canvas.itemconfig(ok_bg, fill=TEAL_LIGHT)

        def ok_leave(e):
            canvas.itemconfig(ok_bg, fill=TEAL)

        def ok_click(e):
            self.overlay.place_forget()
            self.overlay.destroy()
            self.overlay = None
            self._show_build_tab()

        canvas.tag_bind(ok_bg, "<Enter>", ok_enter)
        canvas.tag_bind(ok_bg, "<Leave>", ok_leave)
        canvas.tag_bind(ok_bg, "<Button-1>", ok_click)
        canvas.tag_bind(ok_text, "<Enter>", ok_enter)
        canvas.tag_bind(ok_text, "<Leave>", ok_leave)
        canvas.tag_bind(ok_text, "<Button-1>", ok_click)


# ──────────────────────────────────────────────────────────────────────────────
# Run the App
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = IceCreamApp(root)
    root.mainloop()
