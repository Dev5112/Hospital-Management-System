# Hospital Management System (HMS) REST API

A complete JSON-based REST API for Hospital Management System built with Flask-RESTful in Python.

## Features

- ✅ JWT-based Authentication with Role-Based Access Control (RBAC)
- ✅ 5 HTTP Methods: GET, POST, PUT, PATCH, DELETE
- ✅ Standardized JSON Response Envelopes
- ✅ Input Validation & Error Handling
- ✅ Comprehensive Error Responses with Field-Level Errors
- ✅ Pagination Support
- ✅ Database Integrity with Foreign Keys & Constraints
- ✅ CORS Enabled for Cross-Origin Requests
- ✅ Request/Response Logging
- ✅ Pytest Test Suite with Fixtures
- ✅ Production-Ready Code with Full Type Hints

## Project Structure

```
hms/api/
├── config.py                  # API configuration (JWT, DB path, constants)
├── database.py                # Database wrapper for queries
├── app.py                     # Flask app factory
├── middleware.py              # Error handlers, CORS, logging
├── utils/
│   ├── response.py            # Standardized response builders
│   ├── validators.py          # Input validation utilities
│   └── auth_helper.py         # JWT encode/decode, decorators
└── resources/
    ├── auth.py                # Login/Logout endpoints
    ├── doctors.py             # Doctor CRUD operations
    ├── patients.py            # Patient CRUD operations
    ├── appointments.py        # Appointment booking
    ├── billing.py             # Billing management
    └── wards.py               # Ward management

tests/
├── test_doctors.py            # Doctor resource tests
├── test_patients.py           # Patient resource tests
└── test_appointments.py       # Appointment resource tests
```

## Quick Start

### Installation

```bash
# Clone/navigate to project
cd "MAD1 Proj"

# Create virtual environment (macOS/Linux)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Server

```bash
# Start development server
python run.py

# Server runs at http://localhost:5000
# Debug mode is ON by default
```

## Authentication

### Roles & Default Credentials

```
admin:    username=admin,    password=admin123    (Full access)
doctor:   username=doctor,   password=doctor123   (Limited access)
patient:  username=patient,  password=patient123  (Personal data only)
```

### Login Flow

1. POST `/api/auth/login` with credentials
2. Receive JWT token in response
3. Include token in `Authorization: Bearer <token>` header for protected endpoints

## API Response Format

### Success Response
```json
{
  "status": "success",
  "code": 200,
  "data": { /* response data */ },
  "message": "Operation successful",
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total": 50,
    "total_pages": 5
  }
}
```

### Error Response
```json
{
  "status": "error",
  "code": 400,
  "data": null,
  "message": "Validation failed",
  "errors": {
    "email": "Invalid email format",
    "phone": "Must be 10 digits"
  }
}
```

## API Endpoints

### Authentication

#### Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Response:**
```json
{
  "status": "success",
  "code": 200,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "username": "admin",
    "role": "admin",
    "expires_in": 86400
  },
  "message": "Login successful"
}
```

#### Logout
```bash
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### Doctors

#### Get All Doctors
```bash
curl -X GET "http://localhost:5000/api/doctors?specialization=Cardiology&page=1&limit=10"
```

#### Create Doctor (Admin Only)
```bash
curl -X POST http://localhost:5000/api/doctors \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Dr. Smith",
    "specialization": "Cardiology",
    "phone": "9876543210",
    "email": "smith@hospital.com",
    "available_days": "Mon-Fri"
  }'
```

#### Get Single Doctor
```bash
curl -X GET http://localhost:5000/api/doctors/1
```

#### Update Doctor (Full)
```bash
curl -X PUT http://localhost:5000/api/doctors/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Dr. Smith Updated",
    "specialization": "Neurology",
    "phone": "9876543211",
    "email": "smith.new@hospital.com",
    "available_days": "Mon-Sat"
  }'
```

#### Partial Update Doctor
```bash
curl -X PATCH http://localhost:5000/api/doctors/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "phone": "9876543211",
    "available_days": "Mon-Sat"
  }'
```

