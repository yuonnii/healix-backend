# Healix

A healthcare platform that connects patients, doctors, and pharmacies through a single REST API. It also connect with a physical (a wokwi simulation for now) IoT device (ESP32) that streams patient vitals directly to the doctor's dashboard during consultations.

## What it does

**For patients:** search for doctors by specialty, rating, fee, and location and book an appointment, track your live queue position, chat with the doctor, and scan a prescription photo to find which nearby pharmacy has your medicines in stock.

**For doctors:** manage your weekly schedule, handle your daily queue with status updates, read your patient's live heart rate / temperature / SpO2 from the IoT device mid consultation, write diagnoses, and issue digital prescriptions.

**For pharmacies:** manage your medicine inventory and stock levels, prices, expiry dates and automatically appear in patient searches when someone needs a medicine you carry.

**For admins:** verify doctor and pharmacy accounts before they go public, and manage everything through the Django admin panel.

## Tech stack

| Backend = Django 5.0.4 + Django REST Framework 3.15.1 
| Authentication = SimpleJWT -> access tokens (1 hr) + refresh tokens (7 days, blacklisted on logout) 
| Database = SQLite
| IoT device = ESP32 (Wokwi simulator) with DS18B20 temperature sensor
| API docs = drf-spectacular -> Swagger UI at `/api/docs/`
| Filtering = django-filter
| Tunnel (demo) = ngrok -> exposes local server to the Wokwi simulator

## Project structure 

healix/
── healix/           # Core settings, URL router, permissions, exception handler
── accounts/         # Custom User model, JWT auth, patient profiles
── doctors/          # Doctor profiles, search/filter, scheduling, reviews
── appointments/     # Booking, smart queue system, in app messaging
── pharmacies/       # Pharmacy profiles, medicines, inventory management
── prescriptions/    # Digital prescriptions + prescription image scanning
── vitals/           # IoT device readings
── core/             # Management commands (database seeder)


## Database design

Everything lives in a single SQLite database. The schema is split across 15 tables:

| `users` | Single auth table for all roles. Login by email. |
| `patient_profiles` | Blood type, allergies, chronic conditions, GPS location |
| `doctor_profiles` | Specialty, license, fee, bio, GPS, cached avg rating |
| `specialties` | Cardiologie, Pédiatrie, Neurologie, etc. |
| `doctor_availability` | Weekly recurring schedule blocks per doctor |
| `doctor_reviews` | Rating + comment. Saving one auto-updates the doctor's cached average. |
| `appointments` | Full lifecycle with queue number, timestamps, diagnosis |
| `messages` | Chat thread scoped to each appointment |
| `pharmacies` | Pharmacy profiles |
| `medicines` | Global catalog : Doliprane, Augmentin, Glucophage, etc. |
| `pharmacy_inventory` | Stock per pharmacy per medicine (quantity, price, expiry) |
| `prescriptions` | Doctor issued prescriptions linked to appointments |
| `prescription_items` | Individual medicine lines per prescription |
| `vital_readings` | Heart rate, temperature, SpO2 readings from the IoT device. Alert flags computed on save. |
| `device_tokens` | IoT device registry : maps each device to a patient |

IMPORTANT:
- All user types (patient, doctor, pharmacy, admin) share one `users` table. The `role` field determines what they can do.
- Queue numbers are assigned at booking time. Queue position is computed live by counting how many confirmed/in_progress appointments for the same doctor on the same day have a lower queue number.
- Alert flags on `vital_readings` (`is_fever`, `is_tachycardia`, `is_low_spo2`, `has_alert`) are computed automatically on every save — fever if temp > 38°C, tachycardia if HR > 110 BPM, low SpO2 if below 95%.


## API reference

**Base URL:** `http://localhost:8000/api/v1`  
**Interactive docs:** `http://localhost:8000/api/docs/`  
**Auth header:** `Authorization: Bearer <access_token>`  
**IoT device header:** `X-Device-Key: <device_token>`

### Authentication
POST   /auth/register/patient/      Register patient (tokens returned immediately)
POST   /auth/register/doctor/       Register doctor (visible after admin verification)
POST   /auth/register/pharmacy/     Register pharmacy (visible after admin verification)
POST   /auth/login/                 Email + password -> access + refresh tokens
POST   /auth/logout/                Blacklist refresh token
POST   /auth/token/refresh/         Exchange refresh -> new access token
POST   /auth/change-password/       Requires current password
GET    /auth/me/                    Current user info + role
PATCH  /auth/me/                    Update name, phone, profile picture

### Doctors
GET    /doctors/                              Search (specialty, rating, fee, location, language)
GET    /doctors/specialties/                  All specialties (for dropdowns)
GET    /doctors/{id}/                         Full doctor profile
GET    /doctors/{id}/slots/?date=YYYY-MM-DD   Available time slots on a date
GET    /doctors/{id}/reviews/                 Paginated reviews
POST   /doctors/{id}/reviews/add/             Submit review (patient only, needs completed appt)
GET    /doctors/me/profile/                   Doctor's own profile
PATCH  /doctors/me/profile/                   Update specialty, bio, fee, clinic info
GET    /doctors/me/availability/              Own schedule
POST   /doctors/me/availability/              Add schedule block
PATCH  /doctors/me/availability/{id}/         Edit schedule block
DELETE /doctors/me/availability/{id}/         Remove schedule block

