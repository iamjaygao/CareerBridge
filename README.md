# CareerBridge

**CareerBridge** is an AI-powered career prep platform designed to help students and early professionals land internships and full-time positions. The platform provides automated resume analysis, mentor booking, and mock interview scheduling.

---

## 🚀 Features

### 🧠 AI Resume Analysis
- Upload your resume in PDF format
- Get instant feedback using OpenAI-powered scoring
- Receive suggestions to improve ATS compatibility and technical skill matching

### 👥 Mentor Marketplace
- Browse available mentors with real-world experience
- Book resume reviews or mock interviews 
- Integrated payment system using Stripe

### 📅 Mock Interview Booking System
- Mentor availability shown in calendar interface
- Select preferred time slot and mentor
- Receive confirmation and calendar invite

### 👤 User Management
- Register/login with JWT-based authentication
- Track resume uploads, booking history, and feedback

### 🔔 Notification System
- Alerts for upcoming mock interviews
- Resume feedback ready notifications
- Mentor messages

---

## 🧰 Tech Stack

| Layer     | Technology              |
|-----------|--------------------------|
| Frontend  | React, Tailwind CSS      |
| Backend   | Django REST Framework    |
| Database  | PostgreSQL               |
| AI        | OpenAI API / Custom NLP  |
| Payments  | Stripe API               |
| Storage   | AWS S3 or Firebase       |
| Auth      | JWT (JSON Web Token)     |

---

## 📦 Project Structure

```plaintext
careerbridge/
├── backend/
│   ├── api/
│   ├── auth/
│   ├── resume_analysis/
│   └── ...
├── frontend/
│   ├── src/
│   ├── components/
│   └── pages/
└── README.md
