#!/usr/bin/env python3
"""
Chemotherapy Calculator Calendar — Unified Version
-------------------------------------------------
All requested features:
- BSA-based dosing (mg/m^2/day × BSA)
- Whole-tablet rounding (ceil/floor mix) with scheduling modes:
  • Front-load overall  • Weekly front-load  • Alternating high/low
- Adjustable: BSA, mg/m^2/day, days, tablet size (mg)
- Total mg/m^2 is derived (not editable)
- 7-column calendar view
- Provider-friendly summary (INPUTS, DERIVED, DAILY DOSE, ROUNDING MIX, TOTALS)
- Pharmacy one-liner (copy button + included in provider export)
- Total number of tablets (on-screen + in both exports)
- Two exports: Provider (ASCII, landscape attempt) and Patient (12pt, landscape attempt)
- Window opens compact and resizable

DISCLAIMER: Support tool only. Verify against protocol and clinical judgment.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from math import floor
from typing import List, Tuple

APP_TITLE = "Chemotherapy Calculator Calendar"

DEFAULTS = {
    "bsa": 1.70,
    "mg_per_m2_day": 50.0,
    "days": 21,
    "tablet_size_mg": 50,
    "mode": "Front-load overall",
}

SCHEDULE_MODES = [
    "Front-load overall",
    "Weekly front-load",
    "Alternating high/low",
]

# -------------------- Core math --------------------

def compute_mix(bsa: float, mg_per_m2_day: float, days: int, tablet_size_mg: int):
    if any(x <= 0 for x in (bsa, mg_per_m2_day, days, tablet_size_mg)):
        raise ValueError("All inputs must be positive.")

    exact_daily_mg = mg_per_m2_day * bsa
    exact_tabs = exact_daily_mg / tablet_size_mg
    f = int(floor(exact_tabs))
    c = f if abs(exact_tabs - f) < 1e-12 else f + 1

    total_exact_tabs = days * exact_tabs
    ceil_days = 0 if c == f else int(round(total_exact_tabs - days * f))
    ceil_days = max(0, min(days, ceil_days))

    return {
        "exact_daily_mg": exact_daily_mg,
        "exact_tabs": exact_tabs,
        "floor_tabs": f,
        "ceil_tabs": c,
        "ceil_days": ceil_days,
        "floor_days": days - ceil_days,
    }

# -------------------- Scheduling arrangements --------------------

def arrange_frontload_overall(days: int, ceil_days: int, c: int, f: int) -> List[int]:
    return [c]*ceil_days + [f]*(days - ceil_days)

def arrange_weekly_frontload(days: int, ceil_days_total: int, exact_tabs: float, c: int, f: int) -> List[int]:
    # Distribute ceil-days week by week, placing them at the start of each 7-day block.
    per_day = [f] * days
    remaining_ceil = ceil_days_total
    start = 0
    while start < days:
        week_len = min(7, days - start)
        wk_f = int(floor(exact_tabs))
        wk_c = wk_f if abs(exact_tabs - wk_f) < 1e-12 else wk_f + 1
        wk_ceil = 0 if wk_c == wk_f else int(round(week_len * exact_tabs - week_len * wk_f))
        wk_ceil = max(0, min(week_len, wk_ceil, remaining_ceil))
        for i in range(wk_ceil):
            per_day[start + i] = c
        remaining_ceil -= wk_ceil
        start += week_len
    # If rounding left unplaced highs, place earliest first
    start = 0
    while remaining_ceil > 0 and start < days:
        week_end = min(start + 7, days)
        for i in range(start, week_end):
            if per_day[i] == f:
                per_day[i] = c
                remaining_ceil -= 1
                if remaining_ceil == 0:
                    break
        start += 7
    return per_day

def arrange_alternating(days: int, ceil_days: int, c: int, f: int) -> List[int]:
    per_day = []
    highs = ceil_days
    lows = days - ceil_days
    turn_high = True
    while len(per_day) < days:
        if turn_high and highs > 0:
            per_day.append(c); highs -= 1
        elif (not turn_high) and lows > 0:
            per_day.append(f); lows -= 1
        elif highs > 0:
            per_day.append(c); highs -= 1
        else:
            per_day.append(f); lows -= 1
        turn_high = not turn_high
    return per_day

# -------------------- Pharmacy one-liner helpers --------------------

def compress_runs(per_day_tabs: List[int]) -> List[Tuple[int,int,int]]:
    """Return list of (start_day, end_day, tabs) runs."""
    if not per_day_tabs:
        return []
    runs = []
    start = 1
    current = per_day_tabs[0]
    for i in range(1, len(per_day_tabs)):
        if per_day_tabs[i] != current:
            runs.append((start, i, current))
            start = i+1
            current = per_day_tabs[i]
    runs.append((start, len(per_day_tabs), current))
    return runs

def is_strict_alternating(per_day_tabs: List[int]) -> Tuple[bool,int,int]:
    if len(per_day_tabs) < 2:
        return False, 0, 0
    a = per_day_tabs[0]
    b = per_day_tabs[1]
    if a == b:
        return False, 0, 0
    for i in range(2, len(per_day_tabs)):
        expect = a if i % 2 == 0 else b
        if per_day_tabs[i] != expect:
            return False, 0, 0
    return True, a, b

def format_pharmacy_snippet(per_day_tabs: List[int], tablet_size_mg: int, days: int, mg_per_m2_day: float, bsa: float) -> str:
    alt, a, b = is_strict_alternating(per_day_tabs)
    if alt:
        return (f"Tablet size {tablet_size_mg} mg: Alternate {a} and {b} tab(s) daily, starting with {a}, for {days} days; "
                f"dose {mg_per_m2_day:g} mg/m^2/day at BSA {bsa:.2f} m^2.")
    runs = compress_runs(per_day_tabs)
    ranges = []
    for s,e,t in runs:
        label = f"Day {s}" if s == e else f"Days {s}-{e}"
        ranges.append(f"{label}: {t} tab(s)")
    return (f"Tablet size {tablet_size_mg} mg; " + "; ".join(ranges) +
            f"; total {days} days; dose {mg_per_m2_day:g} mg/m^2/day at BSA {bsa:.2f} m^2.")

# -------------------- Calendar text --------------------

def make_calendar_text(per_day_tabs: List[int], tablet_size_mg: int, cols: int = 7) -> str:
    # Calendar grid with 3 text lines per cell
    days = len(per_day_tabs)
    rows = (days + cols - 1) // cols
    cells = []
    for i, tabs in enumerate(per_day_tabs):
        mg = tabs * tablet_size_mg
        cells.append(f"Day {i+1}\n{tabs} tab(s)\n({mg} mg)")
    maxw = max((len(line) for cell in cells for line in cell.splitlines()), default=12)
    cw = max(12, maxw)

    header = " | ".join(f"D{c+1}".center(cw) for c in range(cols))
    lines = [header, "-"*len(header)]

    for r in range(rows):
        block = []
        for c_i in range(cols):
            idx = r*cols + c_i
            if idx < days:
                parts = cells[idx].splitlines()
            else:
                parts = ["", "", ""]
            while len(parts) < 3: parts.append("")
            block.append([p.ljust(cw) for p in parts[:3]])
        for li in range(3):
            lines.append(" | ".join(block[c_i][li] for c_i in range(cols)))
        lines.append("-"*len(header))
    return "\n".join(lines)

# -------------------- Export helpers (RTF) --------------------

def _rtf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

def ascii_sanitize(s: str) -> str:
    mapping = {
        "m²": "m^2", "µ": "u", "×": "x", "–": "-", "—": "-", "→": "->",
        "≤": "<=", "≥": ">=", "…": "...", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "-", "°": " deg ", "™": "(TM)", "®": "(R)", "©": "(C)"
    }
    for k,v in mapping.items():
        s = s.replace(k,v)
    try:
        s = s.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        pass
    return s

def export_provider_rtf(filepath: str, title: str, summary: str, pharmacy_line: str, calendar_text: str, total_pills: int):
    # ASCII-only provider doc; attempt landscape Letter via \\paperw/\\paperh
    summary_ascii = ascii_sanitize(summary)
    calendar_ascii = ascii_sanitize(calendar_text)
    pharm_ascii = ascii_sanitize(pharmacy_line)
    header = (r"{\rtf1\ansi\deff0"
              r"{\fonttbl{\f0\fmodern Courier New;}{\f1\fmodern Consolas;}}"
              r"\paperw15840\paperh12240\margl720\margr720\margt720\margb720 ")
    body = (r"\fs20 \b " + _rtf_escape(ascii_sanitize(title)) + r"\b0\line "
            + r"\f0 "
            + r"\b Provider Summary\b0\line " + _rtf_escape(summary_ascii) + r"\line "
            + r"Total tablets to dispense: " + str(total_pills) + r"\line\line "
            + r"\b Pharmacy Snippet\b0\line " + _rtf_escape(pharm_ascii) + r"\line\line "
            + r"\b Calendar\b0\line " + _rtf_escape(calendar_ascii).replace("\n", r"\line "))
    rtf = header + body + "}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(rtf)

def export_patient_rtf(filepath: str, title: str, patient_intro: str, calendar_text: str, total_pills: int):
    # Patient-friendly 12pt, attempt landscape Letter via \\paperw/\\paperh
    header = (r"{\rtf1\ansi\deff0"
              r"{\fonttbl{\f0\fmodern Courier New;}{\f1\fmodern Consolas;}}"
              r"\paperw15840\paperh12240\margl720\margr720\margt720\margb720 ")
    intro = _rtf_escape(patient_intro)
    cal = _rtf_escape(calendar_text).replace("\n", r"\line ")
    body = (r"\fs24 \b Your Chemotherapy Tablet Schedule\b0\line "
            + intro + r"\line "
            + r"Total tablets for the course: " + str(total_pills) + r"\line\line "
            + r"\b Daily Plan\b0\line " + cal)
    rtf = header + r"\f0 " + body + "}"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(rtf)

# -------------------- GUI --------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        # Natural size, resizable
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        p = ttk.Frame(self, padding=10)
        p.pack(fill="both", expand=True)

        row = 0
        ttk.Label(p, text="BSA (m^2):", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w")
        self.var_bsa = tk.StringVar(value=str(DEFAULTS["bsa"]))
        ttk.Entry(p, textvariable=self.var_bsa, width=8).grid(row=row, column=1, sticky="w", padx=6)

        ttk.Label(p, text="mg/m^2/day:", font=("Segoe UI", 10)).grid(row=row, column=2, sticky="w", padx=(12,0))
        self.var_mg_day = tk.StringVar(value=str(DEFAULTS["mg_per_m2_day"]))
        ttk.Entry(p, textvariable=self.var_mg_day, width=8).grid(row=row, column=3, sticky="w", padx=6)

        ttk.Label(p, text="Days:", font=("Segoe UI", 10)).grid(row=row, column=4, sticky="w", padx=(12,0))
        self.var_days = tk.StringVar(value=str(DEFAULTS["days"]))
        ttk.Entry(p, textvariable=self.var_days, width=6).grid(row=row, column=5, sticky="w", padx=6)

        ttk.Label(p, text="Tablet size (mg):", font=("Segoe UI", 10)).grid(row=row, column=6, sticky="w", padx=(12,0))
        self.var_tab = tk.StringVar(value=str(DEFAULTS["tablet_size_mg"]))
        ttk.Entry(p, textvariable=self.var_tab, width=8).grid(row=row, column=7, sticky="w", padx=6)

        row += 1
        ttk.Label(p, text="Schedule mode:", font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", pady=(8,0))
        self.var_mode = tk.StringVar(value=DEFAULTS["mode"])
        ttk.Combobox(p, textvariable=self.var_mode, values=SCHEDULE_MODES, width=20, state="readonly").grid(row=row, column=1, sticky="w", padx=6, pady=(8,0))
        ttk.Button(p, text="Calculate", command=self.on_calculate).grid(row=row, column=2, padx=(12,0), pady=(8,0))
        ttk.Button(p, text="Export Provider (.doc)", command=self.on_export_provider).grid(row=row, column=3, padx=(8,0), pady=(8,0))
        ttk.Button(p, text="Export Patient (.doc)", command=self.on_export_patient).grid(row=row, column=4, padx=(8,0), pady=(8,0))

        row += 1
        ttk.Separator(p).grid(row=row, column=0, columnspan=8, sticky="ew", pady=8)

        # Provider summary (organized)
        row += 1
        ttk.Label(p, text="Provider Summary", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, columnspan=8, sticky="w")
        row += 1
        self.txt_summary = tk.Text(p, height=8, width=100, wrap="word", font=("Consolas", 10))
        self.txt_summary.grid(row=row, column=0, columnspan=8, sticky="nsew")

        # Calendar grid
        row += 1
        ttk.Label(p, text="Calendar", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, columnspan=8, sticky="w", pady=(6,2))
        row += 1
        self.txt_calendar = tk.Text(p, height=18, width=100, wrap="none", font=("Consolas", 10))
        self.txt_calendar.grid(row=row, column=0, columnspan=8, sticky="nsew")

        # Pharmacy one-liner
        row += 1
        ttk.Label(p, text="Pharmacy one-liner (or copy 'ROUNDING MIX' above)", font=("Segoe UI", 10, "bold")).grid(row=row, column=0, columnspan=8, sticky="w", pady=(6,2))
        row += 1
        self.pharm_var = tk.StringVar(value="")
        self.ent_pharm = ttk.Entry(p, textvariable=self.pharm_var, width=110)
        self.ent_pharm.grid(row=row, column=0, columnspan=7, sticky="ew")
        ttk.Button(p, text="Copy", command=self.copy_pharmacy).grid(row=row, column=7, sticky="e", padx=(6,0))

        # Totals
        row += 1
        self.lbl_totals = ttk.Label(p, text="Total tablets: —", font=("Segoe UI", 10, "bold"))
        self.lbl_totals.grid(row=row, column=0, columnspan=8, sticky="w", pady=(6,0))

        # Disclaimer
        row += 1
        disclaimer = ("Verify dosing with institutional protocol. Tool ignores renal/hepatic function, ANC/platelets, and interactions.")
        ttk.Label(p, text=disclaimer, foreground="#A00000", wraplength=760).grid(row=row, column=0, columnspan=8, sticky="w", pady=(6,0))

        for c in range(8):
            p.grid_columnconfigure(c, weight=1)

        self.bind("<Return>", lambda e: self.on_calculate())

    def _parse_inputs(self):
        try:
            bsa = float(self.var_bsa.get().strip())
            mg_day = float(self.var_mg_day.get().strip())
            days = int(float(self.var_days.get().strip()))
            tab = int(float(self.var_tab.get().strip()))
            if any(x <= 0 for x in (bsa, mg_day, days, tab)):
                raise ValueError
            return bsa, mg_day, days, tab
        except Exception:
            messagebox.showerror("Invalid input", "Enter positive numeric values (BSA, mg/m^2/day, days, tablet size).")
            return None

    def _arrange_by_mode(self, days, ceil_days, exact_tabs, c, f, mode):
        if mode == "Front-load overall":
            return arrange_frontload_overall(days, ceil_days, c, f)
        if mode == "Weekly front-load":
            return arrange_weekly_frontload(days, ceil_days, exact_tabs, c, f)
        if mode == "Alternating high/low":
            return arrange_alternating(days, ceil_days, c, f)
        return arrange_frontload_overall(days, ceil_days, c, f)

    def on_calculate(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        bsa, mg_day, days, tab = parsed

        mix = compute_mix(bsa, mg_day, days, tab)
        per_day_tabs = self._arrange_by_mode(days, mix["ceil_days"], mix["exact_tabs"],
                                             mix["ceil_tabs"], mix["floor_tabs"], self.var_mode.get())

        exact_total_mg = mix["exact_daily_mg"] * days
        mixed_total_mg = sum(t * tab for t in per_day_tabs)
        total_pills = sum(per_day_tabs)
        derived_total_m2 = mg_day * days

        # Provider summary (organized)
        lines = []
        lines.append(f"INPUTS -> BSA {bsa:.2f} m^2 | mg/m^2/day {mg_day:.3g} | Days {days} | Tablet {tab} mg | Mode {self.var_mode.get()}")
        lines.append(f"DERIVED -> Total mg/m^2: {derived_total_m2:.3g}")
        lines.append(f"DAILY DOSE -> Exact {mix['exact_daily_mg']:.1f} mg  ({mix['exact_tabs']:.3f} tab/day)")
        lines.append(f"ROUNDING MIX -> {mix['ceil_tabs']} tab(s) on {mix['ceil_days']} day(s); {mix['floor_tabs']} tab(s) on {mix['floor_days']} day(s)")
        lines.append(f"TOTALS -> Exact {exact_total_mg:.0f} mg | Mixed {mixed_total_mg:.0f} mg | Tablets {total_pills}")
        self.txt_summary.delete("1.0", "end")
        self.txt_summary.insert("1.0", "\n".join(lines))

        cal = make_calendar_text(per_day_tabs, tab, cols=7)
        self.txt_calendar.delete("1.0", "end")
        self.txt_calendar.insert("1.0", cal)

        # Pharmacy one-liner
        pharm = format_pharmacy_snippet(per_day_tabs, tab, days, mg_day, bsa)
        self.pharm_var.set(pharm)

        self.lbl_totals.config(text=f"Total tablets to dispense: {total_pills} (each {tab} mg)")

        # Keep last results for export
        self._last_provider_summary = "\n".join(lines)
        self._last_calendar = cal
        self._last_pharmacy = pharm
        self._last_total_pills = total_pills
        self._last_patient_intro = (
            f"This plan lasts {days} days. Each tablet is {tab} mg. On some days you will take more tablets than others to match your dose."
        )

    def copy_pharmacy(self):
        txt = self.pharm_var.get()
        if not txt:
            return
        self.clipboard_clear()
        self.clipboard_append(txt)
        messagebox.showinfo("Copied", "Pharmacy snippet copied to clipboard.")

    def on_export_provider(self):
        if not hasattr(self, "_last_calendar"):
            messagebox.showwarning("Nothing to export", "Calculate a schedule first.")
            return
        fname = filedialog.asksaveasfilename(
            title="Export Provider Order",
            defaultextension=".doc",
            filetypes=[("Word document (.doc)", "*.doc"), ("Rich Text Format (.rtf)", "*.rtf"), ("All files", "*.*")],
            initialfile="Chemo_Provider_Order.doc",
        )
        if not fname:
            return
        try:
            export_provider_rtf(fname, APP_TITLE, self._last_provider_summary, self._last_pharmacy, self._last_calendar, self._last_total_pills)
            messagebox.showinfo("Exported", f"Saved: {fname}\n")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

    def on_export_patient(self):
        if not hasattr(self, "_last_calendar"):
            messagebox.showwarning("Nothing to export", "Calculate a schedule first.")
            return
        fname = filedialog.asksaveasfilename(
            title="Export Patient Handout",
            defaultextension=".doc",
            filetypes=[("Word document (.doc)", "*.doc"), ("Rich Text Format (.rtf)", "*.rtf"), ("All files", "*.*")],
            initialfile="Chemo_Patient_Handout.doc",
        )
        if not fname:
            return
        try:
            export_patient_rtf(fname, APP_TITLE, self._last_patient_intro, self._last_calendar, self._last_total_pills)
            messagebox.showinfo("Exported", f"Saved: {fname}\n")
        except Exception as e:
            messagebox.showerror("Export failed", str(e))

if __name__ == "__main__":
    app = App()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    app.mainloop()
