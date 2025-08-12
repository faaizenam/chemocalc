Etoposide Dose Calculator
=========================

This directory contains a simple Tkinter application for calculating
etoposide doses based on a patient's body surface area (BSA). By default the
regimen assumes **50 mg/m²/day** for **21 days**, but you can override
both the per‑day dose and the number of dosing days. The application also
automatically recalculates the **total dose per m²** when you change either
value. Tablets come only in 50 mg strength; the calculator rounds the daily
tablet count to whole numbers and proposes an alternating schedule (mixing
higher and lower tablet counts) to minimise cumulative dosing error.

Files
-----

* **EtoposideDoseCalculator.py** – the Python source code for the GUI
  application. Run this with `python EtoposideDoseCalculator.py` if you have
  Python 3.10+ installed.

Packaging as a standalone Windows EXE
-------------------------------------

Although this repository is Linux‑based, you can produce a Windows executable
on a Windows machine using PyInstaller. Cross‑compiling from Linux to
Windows is *not* supported by PyInstaller, so you must run the following
commands on a Windows computer with Python installed:

```powershell
# Install PyInstaller (only required once)
python -m pip install pyinstaller

# Generate a single‑file, windowed executable (no console)
pyinstaller --onefile --windowed EtoposideDoseCalculator.py

# The resulting EXE will be in the `dist` folder. You can rename it or
# distribute it directly.
```

For convenience, you can also use `pyinstaller` with the `--icon=...` flag
to embed an icon in the executable. See the PyInstaller documentation for
additional options.

Usage
-----

1. Launch the application. A window will appear where you can enter the patient's
   BSA as well as customise the intended regimen.
2. Enter the BSA (in square metres). Adjust the **dose per m² per day**, the
   **total dose per m²**, or the **number of days** as needed. When you change
   one, the others will update automatically to remain consistent.
3. Click **Calculate**. The app displays:
   * The exact daily dose (mg) and tablet count (fractional) for this patient.
   * How many days require the higher tablet count versus the lower count.
   * The total patient‑specific dose target and the total delivered by the
     proposed schedule.
   * A day‑by‑day schedule table listing how many 50 mg tablets to take each
     day (length equal to the number of days you specified).

Please verify doses with your institutional protocols before prescribing.