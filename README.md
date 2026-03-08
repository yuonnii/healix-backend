# Healix Backend API

Healthcare platform connecting patients, doctors, and pharmacies.

---

## Project Structure

```
healix/
├── healix/               ← Core config (settings, urls, permissions, exceptions)
├── accounts/             ← Users, authentication, patient profiles
├── doctors/              ← Doctor profiles, search, availability, reviews
├── appointments/         ← Booking, smart queue system, messaging
├── pharmacies/           ← Pharmacy & medicine inventory
├── prescriptions/        ← Prescriptions & image scanning
├── manage.py
├── requirements.txt
└── .env.example
```

---

## Setup Guide 

### 1. Prerequisites

Install Python 3.10+ from https://python.org.
Verify: `python --version`

---

### 2. Create & activate a virtual environment

```bash
# Create
python -m venv venv

# Activate — Mac/Linux:
source venv/bin/activate

# Activate — Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` — for local development the defaults work as-is. SQLite is used automatically.

---

### 5. Create database tables
```bash
# Step 1 — Generate migration files from your models
python manage.py makemigrations accounts
python manage.py makemigrations doctors
python manage.py makemigrations appointments
python manage.py makemigrations pharmacies
python manage.py makemigrations prescriptions

# Step 2 — Apply migrations (creates the actual database tables)
python manage.py migrate
```

### 6. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

Enter your email, and password when prompted.

---

### 7. Run the development server

```bash
python manage.py runserver
```

The API is now live at: **http://127.0.0.1:8000**

- Swagger UI (interactive docs): http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- Admin panel: http://127.0.0.1:8000/admin/

---


## Testing with Postman

### Install Postman
Download from https://postman.com/downloads/

---

### Step 1 — Set up a Collection

1. Open Postman → Click **New** → **Collection** → Name it `Healix API`
2. Click the collection → **Variables** tab → Add:
   - Variable: `base_url` | Value: `http://127.0.0.1:8000/api/v1`
   - Variable: `access_token` | Value: *(leave blank for now)*

Now use `{{base_url}}` in all your requests instead of typing the full URL.

---

### Step 2 — Register a Patient

- **Method:** POST
- **URL:** `{{base_url}}/auth/register/patient/`
- **Body** → raw → JSON:

```json
{
    "email": "patient@healix.com",
    "first_name": "Sara",
    "last_name": "Ahmed",
    "phone_number": "+213555000001",
    "password": "Test1234!",
    "password_confirm": "Test1234!",
    "date_of_birth": "1995-03-20",
    "gender": "female",
    "blood_type": "A+"
}
```

- Copy the `access` token from the response.

---

### Step 3 — Set the token in Postman

**Option A (manual):**
After login/register, copy the `access` token and paste it into your Collection variable `access_token`.

**Option B (automatic — recommended):**
In your Login request → **Tests** tab, paste:
```javascript
var data = pm.response.json();
pm.collectionVariables.set("access_token", data.data.tokens.access);
```
Now every login auto-saves the token.

---

### Step 4 — Authenticate requests

For any protected endpoint:
1. Go to the request → **Authorization** tab
2. Type: **Bearer Token**
3. Token: `{{access_token}}`

Or set this once on the **Collection** level so all requests inherit it.

---

### Step 5 — Register a Doctor

- **Method:** POST
- **URL:** `{{base_url}}/auth/register/doctor/`
- **Body:**

```json
{
    "email": "doctor@healix.com",
    "first_name": "Karim",
    "last_name": "Benali",
    "phone_number": "+213555000002",
    "password": "Test1234!",
    "password_confirm": "Test1234!",
    "specialty": "Cardiology",
    "license_number": "DZ-MED-12345",
    "years_of_experience": 10,
    "clinic_name": "Benali Heart Clinic",
    "clinic_address": "12 Rue Didouche Mourad, Algiers",
    "consultation_fee": "2000.00",
    "bio": "Specialist in interventional cardiology."
}
```

Then go to http://127.0.0.1:8000/admin/ → Doctor Profiles → select the doctor → use **"Verify selected doctors"** action. Doctors must be verified before they appear in search.

---

### Step 6 — Add Doctor Availability (as Doctor)

Login as the doctor first to get a doctor token, then:

