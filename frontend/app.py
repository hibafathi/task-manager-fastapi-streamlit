# File: frontend/app.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 10


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "page": "login",
        "token": None,
        "email": None,
        "selected_task_id": None,
        "delete_task_id": None,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_custom_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
            }

            [data-testid="stSidebar"] * {
                color: #f9fafb !important;
            }

            .app-title {
                font-size: 2.2rem;
                font-weight: 700;
                color: #111827;
                margin-bottom: 0.25rem;
            }

            .app-subtitle {
                color: #4b5563;
                font-size: 1rem;
                margin-bottom: 1.25rem;
            }

            .section-title {
                font-size: 1.45rem;
                font-weight: 700;
                color: #111827;
                margin-top: 0.75rem;
                margin-bottom: 0.75rem;
            }

            .summary-card {
                background: white;
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                border: 1px solid #e5e7eb;
            }

            .summary-label {
                color: #6b7280;
                font-size: 0.95rem;
                margin-bottom: 0.25rem;
            }

            .summary-value {
                color: #111827;
                font-size: 1.8rem;
                font-weight: 700;
            }

            .panel {
                background: white;
                border-radius: 20px;
                padding: 1.1rem 1.2rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                border: 1px solid #e5e7eb;
                margin-bottom: 1rem;
            }

            .task-card {
                background: white;
                border-radius: 18px;
                padding: 1rem 1rem 0.85rem 1rem;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
                border: 1px solid #e5e7eb;
                margin-bottom: 0.9rem;
            }

            .task-card-title {
                color: #111827;
                font-size: 1.1rem;
                font-weight: 700;
                margin-bottom: 0.35rem;
            }

            .task-card-desc {
                color: #4b5563;
                font-size: 0.95rem;
                margin-bottom: 0.85rem;
            }

            .task-meta {
                color: #6b7280;
                font-size: 0.9rem;
                margin-bottom: 0.5rem;
            }

            .badge {
                display: inline-block;
                padding: 0.28rem 0.65rem;
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 700;
                margin-right: 0.4rem;
                margin-bottom: 0.35rem;
            }

            .badge-status-pending {
                background: #fff7ed;
                color: #c2410c;
                border: 1px solid #fdba74;
            }

            .badge-status-in-progress {
                background: #eff6ff;
                color: #1d4ed8;
                border: 1px solid #93c5fd;
            }

            .badge-status-done {
                background: #ecfdf5;
                color: #047857;
                border: 1px solid #86efac;
            }

            .badge-priority-low {
                background: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
            }

            .badge-priority-medium {
                background: #fffbeb;
                color: #b45309;
                border: 1px solid #fcd34d;
            }

            .badge-priority-high {
                background: #fef2f2;
                color: #b91c1c;
                border: 1px solid #fca5a5;
            }

            .detail-grid {
                background: white;
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
                border: 1px solid #e5e7eb;
            }

            .detail-label {
                color: #6b7280;
                font-size: 0.9rem;
                margin-bottom: 0.15rem;
            }

            .detail-value {
                color: #111827;
                font-size: 1rem;
                font-weight: 600;
                margin-bottom: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_auth_headers() -> dict[str, str]:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def api_call(
    method: str,
    endpoint: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    require_auth: bool = False,
) -> tuple[bool, Any]:
    url = f"{API_BASE_URL}{endpoint}"
    headers = get_auth_headers() if require_auth else {}

    try:
        response = requests.request(
            method=method,
            url=url,
            json=json,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.ConnectionError:
        return False, "Backend server is not running. Start FastAPI first."
    except requests.exceptions.Timeout:
        return False, "Request timed out. Please try again."
    except requests.exceptions.RequestException as exc:
        return False, f"Request failed: {exc}"

    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text or "Unknown server response"}

    if 200 <= response.status_code < 300:
        return True, data

    if response.status_code == 401 and require_auth:
        st.session_state["token"] = None
        st.session_state["email"] = None
        st.session_state["page"] = "login"

    detail = data.get("detail", "Something went wrong.")
    return False, detail


def go_to(page: str, *, task_id: int | None = None) -> None:
    st.session_state["page"] = page
    if task_id is not None:
        st.session_state["selected_task_id"] = task_id
    st.rerun()


def logout() -> None:
    st.session_state["token"] = None
    st.session_state["email"] = None
    st.session_state["selected_task_id"] = None
    st.session_state["delete_task_id"] = None
    st.session_state["page"] = "login"
    st.rerun()


def format_due_date(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value).date().isoformat()
    except ValueError:
        return value


def parse_due_date_for_input(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None


def require_login() -> bool:
    if not st.session_state.get("token"):
        st.warning("Please login first.")
        st.session_state["page"] = "login"
        return False
    return True


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='app-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='app-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("## Task Manager")
        st.caption("FastAPI + Streamlit")

        email = st.session_state.get("email")
        if email:
            st.markdown(f"**Logged in as**  \n{email}")
            st.divider()

            if st.button("Dashboard", use_container_width=True):
                go_to("dashboard")
            if st.button("Add Task", use_container_width=True):
                go_to("add_task")
            if st.button("Logout", use_container_width=True):
                logout()
        else:
            st.write("Please login or register to continue.")


def render_login_page() -> None:
    render_page_header("Welcome Back", "Sign in to continue managing your tasks.")

    with st.container():
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if not email.strip() or not password.strip():
                st.error("Email and password are required.")
            else:
                with st.spinner("Logging in..."):
                    ok, data = api_call(
                        "POST",
                        "/auth/login",
                        json={"email": email.strip(), "password": password},
                    )
                if ok:
                    st.session_state["token"] = data["access_token"]
                    st.session_state["email"] = data["email"]
                    st.session_state["page"] = "dashboard"
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error(str(data))

    st.caption("New user?")
    if st.button("Go to Register", use_container_width=True):
        go_to("register")


def render_register_page() -> None:
    render_page_header("Create Account", "Register to start organizing your personal tasks.")

    with st.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        if not email.strip() or not password.strip() or not confirm_password.strip():
            st.error("All fields are required.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            with st.spinner("Creating account..."):
                ok, data = api_call(
                    "POST",
                    "/auth/register",
                    json={"email": email.strip(), "password": password},
                )
            if ok:
                st.success("Registration successful. Please login.")
                st.session_state["page"] = "login"
                st.rerun()
            else:
                st.error(str(data))

    if st.button("Back to Login", use_container_width=True):
        go_to("login")


def fetch_summary() -> dict[str, int] | None:
    ok, data = api_call("GET", "/tasks/summary", require_auth=True)
    if ok:
        return data
    st.error(str(data))
    return None


def fetch_tasks(
    status_filter: str,
    priority_filter: str,
) -> list[dict[str, Any]] | None:
    params: dict[str, str] = {}
    if status_filter != "All":
        params["status"] = status_filter
    if priority_filter != "All":
        params["priority"] = priority_filter

    ok, data = api_call("GET", "/tasks/", params=params, require_auth=True)
    if ok:
        return data
    st.error(str(data))
    return None


def fetch_task_detail(task_id: int) -> dict[str, Any] | None:
    ok, data = api_call("GET", f"/tasks/{task_id}", require_auth=True)
    if ok:
        return data
    st.error(str(data))
    return None


def get_status_badge(status_value: str) -> str:
    class_name = {
        "pending": "badge-status-pending",
        "in-progress": "badge-status-in-progress",
        "done": "badge-status-done",
    }.get(status_value, "badge-status-pending")
    return f"<span class='badge {class_name}'>{status_value}</span>"


def get_priority_badge(priority_value: str) -> str:
    class_name = {
        "low": "badge-priority-low",
        "medium": "badge-priority-medium",
        "high": "badge-priority-high",
    }.get(priority_value, "badge-priority-low")
    return f"<span class='badge {class_name}'>{priority_value}</span>"


def render_summary_cards(summary: dict[str, int]) -> None:
    values = [
        ("Total Tasks", summary.get("total", 0)),
        ("Pending", summary.get("pending", 0)),
        ("In Progress", summary.get("in_progress", 0)),
        ("Done", summary.get("done", 0)),
    ]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, values):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-label">{label}</div>
                    <div class="summary-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_task_actions(task_list: list[dict[str, Any]]) -> None:
    st.markdown("<div class='section-title'>Quick Actions</div>", unsafe_allow_html=True)

    if not task_list:
        st.info("No tasks available.")
        return

    options = {
        f"#{task['id']} | {task['title']} | {task['status']} | {task['priority']}": task["id"]
        for task in task_list
    }
    selected_label = st.selectbox("Select Task", list(options.keys()))
    selected_task_id = options[selected_label]

    col1, col2, col3, col4 = st.columns(4)

    if col1.button("View", use_container_width=True):
        go_to("task_detail", task_id=selected_task_id)

    if col2.button("Edit", use_container_width=True):
        go_to("edit_task", task_id=selected_task_id)

    if col3.button("Mark Done", use_container_width=True):
        with st.spinner("Updating task..."):
            ok, data = api_call(
                "PATCH",
                f"/tasks/{selected_task_id}/status",
                json={"status": "done"},
                require_auth=True,
            )
        if ok:
            st.success("Task marked as done.")
            st.rerun()
        else:
            st.error(str(data))

    if col4.button("Delete", use_container_width=True):
        st.session_state["delete_task_id"] = selected_task_id
        st.rerun()

    delete_task_id = st.session_state.get("delete_task_id")
    if delete_task_id == selected_task_id:
        st.warning("Are you sure you want to delete this task?")
        yes_col, no_col = st.columns(2)

        if yes_col.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting task..."):
                ok, data = api_call(
                    "DELETE",
                    f"/tasks/{selected_task_id}",
                    require_auth=True,
                )
            st.session_state["delete_task_id"] = None
            if ok:
                st.success("Task deleted successfully.")
                st.rerun()
            else:
                st.error(str(data))

        if no_col.button("Cancel", use_container_width=True):
            st.session_state["delete_task_id"] = None
            st.rerun()


def render_task_card(task: dict[str, Any], display_index: int) -> None:
    st.markdown(
        f"""
        <div class="task-card">
            <div class="task-meta">Task #{display_index} • DB ID: {task["id"]}</div>
            <div class="task-card-title">{task["title"]}</div>
            <div class="task-card-desc">{task["description"] or "No description provided."}</div>
            <div>
                {get_priority_badge(task["priority"])}
                {get_status_badge(task["status"])}
            </div>
            <div class="task-meta">Due Date: {format_due_date(task.get("due_date"))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    if col1.button("View Details", key=f"view_{task['id']}", use_container_width=True):
        go_to("task_detail", task_id=task["id"])
    if col2.button("Edit", key=f"edit_{task['id']}", use_container_width=True):
        go_to("edit_task", task_id=task["id"])
    if col3.button("Mark Done", key=f"done_{task['id']}", use_container_width=True):
        with st.spinner("Updating task..."):
            ok, data = api_call(
                "PATCH",
                f"/tasks/{task['id']}/status",
                json={"status": "done"},
                require_auth=True,
            )
        if ok:
            st.success("Task marked as done.")
            st.rerun()
        else:
            st.error(str(data))


def render_dashboard_page() -> None:
    if not require_login():
        return

    render_page_header(
        "Dashboard",
        "Track your workload, filter tasks, and manage progress in one place.",
    )

    summary = fetch_summary()
    if summary:
        render_summary_cards(summary)

    st.markdown("<div class='section-title'>Filters</div>", unsafe_allow_html=True)
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "pending", "in-progress", "done"],
            )
        with col2:
            priority_filter = st.selectbox(
                "Filter by Priority",
                ["All", "low", "medium", "high"],
            )

    with st.spinner("Loading tasks..."):
        task_list = fetch_tasks(status_filter, priority_filter)

    if task_list is None:
        return

    st.markdown("<div class='section-title'>Your Tasks</div>", unsafe_allow_html=True)

    if task_list:
        table_rows: list[dict[str, Any]] = []
        for index, task in enumerate(task_list, start=1):
            table_rows.append(
                {
                    "S.No": index,
                    "Title": task["title"],
                    "Description": task["description"],
                    "Priority": task["priority"],
                    "Status": task["status"],
                    "Due Date": format_due_date(task.get("due_date")),
                }
            )
        st.dataframe(table_rows, use_container_width=True, hide_index=True)

        st.markdown("<div class='section-title'>Task Cards</div>", unsafe_allow_html=True)
        for index, task in enumerate(task_list, start=1):
            render_task_card(task, index)
    else:
        st.info("No tasks found.")

    render_task_actions(task_list)


def render_add_task_page() -> None:
    if not require_login():
        return

    render_page_header("Add Task", "Create a new task with priority, status, and due date.")

    with st.form("add_task_form"):
        title = st.text_input("Title")
        description = st.text_area("Description")
        priority = st.selectbox("Priority", ["low", "medium", "high"])
        status = st.selectbox("Status", ["pending", "in-progress", "done"])
        due_date = st.date_input("Due Date", value=None)
        submitted = st.form_submit_button("Create Task", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("Title is required.")
            return

        payload = {
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority,
            "status": status,
            "due_date": due_date.isoformat() if due_date else None,
        }

        with st.spinner("Creating task..."):
            ok, data = api_call(
                "POST",
                "/tasks/",
                json=payload,
                require_auth=True,
            )

        if ok:
            st.success("Task created successfully.")
            st.session_state["page"] = "dashboard"
            st.rerun()
        else:
            st.error(str(data))

    if st.button("Back to Dashboard", use_container_width=True):
        go_to("dashboard")


def render_task_detail_page() -> None:
    if not require_login():
        return

    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        st.warning("No task selected.")
        if st.button("Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        return

    render_page_header("Task Detail", "Review the selected task and manage it safely.")

    with st.spinner("Loading task..."):
        task = fetch_task_detail(task_id)

    if not task:
        return

    st.markdown("<div class='detail-grid'>", unsafe_allow_html=True)
    st.markdown("<div class='detail-label'>Task ID</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='detail-value'>{task['id']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='detail-label'>Title</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='detail-value'>{task['title']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='detail-label'>Description</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='detail-value'>{task['description'] or '-'}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='detail-label'>Priority</div>", unsafe_allow_html=True)
    st.markdown(get_priority_badge(task["priority"]), unsafe_allow_html=True)
    st.markdown("<div class='detail-label'>Status</div>", unsafe_allow_html=True)
    st.markdown(get_status_badge(task["status"]), unsafe_allow_html=True)
    st.markdown("<div class='detail-label'>Due Date</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='detail-value'>{format_due_date(task.get('due_date'))}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    delete_key = f"confirm_delete_detail_{task_id}"
    st.session_state.setdefault(delete_key, False)

    col1, col2, col3 = st.columns(3)

    if col1.button("Edit", use_container_width=True):
        go_to("edit_task", task_id=task_id)

    if col2.button("Delete", use_container_width=True):
        st.session_state[delete_key] = True
        st.rerun()

    if col3.button("Back", use_container_width=True):
        go_to("dashboard")

    if st.session_state.get(delete_key):
        st.warning("Are you sure you want to delete this task?")
        yes_col, no_col = st.columns(2)

        if yes_col.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting task..."):
                ok, data = api_call("DELETE", f"/tasks/{task_id}", require_auth=True)

            st.session_state[delete_key] = False

            if ok:
                st.success("Task deleted successfully.")
                st.session_state["selected_task_id"] = None
                go_to("dashboard")
            else:
                st.error(str(data))

        if no_col.button("Cancel", use_container_width=True):
            st.session_state[delete_key] = False
            st.rerun()


def render_edit_task_page() -> None:
    if not require_login():
        return

    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        st.warning("No task selected.")
        if st.button("Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        return

    render_page_header("Edit Task", "Update task content, status, priority, and due date.")

    task = fetch_task_detail(task_id)
    if not task:
        return

    default_due_date = parse_due_date_for_input(task.get("due_date"))

    with st.form("edit_task_form"):
        title = st.text_input("Title", value=task["title"])
        description = st.text_area("Description", value=task["description"])
        priority = st.selectbox(
            "Priority",
            ["low", "medium", "high"],
            index=["low", "medium", "high"].index(task["priority"]),
        )
        status_value = (
            task["status"]
            if task["status"] in ["pending", "in-progress", "done"]
            else "pending"
        )
        status = st.selectbox(
            "Status",
            ["pending", "in-progress", "done"],
            index=["pending", "in-progress", "done"].index(status_value),
        )
        due_date = st.date_input("Due Date", value=default_due_date)
        submitted = st.form_submit_button("Update Task", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("Title is required.")
            return

        payload = {
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority,
            "status": status,
            "due_date": due_date.isoformat() if due_date else None,
        }

        with st.spinner("Updating task..."):
            ok, data = api_call(
                "PUT",
                f"/tasks/{task_id}",
                json=payload,
                require_auth=True,
            )

        if ok:
            st.success("Task updated successfully.")
            go_to("dashboard")
        else:
            st.error(str(data))

    if st.button("Cancel", use_container_width=True):
        go_to("dashboard")


def main() -> None:
    st.set_page_config(page_title="Task Manager", page_icon="✅", layout="wide")
    init_session_state()
    apply_custom_css()
    render_sidebar()

    page = st.session_state.get("page", "login")

    if page == "login":
        render_login_page()
    elif page == "register":
        render_register_page()
    elif page == "dashboard":
        render_dashboard_page()
    elif page == "add_task":
        render_add_task_page()
    elif page == "task_detail":
        render_task_detail_page()
    elif page == "edit_task":
        render_edit_task_page()
    else:
        st.session_state["page"] = "login"
        st.rerun()


if __name__ == "__main__":
    main()
