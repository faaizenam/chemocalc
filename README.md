Chemotherapy Calculator Calendar
================================

What this is
------------
A BSA-based chemotherapy tablet scheduler with:
- Whole-tablet rounding (no splitting)
- Three scheduling modes:
  1) Front-load overall (higher early, lower later)
  2) Weekly front-load (higher at start of each 7-day block)
  3) Alternating high/low
- Derived total mg/m^2 (display-only)
- 7-column calendar output
- “Sig” one-liner for pharmacy (no tablet size, no quantity)
- Total tablets to dispense
- Exports:
  • Provider .doc (RTF, ASCII-safe, landscape attempt, includes Sig)
  • Patient .doc (RTF, 12 pt, landscape attempt, plain language)

Two ways to use
---------------
A) Windows app
   - Run ChemoCalculatorCalendar.exe (no Python needed).
   - If Windows warns:
     • Right-click → Properties → Unblock → OK
     • SmartScreen: More info → Run anyway (or use a code-signed build).
   - Outlook will usually block .exe attachments. Share via a link (GitHub Release,
     SharePoint/OneDrive) or zip it.

B) Static website (no backend; everything in the browser)
   - Open index.html (works locally) or visit the GitHub Pages URL (see below).
   - No PHI is sent to a server; all computation is client-side.
   - Works offline after first load (browser cache permitting).

Repository layout
-----------------
/app/
  ChemoCalculatorCalendar.exe            ← built Windows binary
  (optional) ChemoCalculatorCalendar.py  ← source used to build the .exe

/site/
  index.html     ← UI + all features in browser
  app.js         ← calculation + calendar + Sig + RTF exports
  styles.css     ← minimal styling
  /assets        ← (optional) icons or logo

/README.txt      ← this file
/LICENSE         ← (optional) your chosen license

Quick start (static site)
-------------------------
1) Put the files under /site/.
2) Test locally: double-click index.html. Enter BSA, mg/m^2/day, days, tablet size; select
   schedule mode; click Calculate. Use the Copy button for the Sig, or export Provider/Patient docs.
3) Deploy to GitHub Pages:
   - Commit/push to your repo.
   - GitHub → Settings → Pages:
       • Source: Deploy from branch
       • Branch: main (or default)
       • Folder: /site (select “/root” if you placed files at repo root)
   - Save. Wait ~1–2 minutes for the site to go live at:
       https://<your-user>.github.io/<your-repo>/
   - If the page 404s, give it a minute and refresh. Clear cache if needed.

Quick start (Windows app)
-------------------------
1) Grab ChemoCalculatorCalendar.exe from /app/ or the Releases page.
2) First-run friction you WILL see on some machines:
   - “This file came from another computer” banner: Right-click → Properties → Unblock.
   - SmartScreen: “Windows protected your PC” → More info → Run anyway.
   - Some hospitals block unknown binaries; share via a signed build or IT-approved share.

How the rounding and modes work (trust but verify)
--------------------------------------------------
- Daily exact tablets = (mg/m^2/day × BSA) / tablet_size_mg
- Mix = “ceil” tabs on N days and “floor” tabs on the rest so the total tablet count
  matches the rounded course total as closely as possible.
- Modes only change the ordering of those higher vs lower days:
  • Front-load overall: all higher-tab days first, then lower-tab days
  • Weekly front-load: repeat a weekly pattern (hi… then lo…) across each 7-day block
  • Alternating: interleave higher and lower days, starting with higher

Sig one-liner (pharmacist-friendly)
-----------------------------------
- Output is “Sig: …” only (no tablet size or quantity; those live elsewhere in the order).
- Heuristics pick the simplest natural wording:
  • Uniform → “Sig: Take X tab(s) PO once daily for N days.”
  • Two contiguous blocks → “Days 1–K: X tab(s) PO daily; then Days K+1–N: Y tab(s) PO daily. Total N days.”
  • Weekly front-load → “Repeat weekly ×W: Days 1–k: X tab(s) PO daily; Days k+1–7: Y tab(s) PO daily. Total N days.”
  • Strict alternating → “Alternate X and Y tab(s) PO daily, starting with X, for N days.”
  • Fallback → compressed day ranges.

Export details (RTF)
--------------------
- Provider .doc (RTF) is ASCII-sanitized so symbols render consistently (e.g., m^2).
- Patient .doc (RTF) uses 12-pt monospace for clean calendar alignment.
- Both attempt landscape via RTF section props; if Word ignores it, content still lays out.
- If Word shows raw “{\rtf1\ansi…” text, your RTF header got escaped—use the provided export code.

Hosting the .exe for download
-----------------------------
- Best: GitHub Releases
  1) Repo → Releases → Draft a new release
  2) Upload ChemoCalculatorCalendar.exe as a release asset
  3) Publish and share the link
- Alternative: SharePoint/OneDrive/Teams file link (inside hospital domains).
- Email attachments are unreliable for .exe; Outlook usually blocks them.

Building a new .exe (optional, for maintainers)
-----------------------------------------------
- Build on Windows with Python 3.x:
  py -3 -m pip install --upgrade pip
  py -3 -m pip install pyinstaller pyinstaller-hooks-contrib
  py -3 -m PyInstaller --noconfirm --clean --windowed --onefile ^
      --name ChemoCalculatorCalendar --hidden-import tkinter ^
      ChemoCalculatorCalendar.py
- Output: dist\ChemoCalculatorCalendar.exe
- If you want an icon: add “--icon chemo.ico”.

Security / privacy reality check
--------------------------------
- Static site: all calculation happens in the browser; no patient data is sent to a server.
- Don’t paste PHI into issue titles, commit messages, or screenshots.
- The Windows app runs fully offline.
- This is a **clinical support tool**; verify against protocol and clinical judgment
  (renal/hepatic function, ANC/platelets, interactions are NOT accounted for).

Support / common problems
-------------------------
- “Portrait export” → you’re using an older export function; upgrade to the RTF with single
  backslashes and \sectd\landscape in the header.
- “Weird symbols” → use the Provider export (ASCII sanitized) or switch the font in Word.
- “Pages not loading” → ensure GitHub Pages source is /site or repo root and wait a minute.

Versioning
----------
- Tag releases for each significant change (e.g., weekly-frontload tweak, Sig wording).
- Keep the .exe and /site in sync so UI and web behavior match.

End
---
This is deliberately simple: one .exe for Windows, one static site for everyone else.
If a feature complicates the UI or confuses the pharmacist, it doesn’t ship.
