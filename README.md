# 🧠 Smart Timetable Management System

An AI-assisted smart timetable generator with conflict resolution, multi-role interface (admin, teacher, student), and downloadable scheduling formats.

---

## 🚀 Features

- 🧩 Auto-generated timetable with conflict resolution
- 👨‍🏫 Admin/Teacher/Student roles
- 📥 Download in CSV/Excel format
- 📊 Streamlit dashboard interface
- 📡 Flask-based API with PostgreSQL backend

---

## 🖥️ Local Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/dibyacharyaAI/smart-timetable-final-db.git
cd smart-timetable-final-db
```

### 2. Create and Activate Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🛠️ Environment Variables

Create a `.env` file in the root directory:

```bash
touch .env
```

Add this line to `.env`:

```env
SQLALCHEMY_DATABASE_URI=postgresql://postgres:12345@localhost:5432/smart_timetable
```

Make sure:
- PostgreSQL is installed and running
- Database `smart_timetable` is created in pgAdmin or CLI
- Username/password matches

---

## ▶️ Run Flask App

```bash
python app_server.py
```

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

Default admin may be:
```
email: admin
password: admin123
```

---

## 🧪 API Testing (via `curl` or Postman)

Login:

```bash
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d "email=admin&password=admin123"
```

Fetch timetable:

```bash
curl -b cookies.txt http://127.0.0.1:5000/api/timetable
```

---

## 📊 Optional: Run Streamlit Panels

Admin:

```bash
streamlit run streamlit_admin.py
```

Teacher:

```bash
streamlit run streamlit_teacher.py
```

Student:

```bash
streamlit run streamlit_student.py
```

---

## 📁 Folder Structure

```
.
├── app.py
├── app_server.py
├── models.py
├── routes/
├── static/
├── templates/
├── .env.example
├── requirements.txt
└── streamlit_admin.py (and others)
```

---

## 👨‍💻 Author

[@dibyacharyaAI](https://github.com/dibyacharyaAI)

---

## 🛡️ License

MIT License – feel free to use, modify, and distribute.