Doctor search supports these query params: `specialty`, `min_rating`, `max_fee`, `min_fee`, `min_experience`, `available` (true/false), `verified`, `language`, `search`, `ordering`, `lat`, `lng`, `radius_km`.

### Appointments
POST   /appointments/book/                    Book a slot (validates against doctor's schedule)
GET    /appointments/my/                      Patient's appointments (?status= filter)
GET    /appointments/{id}/                    Appointment detail
POST   /appointments/{id}/cancel/             Cancel with optional reason
GET    /appointments/{id}/queue/              Live queue position + estimated wait (patient)
GET    /appointments/{id}/messages/           Message thread (auto-marks unread)
POST   /appointments/{id}/messages/           Send message
GET    /appointments/doctor/list/             All appointments (?status=&date= filter)
PATCH  /appointments/{id}/update/             Update status + notes + diagnosis (doctor)
GET    /appointments/doctor/queue/            Today's queue with per-status counts
GET    /appointments/doctor/dashboard/        Stats: today / this week / all time

Status transitions: `pending -> confirmed -> in_progress -> completed`, with `cancelled` and `no_show` branches. Invalid transitions return a 400.

### Pharmacies and medicines
GET    /pharmacies/                           Search (?lat=&lng=&radius_km=)
GET    /pharmacies/{id}/                      Pharmacy detail + inventory
GET    /medicines/                            Search medicines (accent-insensitive)
GET    /medicines/{id}/availability/          Pharmacies that have this medicine in stock
GET    /pharmacies/me/inventory/              Own inventory
POST   /pharmacies/me/inventory/              Add medicine
PATCH  /pharmacies/me/inventory/{id}/         Update stock or price
DELETE /pharmacies/me/inventory/{id}/         Remove

### Prescriptions
GET    /prescriptions/my/                     Patient's prescriptions
GET    /prescriptions/{id}/                   Detail with all items
POST   /prescriptions/scan/                   Upload photo -> identify medicines + nearby pharmacies
GET    /prescriptions/scan/history/           Past scans
POST   /prescriptions/create/                 Issue prescription (doctor)

Scan endpoint is `multipart/form-data`, field name `image`. Optional query params `?lat=&lng=&radius_km=` filter pharmacy results by proximity.

### Vitals
POST   /vitals/push/                          Device pushes reading (X-Device-Key, no JWT)
GET    /vitals/patient/{id}/                  All readings for a patient (?alerts_only=true)
GET    /vitals/patient/{id}/latest/           Single most recent reading
GET    /vitals/appointment/{id}/              Readings for an appointment + session stats
GET    /vitals/me/                            Patient views own history
GET    /vitals/devices/                       List registered devices (admin)
POST   /vitals/devices/                       Register device + generate token (admin)
PATCH  /vitals/devices/{id}/                  Enable / disable device (admin)

### Response format
Every endpoint returns the same envelope:

```json
// success
{ "success": true, "message": "...", "data": { } }

// paginated list
{ "success": true, "pagination": { "count": 48, "total_pages": 3, "current_page": 1, "next": "...", "previous": null }, "results": [ ] }

// error
{ "success": false, "error": { "status_code": 400, "message": "...", "details": { } } }
```

## IoT device

The ESP32 reads a DS18B20 temperature sensor and a potentiometer (simulating heart rate and SpO2), displays readings on an OLED, and lights up a LED + buzzer when any threshold is exceeded.

It authenticates with the API using a static `X-Device-Key` header, no login flow on the device. Each token is registered in the `device_tokens` table and linked to a specific patient, so the server always knows who the reading belongs to.

To connect a Wokwi device to a locally running server i used ngrok:

# terminal 1
python manage.py runserver

# terminal 2
ngrok http 8000
# -> https://link-given-by-ngrok


Then in Wokwi:
const char* serverName = "https://link-given-by-ngrok/api/v1/vitals/push/";
const char* deviceKey  = "insert-token-here";

Register a device by calling `POST /api/v1/vitals/devices/` as admin and copying the returned token.

## Setup

**Requirements:** Python 3.10+, optionally ngrok for IoT testing.

# 1. Clone and set up virtual environment
git clone https://github.com/your-username/healix.git
cd healix
python -m venv venv

# Windows
.venv\Scripts\activate
# Mac / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env

# 4. Create admin account
python manage.py createsuperuser
(My existing one is Gmail: admin@gmail.com / PW: adminadmin)

# 5. Start
python manage.py runserver

### Demo accounts 
All passwords are `Healix2026!` aside for admin.

Patient = sara.benali@healix-demo.dz 
Doctor = dr.karim.benali@healix-demo.dz 
Pharmacy = pharmacie_centrale_dalg_0@healix-demo.dz 
Admin = admin@gmail.com (pw = adminadmin)
 #   h e a l i x - b a c k e n d 
 
 #   h e a l i x - b a c k e n d 
 
 #   h e a l i x - b a c k e n d 
 
 