#### Delete Doctor (Soft Delete)
```bash
curl -X DELETE http://localhost:5000/api/doctors/1 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

#### Get Doctor's Appointments
```bash
curl -X GET "http://localhost:5000/api/doctors/1/appointments?status=scheduled"
```

---

### Patients

#### Register Patient
```bash
curl -X POST http://localhost:5000/api/patients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "dob": "1990-05-15",
    "gender": "M",
    "phone": "9876543210",
    "address": "123 Main St",
    "blood_group": "A+"
  }'
```

#### Get All Patients (Admin/Doctor)
```bash
curl -X GET "http://localhost:5000/api/patients?blood_group=A+&gender=M&page=1&limit=10" \
  -H "Authorization: Bearer TOKEN"
```

#### Get Single Patient
```bash
curl -X GET http://localhost:5000/api/patients/1
```

#### Update Patient (Full)
```bash
curl -X PUT http://localhost:5000/api/patients/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "Jane Doe",
    "dob": "1990-05-15",
    "gender": "F",
    "phone": "9876543211",
    "blood_group": "B+"
  }'
```

#### Partial Update Patient
```bash
curl -X PATCH http://localhost:5000/api/patients/1 \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543211",
    "address": "456 Oak Ave"
  }'
```

#### Get Patient Appointments
```bash
curl -X GET "http://localhost:5000/api/patients/1/appointments?status=completed"
```

#### Get Patient Medical Records
```bash
curl -X GET http://localhost:5000/api/patients/1/medical-records
```

#### Get Patient Billing
```bash
curl -X GET "http://localhost:5000/api/patients/1/billing?status=unpaid"
```

---

### Appointments

#### Book Appointment
```bash
curl -X POST http://localhost:5000/api/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 1,
    "doctor_id": 1,
    "appointment_date": "2025-12-01",
    "time_slot": "10:00"
  }'
```

#### Get All Appointments (Admin/Doctor)
```bash
curl -X GET "http://localhost:5000/api/appointments?date=2025-12-01&status=scheduled&doctor_id=1" \
  -H "Authorization: Bearer TOKEN"
```

#### Get Single Appointment
```bash
curl -X GET http://localhost:5000/api/appointments/1
```

#### Reschedule Appointment
```bash
curl -X PUT http://localhost:5000/api/appointments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "appointment_date": "2025-12-02",
    "time_slot": "14:00"
  }'
```

#### Update Appointment Status
```bash
curl -X PATCH http://localhost:5000/api/appointments/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "status": "completed",
    "notes": "Patient is recovering well"
  }'
```

#### Cancel Appointment
```bash
curl -X DELETE http://localhost:5000/api/appointments/1 \
  -H "Authorization: Bearer TOKEN"
```

#### Get Available Slots
```bash
curl -X GET "http://localhost:5000/api/appointments/available-slots?doctor_id=1&date=2025-12-01"
```

#### Get Today's Appointments (Admin/Doctor)
```bash
curl -X GET http://localhost:5000/api/appointments/today \
  -H "Authorization: Bearer TOKEN"
```

---

### Billing

#### Get All Bills (Admin)
```bash
curl -X GET "http://localhost:5000/api/billing?status=unpaid&page=1&limit=10" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

#### Create Bill (Admin)
```bash
curl -X POST http://localhost:5000/api/billing \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "patient_id": 1,
    "total_amount": 5000,
    "services": ["Consultation", "Lab Test"]
  }'
```

#### Get Single Bill
```bash
curl -X GET http://localhost:5000/api/billing/1
```

#### Record Payment
```bash
curl -X PATCH http://localhost:5000/api/billing/1/pay \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "amount": 2000,
    "payment_method": "cash"
  }'
```

#### Get Billing Summary (Admin)
```bash
curl -X GET http://localhost:5000/api/billing/summary \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

### Wards

#### Get All Wards
```bash
curl -X GET "http://localhost:5000/api/wards?type=ICU&page=1&limit=10"
```

#### Create Ward (Admin)
```bash
curl -X POST http://localhost:5000/api/wards \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "name": "ICU Ward A",
    "ward_type": "ICU",
    "total_beds": 20,
    "available_beds": 20
  }'
