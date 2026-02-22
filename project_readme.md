# CityCab: Ultimate Edition

Lightweight Streamlit-based cab booking simulator with Passenger, Driver and Admin dashboards, maps (Folium), simple OTP flow, wallets and SQLite persistence.

## Features
- Passenger: book private/shared rides, view history, profile and spending chart
- Driver: accept rides, start/end trips with OTP, earnings tracking
- Admin: platform KPIs, user/driver lists, analytics
- Maps: pickup/drop markers via Folium and `streamlit_folium`
- Simple SQLite backend (`citycab_final_v2.db`) with seeded test accounts

## Tech Stack
- Python 3.10+
- Streamlit
- Folium + streamlit_folium
- SQLite (builtin)
- Pandas

> Repository contains other language folders (Java, JavaScript, TypeScript, Kotlin, C++, Gradle, npm) — this app is the Python Streamlit component located at `Project.py`.

## Quickstart (Windows)
1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