- **Method:** POST
- **URL:** `{{base_url}}/doctors/me/availability/`
- **Auth:** Bearer token (doctor's)
- **Body:**

```json
{
    "day_of_week": 0,
    "start_time": "09:00",
    "end_time": "17:00",
    "slot_duration_minutes": 30,
    "max_patients": 1
}
```

Repeat for other days (0=Monday … 6=Sunday).

---

### Step 7 — Search Doctors (as Patient)

- **Method:** GET
- **URL:** `{{base_url}}/doctors/`
- **Auth:** None required

With filters:
```
{{base_url}}/doctors/?specialty=Cardiology&min_rating=0&available=true
```

Nearby search:
```
{{base_url}}/doctors/?lat=36.7525&lng=3.04197&radius_km=10
```

---

### Step 8 — Check Available Slots

- **Method:** GET
- **URL:** `{{base_url}}/doctors/1/slots/?date=2026-03-20`
- **Auth:** None required

Returns a list of time slots with `is_available: true/false`.

---

### Step 9 — Book an Appointment (as Patient)

- **Method:** POST
- **URL:** `{{base_url}}/appointments/book/`
- **Auth:** Bearer token (patient's)
- **Body:**

```json
{
    "doctor": 1,
    "appointment_date": "2026-03-20",
    "appointment_time": "10:00",
    "appointment_type": "in_person",
    "reason_for_visit": "Chest pain evaluation",
    "symptoms": "Occasional shortness of breath"
}
```

---

### Step 10 — Check Queue Status (as Patient)

- **Method:** GET
- **URL:** `{{base_url}}/appointments/1/queue/`
- **Auth:** Bearer token (patient's)

Returns your position in the queue and estimated wait time.

---

### Step 11 — Doctor Updates Appointment Status

Login as doctor, then:

- **Method:** PATCH
- **URL:** `{{base_url}}/appointments/1/update/`
- **Auth:** Bearer token (doctor's)
- **Body:**

```json
{
    "status": "confirmed"
}
```

Valid status transitions:
- `pending` → `confirmed` or `cancelled`
- `confirmed` → `in_progress`, `cancelled`, or `no_show`
- `in_progress` → `completed`

---

### Step 12 — Scan a Prescription (as Patient)

- **Method:** POST
- **URL:** `{{base_url}}/prescriptions/scan/`
- **Auth:** Bearer token (patient's)
- **Body** → **form-data** (not JSON):
  - Key: `image` | Type: File | Value: select any image file

Returns identified medicines and which nearby pharmacies have them in stock.

---

### Quick Reference — All Endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/auth/register/patient/` | ❌ | Register patient |
| POST | `/auth/register/doctor/` | ❌ | Register doctor |
| POST | `/auth/register/pharmacy/` | ❌ | Register pharmacy |
| POST | `/auth/login/` | ❌ | Login |
| POST | `/auth/logout/` | ✅ | Logout |
| POST | `/auth/token/refresh/` | ❌ | Refresh token |
| GET/PATCH | `/auth/me/` | ✅ | My account |
| GET/PATCH | `/patients/profile/` | Patient | Medical profile |
| GET | `/doctors/` | ❌ | Search doctors |
| GET | `/doctors/specialties/` | ❌ | List specialties |
| GET | `/doctors/{id}/` | ❌ | Doctor detail |
| GET | `/doctors/{id}/slots/?date=` | ❌ | Available slots |
| GET | `/doctors/{id}/reviews/` | ❌ | Doctor reviews |
| POST | `/doctors/{id}/reviews/add/` | Patient | Submit review |
| GET/PATCH | `/doctors/me/profile/` | Doctor | My doctor profile |
| GET/POST | `/doctors/me/availability/` | Doctor | Manage schedule |
| POST | `/appointments/book/` | Patient | Book appointment |
| GET | `/appointments/my/` | Patient | My appointments |
| GET | `/appointments/{id}/` | Patient/Doctor | Appointment detail |
| POST | `/appointments/{id}/cancel/` | Patient/Doctor | Cancel |
| GET | `/appointments/{id}/queue/` | Patient | Queue status |
| GET/POST | `/appointments/{id}/messages/` | Patient/Doctor | Chat |
| GET | `/appointments/doctor/list/` | Doctor | All appointments |
| GET | `/appointments/doctor/queue/` | Doctor | Today's queue |
| GET | `/appointments/doctor/dashboard/` | Doctor | Stats |
| PATCH | `/appointments/{id}/update/` | Doctor | Update status |
| GET | `/pharmacies/` | ❌ | Search pharmacies |
| GET | `/pharmacies/{id}/` | ❌ | Pharmacy + inventory |
| GET | `/medicines/` | ❌ | Search medicines |
| GET | `/medicines/{id}/availability/` | ❌ | Where to buy |
| GET/POST | `/pharmacies/me/inventory/` | Pharmacy | My inventory |
| GET/PATCH/DELETE | `/pharmacies/me/inventory/{id}/` | Pharmacy | Update stock |
| GET | `/prescriptions/my/` | Patient | My prescriptions |
| GET | `/prescriptions/{id}/` | Patient/Doctor | Detail |
| POST | `/prescriptions/scan/` | Patient | Scan image |
| GET | `/prescriptions/scan/history/` | Patient | Scan history |
| POST | `/prescriptions/create/` | Doctor | Issue prescription |

---

## User Roles

| Role | What they can do |
|------|-----------------|
| `patient` | Book appointments, scan prescriptions, leave reviews, chat |
| `doctor` | Manage schedule, update appointments, issue prescriptions, chat |
| `pharmacy` | Manage medicine inventory |
| `admin` | Full access via /admin/ panel, verify doctors & pharmacies |

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `no such table: users` | Migrations not run | Run `makemigrations` then `migrate` |
| `401 Unauthorized` | Missing or expired token | Login again, use Bearer token in Auth header |
| `403 Forbidden` | Wrong role for endpoint | Check you're logged in with the right account type |
| `400 - This time slot is already booked` | Slot conflict | Use `/doctors/{id}/slots/?date=` to find free slots |
| `400 - Doctor has no availability at this time` | Outside schedule | Doctor must first add availability slots |
| `Doctor not found` in search | Doctor not verified | Admin must verify the doctor in /admin/ |
#   t e m p h e a l i x  
 