```

#### Get Single Ward
```bash
curl -X GET http://localhost:5000/api/wards/1
```

#### Update Bed Availability
```bash
curl -X PATCH http://localhost:5000/api/wards/1/beds \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -d '{
    "action": "admit",
    "count": 2
  }'
```

#### Get Ward Occupancy (Admin)
```bash
curl -X GET http://localhost:5000/api/wards/occupancy \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_doctors.py -v

# Run specific test
pytest tests/test_doctors.py::test_create_doctor_success -v

# Run with coverage
pytest --cov=hms.api tests/
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200  | OK - Request successful |
| 201  | Created - Resource created |
| 400  | Bad Request - Invalid input |
| 401  | Unauthorized - Missing/invalid token |
| 403  | Forbidden - Insufficient permissions |
| 404  | Not Found - Resource doesn't exist |
| 405  | Method Not Allowed |
| 409  | Conflict - Resource already exists |
| 500  | Internal Server Error |

## Validation Rules

### Email
- Standard email format required
- Must be unique per doctor

### Phone
- Exactly 10 digits required
- Must be unique per doctor/patient

### Blood Groups
- Valid: A+, A-, B+, B-, AB+, AB-, O+, O-

### Time Slots
- 30-minute intervals from 09:00 to 17:30
- Valid slots: 09:00, 09:30, 10:00, ..., 17:30

### Appointment Dates
- Cannot be in the past
- Must be YYYY-MM-DD format

### Genders
- M, F, or Other

## Environment Variables

```bash
FLASK_ENV=development      # development, testing, production
FLASK_DEBUG=True          # Debug mode (True/False)
PORT=5000                 # Server port
HOST=0.0.0.0              # Bind address
DB_PATH=hms.db            # Database file path
JWT_SECRET_KEY=your-key   # JWT signing key (change in production!)
```

## Security Notes

⚠️ **Important for Production:**

1. Change `JWT_SECRET_KEY` in configuration
2. Use HTTPS only in production
3. Implement rate limiting
4. Use environment variables for sensitive data
5. Add input sanitization for SQL injection prevention
6. Implement CORS whitelisting for specific origins
7. Add API authentication for CI/CD pipelines

## Architecture Highlights

### Design Patterns
- **Factory Pattern**: Flask app factory in `app.py`
- **Decorator Pattern**: `@token_required`, `@role_required` for auth
- **Context Manager**: Database connection management
- **Resource Pattern**: Flask-RESTful resource-based routing

### Best Practices
- ✅ All DB queries are parameterized (prevents SQL injection)
- ✅ Comprehensive input validation
- ✅ Proper HTTP status codes
- ✅ Standardized response format
- ✅ Request logging and error tracking
- ✅ Role-based access control
- ✅ Soft deletes for data preservation
- ✅ Full transaction support with rollback

## Troubleshooting

### Import Errors
Ensure you've installed dependencies:
```bash
pip install -r requirements.txt
```

### Database Errors
Ensure database permissions and correct path in config.

### Authentication Fails
- Verify token is correctly formatted in Authorization header
- Check token expiration (24 hours by default)
- Verify user role has access to endpoint

## Future Enhancements

- [ ] Email notifications for appointments
- [ ] SMS reminders
- [ ] Advanced reporting and analytics
- [ ] Appointment rescheduling API
- [ ] Patient health records export
- [ ] Multi-language support
- [ ] Mobile app backend integration
- [ ] Real-time updates with WebSockets
- [ ] Database query optimization and caching
- [ ] API documentation with Swagger/OpenAPI

## Technologies Used

- **Framework**: Flask 3.0.0
- **API**: Flask-RESTful 0.3.10
- **Authentication**: PyJWT 2.8.0
- **Database**: SQLite3
- **Testing**: pytest 7.4.4
- **CORS**: Flask-CORS 4.0.0

## License

This project is for educational purposes.

---

**Questions?** Check the extensive curl examples in this README or review the test files for more usage patterns.
