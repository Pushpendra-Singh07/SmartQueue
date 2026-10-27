# SmartQueue

Hospital OPD queue system. Reception issues a token, doctors call patients in order, and admin sees who is waiting and how the day went.

Emergency patients are always served before normal patients. Within each group, earlier arrivals go first.

## Roles

| Role | What they do |
|------|----------------|
| **Staff** | Register a patient, assign a doctor and priority, get a token, watch the queue |
| **Doctor** | See only their queue, call next, mark Done or No Show, search past visits |
| **Admin** | Add departments, doctors, and staff. Dashboard shows patients per day, load by department and doctor, average wait, and no-show rate |

## Stack

- Python, FastAPI, Jinja2 templates
- MySQL with SQLAlchemy
- Session login (one page, redirect by role)
- Passwords hashed with bcrypt
- Live queue refresh by polling
- Charts with Chart.js, layout with Tabler

This is not a Vite or React app. Do not deploy it with `vite build`.

## Run it locally

You need Python 3.10+ and MySQL.

```sql
CREATE DATABASE smartqueue CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
python -m venv venv
```

Windows:

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Mac:

```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Put your MySQL password in `.env`:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/smartqueue
SECRET_KEY=replace-with-a-long-random-string
```

`SECRET_KEY` signs the login cookie. It is not the database password and it must not be committed.

```bash
python seed.py
uvicorn main:app --reload
```

Open [http://127.0.0.1:8000/login](http://127.0.0.1:8000/login).

### Seed logins

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Doctor | `doctor1` | `doctor123` |
| Staff | `staff1` | `staff123` |

Change these before the site is public.

## Project layout

```text
main.py            app entry, sessions, routers
database.py        MySQL connection
models.py          User, Department, Doctor, Patient, QueueEntry
auth.py            hashing and role checks
seed.py            first admin, doctor, department, and staff
routers/           login, admin, doctor, staff, queue API
templates/         pages
static/            CSS and live queue script
```

## Queue rule

Waiting rows for one doctor are ordered as:

```sql
ORDER BY (CASE WHEN priority = 'Emergency' THEN 0 ELSE 1 END), check_in_time ASC;
```

Status flow: Waiting → In Progress → Done. A called patient who does not arrive is marked No Show and the queue continues.

## Deploy

Host it on a Python server such as Railway, with a hosted MySQL database. Set `DATABASE_URL` and `SECRET_KEY` in the host's environment, not in the repo.

If the host gives a URL that starts with `mysql://`, the app rewrites it to `mysql+pymysql://`.

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Run `python seed.py` once on the server after the first successful boot. A GoDaddy domain is only the name. Point its DNS at the host after the app URL already works. Do not buy GoDaddy website hosting for this project.
