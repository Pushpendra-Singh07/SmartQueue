# SmartQueue

Hospital OPD queue system.

- Admin: departments, doctors, staff, daily / department / doctor charts, wait time, no-show rate
- Staff: register patients, generate tokens, read-only live queue
- Doctor: emergency-first queue, call next, done, no-show, patient history search

## Run locally

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python seed.py
uvicorn main:app --reload
```

Set your MySQL password in `.env`. Create the database first:

```sql
CREATE DATABASE smartqueue CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Logins after seed: `admin/admin123`, `doctor1/doctor123`, `staff1/staff123`.

Pandas is not required. Charts use Chart.js in the browser.
