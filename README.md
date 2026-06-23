# Task Manager

A full-stack personal task management application built with **FastAPI**, **SQLite**, **Streamlit**, and **Python 3.11+**.  
It allows users to register, log in, and manage their personal tasks through a clean web interface. Users can create, update, delete, filter, and track tasks with priority, status, and due date support.

## Overview

This project was developed as part of an internship to demonstrate backend API development, authentication, database integration, and frontend interaction in Python. The backend provides API endpoints for authentication and task management, while the frontend offers a user-friendly dashboard for daily productivity.

## Tech Stack

- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Database:** SQLite
- **Language:** Python 3.11+
- **Authentication:** Token-based authentication with Passlib and bcrypt
- **Validation:** Pydantic
- **HTTP Client:** Requests

## Features

- User registration
- User login and authenticated access
- Create tasks
- View all personal tasks
- View task details
- Update tasks
- Delete tasks
- Update task status
- Filter tasks by status and priority
- Completed / archive task view
- Task summary dashboard
- SQLite-based persistent storage

## Project Structure

```text
TASK-MANAGER/
│   .gitignore
│   README.md
│   requirements.txt
│
├── backend/
│   │   auth.py
│   │   database.py
│   │   main.py
│   │   schemas.py
│   │
│   └── routers/
│       │   tasks.py
│       │   users.py
│
└── frontend/
    │   app.py

Author

Hiba Fathima M
B.Tech Computer Science & Engineering
MEA Engineering College
