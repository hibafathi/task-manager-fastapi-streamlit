# Task Manager

A full-stack personal task management application built with **FastAPI**, **SQLite**, and **Streamlit**. This project was developed as part of an internship to demonstrate backend API development, authentication, database integration, and frontend interaction in Python.

## Overview

The application allows users to register, log in, and manage their personal tasks through a clean web interface. Each user can create, view, update, delete, and track tasks with priority, status, and due date fields. The backend provides secure API endpoints, while the frontend offers an interactive dashboard for daily task management.

## Tech Stack

- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Database:** SQLite
- **Authentication:** Token-based authentication with Passlib and bcrypt
- **Validation:** Pydantic
- **HTTP Client:** Requests
- **Language:** Python 3

## Features

- User registration
- User login and authenticated access
- Create new tasks
- View all personal tasks
- View task details
- Update existing tasks
- Delete tasks
- Update task status
- Filter tasks by status and priority
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

Internship Domain

Python | FastAPI | Streamlit
