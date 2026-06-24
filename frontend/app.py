# File: frontend/app.py
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import requests
import streamlit as st

API_BASE_URL ="https://task-manager-fastapi-streamlit.onrender.com"
REQUEST_TIMEOUT = 10


def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "page": "login",
        "token": None,
        "email": None,
        "name": None,
        "last_registered_name": None,
        "last_registered_email": None,
        "selected_task_id": None,
        "delete_task_id": None,
        "confirm_logout": False,
        "flash_message": None,
        "flash_type": "success",
        "search_query": "",
        "status_filter": "All",
        "priority_filter": "All",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def apply_custom_css() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(99,102,241,0.10), transparent 25%),
                    radial-gradient(circle at top right, rgba(14,165,233,0.10), transparent 20%),
                    linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0b1220 0%, #172554 100%);
                border-right: 1px solid rgba(255,255,255,0.06);
            }

            [data-testid="stSidebar"] * {
                color: #f8fafc !important;
            }

            [data-testid="stExpander"] {
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 14px;
                background: rgba(255,255,255,0.04);
            }

            [data-testid="stExpander"] details summary {
                font-weight: 600;
            }

            .stButton > button {
                border-radius: 12px;
                font-weight: 600;
                border: 1px solid #dbe4ff;
                box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
            }

            .app-title {
                font-size: 2.25rem;
                font-weight: 800;
                color: #0f172a;
                margin-bottom: 0.15rem;
                letter-spacing: -0.02em;
            }

            .app-subtitle {
                color: #475569;
                font-size: 1rem;
                margin-bottom: 1.2rem;
            }

            .section-title {
                font-size: 1.25rem;
                font-weight: 800;
                color: #0f172a;
                margin-top: 0.4rem;
                margin-bottom: 0.65rem;
                letter-spacing: -0.01em;
            }

            .summary-card {
                background: rgba(255,255,255,0.88);
                backdrop-filter: blur(6px);
                border-radius: 18px;
                padding: 1rem 1.1rem;
                border: 1px solid rgba(226,232,240,0.9);
                box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
            }

            .summary-label {
                color: #64748b;
                font-size: 0.92rem;
                margin-bottom: 0.2rem;
            }

            .summary-value {
                color: #0f172a;
                font-size: 1.8rem;
                font-weight: 800;
                line-height: 1.1;
            }

            .summary-subtext {
                color: #64748b;
                font-size: 0.8rem;
                margin-top: 0.28rem;
            }

            .auth-shell {
                max-width: 520px;
                margin: 0 auto;
            }

            .auth-card {
                background: rgba(255,255,255,0.94);
                backdrop-filter: blur(8px);
                border-radius: 22px;
                padding: 1.15rem;
                border: 1px solid rgba(226,232,240,0.95);
                box-shadow: 0 18px 42px rgba(15, 23, 42, 0.10);
            }

            .sidebar-brand {
                font-size: 1.45rem;
                font-weight: 800;
                letter-spacing: -0.01em;
                margin-bottom: 0.2rem;
            }

            .sidebar-tagline {
                color: #cbd5e1;
                font-size: 0.9rem;
                margin-bottom: 1rem;
            }

            .profile-card {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
                padding: 0.95rem 1rem;
                margin-bottom: 0.9rem;
            }

            .profile-label {
                font-size: 0.8rem;
                color: #cbd5e1;
                margin-bottom: 0.15rem;
            }

            .profile-name {
                font-size: 1rem;
                font-weight: 700;
                color: white;
            }

            .profile-email {
                font-size: 0.84rem;
                color: #dbeafe;
                margin-top: 0.2rem;
            }

            .footer-text {
                text-align: center;
                color: #64748b;
                font-size: 0.9rem;
                margin-top: 1.6rem;
                margin-bottom: 0.35rem;
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

    # Resetting auth state on 401 keeps the UI from staying in a broken logged-in state.
    if response.status_code == 401 and require_auth:
        st.session_state["token"] = None
        st.session_state["email"] = None
        st.session_state["name"] = None
        st.session_state["page"] = "login"

    return False, data.get("detail", "Something went wrong.")


def go_to(page: str, *, task_id: int | None = None) -> None:
    st.session_state["page"] = page
    if task_id is not None:
        st.session_state["selected_task_id"] = task_id
    st.rerun()


def set_flash_message(message: str, message_type: str = "success") -> None:
    st.session_state["flash_message"] = message
    st.session_state["flash_type"] = message_type


def show_flash_message() -> None:
    message = st.session_state.get("flash_message")
    if not message:
        return

    message_type = st.session_state.get("flash_type", "success")
    if message_type == "success":
        st.success(message)
    elif message_type == "warning":
        st.warning(message)
    else:
        st.error(message)

    st.session_state["flash_message"] = None
    st.session_state["flash_type"] = "success"


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


def is_overdue(task: dict[str, Any]) -> bool:
    if task.get("status") == "done":
        return False
    due = parse_due_date_for_input(task.get("due_date"))
    return due is not None and due < date.today()


def calculate_completion_rate(summary: dict[str, int]) -> int:
    total = summary.get("total", 0)
    done = summary.get("done", 0)
    return 0 if total == 0 else round((done / total) * 100)


def count_overdue_tasks(task_list: list[dict[str, Any]]) -> int:
    return sum(1 for task in task_list if is_overdue(task))


def filter_tasks_by_search(task_list: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    normalized = query.strip().lower()
    if not normalized:
        return task_list
    return [task for task in task_list if normalized in task.get("title", "").lower()]


def validate_task_form(title: str, description: str, due_date_value: date | None) -> str | None:
    cleaned_title = title.strip()
    cleaned_description = description.strip()

    if not cleaned_title:
        return "Title is required."
    if len(cleaned_title) < 3:
        return "Title must have at least 3 characters."
    if len(cleaned_title) > 200:
        return "Title must be at most 200 characters."
    if len(cleaned_description) > 1000:
        return "Description must be at most 1000 characters."
    # Blocking past dates in the UI prevents avoidable backend validation failures.
    if due_date_value is not None and due_date_value < date.today():
        return "Due date cannot be in the past."
    return None


def validate_register_form(name: str, email: str, password: str, confirm_password: str) -> str | None:
    cleaned_name = name.strip()

    if not cleaned_name or not email.strip() or not password.strip() or not confirm_password.strip():
        return "All fields are required."
    if len(cleaned_name) < 2:
        return "Name must have at least 2 characters."
    if len(cleaned_name) > 100:
        return "Name must be at most 100 characters."
    if len(password) < 6:
        return "Password must have at least 6 characters."
    if len(password) > 72:
        return "Password must be at most 72 characters."
    if password != confirm_password:
        return "Passwords do not match."
    return None


def require_login() -> bool:
    if not st.session_state.get("token"):
        st.warning("Please login first.")
        st.session_state["page"] = "login"
        return False
    return True


def derive_name_from_email(email: str | None) -> str:
    if not email:
        return "User"
    username = email.split("@")[0].replace(".", " ").replace("_", " ").strip()
    return username.title() if username else "User"


def current_display_name() -> str:
    stored_name = st.session_state.get("name")
    if stored_name and str(stored_name).strip():
        return str(stored_name).strip()
    # Falling back to email keeps the greeting usable even if backend name support is missing.
    return derive_name_from_email(st.session_state.get("email"))


def logout() -> None:
    st.session_state["token"] = None
    st.session_state["email"] = None
    st.session_state["name"] = None
    st.session_state["selected_task_id"] = None
    st.session_state["delete_task_id"] = None
    st.session_state["confirm_logout"] = False
    st.session_state["page"] = "login"
    set_flash_message("You have been logged out successfully.", "success")
    st.rerun()


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='app-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='app-subtitle'>{subtitle}</div>", unsafe_allow_html=True)


def fetch_summary() -> dict[str, int] | None:
    ok, data = api_call("GET", "/tasks/summary", require_auth=True)
    if ok:
        return data
    st.error(str(data))
    return None


def fetch_tasks(status_filter: str, priority_filter: str) -> list[dict[str, Any]] | None:
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


def get_status_badge_text(status_value: str) -> str:
    mapping = {
        "pending": "🟠 Pending",
        "in-progress": "🔵 In Progress",
        "done": "🟢 Done",
    }
    return mapping.get(status_value, status_value.title())


def get_priority_badge_text(priority_value: str) -> str:
    mapping = {
        "low": "⚪ Low",
        "medium": "🟡 Medium",
        "high": "🔴 High",
    }
    return mapping.get(priority_value, priority_value.title())


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("<div class='sidebar-brand'>Task Manager</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-tagline'>Plan better. Work clearer.</div>", unsafe_allow_html=True)

        email = st.session_state.get("email")
        if email:
            name = current_display_name()
            st.markdown(
                f"""
                <div class="profile-card">
                    <div class="profile-label">Profile</div>
                    <div class="profile-name">{name}</div>
                    <div class="profile-email">{email}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button("Dashboard", use_container_width=True):
                go_to("dashboard")

            if st.button("Add Task", use_container_width=True):
                go_to("add_task")

            if not st.session_state.get("confirm_logout"):
                if st.button("Logout", use_container_width=True):
                    st.session_state["confirm_logout"] = True
                    st.rerun()
            else:
                st.warning("Are you sure you want to logout?")
                confirm_col, cancel_col = st.columns(2)
                if confirm_col.button("Yes", use_container_width=True):
                    logout()
                if cancel_col.button("No", use_container_width=True):
                    st.session_state["confirm_logout"] = False
                    st.rerun()

        with st.expander("ℹ️ About"):
            st.write("Task Manager keeps your daily work organized in one place.")
            st.write("Add tasks, track progress, set priorities, and stay on top of due dates.")

        with st.expander("❓ Help"):
            st.write("Use Dashboard to view and manage tasks.")
            st.write("Use Add Task to create a new task.")
            st.write("Use search and filters to find tasks faster.")
            st.write("Completed work is available in the Completed / Archive tab.")


def render_auth_shell(title: str, subtitle: str) -> None:
    render_page_header(title, subtitle)
    show_flash_message()


def render_login_page() -> None:
    render_auth_shell("Welcome Back", "Sign in to continue managing your tasks.")

    left, center, right = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)
        with st.container(border=True):
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
                        returned_name = data.get("name")
                        if returned_name:
                            st.session_state["name"] = returned_name
                        elif (
                            st.session_state.get("last_registered_email") == data["email"]
                            and st.session_state.get("last_registered_name")
                        ):
                            st.session_state["name"] = st.session_state["last_registered_name"]
                        else:
                            st.session_state["name"] = derive_name_from_email(data["email"])
                        st.session_state["page"] = "dashboard"
                        set_flash_message("Login successful.", "success")
                        st.rerun()
                    else:
                        st.error(str(data))

            st.caption("New user?")
            if st.button("Go to Register", use_container_width=True):
                go_to("register")
        st.markdown("</div>", unsafe_allow_html=True)


def render_register_page() -> None:
    render_auth_shell("Create Account", "Register to start organizing your personal tasks.")

    left, center, right = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div class='auth-shell'>", unsafe_allow_html=True)
        with st.container(border=True):
            with st.form("register_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                validation_error = validate_register_form(name, email, password, confirm_password)
                if validation_error:
                    st.error(validation_error)
                else:
                    cleaned_name = name.strip()
                    with st.spinner("Creating account..."):
                        ok, data = api_call(
                            "POST",
                            "/auth/register",
                            json={
                                "name": cleaned_name,
                                "email": email.strip(),
                                "password": password,
                            },
                        )
                    if ok:
                        st.session_state["last_registered_name"] = cleaned_name
                        st.session_state["last_registered_email"] = email.strip()
                        st.session_state["page"] = "login"
                        set_flash_message("Registration successful. Please login.", "success")
                        st.rerun()
                    else:
                        st.error(str(data))

            st.caption("Already have an account?")
            if st.button("Back to Login", use_container_width=True):
                go_to("login")
        st.markdown("</div>", unsafe_allow_html=True)


def render_summary_cards(summary: dict[str, int], overdue_count: int) -> None:
    completion_rate = calculate_completion_rate(summary)
    values = [
        ("Total Tasks", summary.get("total", 0), "All active and completed tasks"),
        ("Pending", summary.get("pending", 0), "Tasks waiting to be started"),
        ("Done", summary.get("done", 0), f"{completion_rate}% completion rate"),
        ("Overdue", overdue_count, "Tasks past due date and not done"),
    ]
    cols = st.columns(4)
    for col, (label, value, subtext) in zip(cols, values):
        with col:
            st.markdown(
                f"""
                <div class="summary-card">
                    <div class="summary-label">{label}</div>
                    <div class="summary-value">{value}</div>
                    <div class="summary-subtext">{subtext}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_task_card(task: dict[str, Any], display_index: int) -> None:
    overdue = is_overdue(task)

    with st.container(border=True):
        st.markdown(f"### Task #{display_index} — {task.get('title', 'Untitled')}")
        st.write(task.get("description") or "No description provided.")

        col1, col2, col3 = st.columns(3)
        col1.write(f"**Priority:** {get_priority_badge_text(task.get('priority', 'low'))}")
        col2.write(f"**Status:** {get_status_badge_text(task.get('status', 'pending'))}")
        col3.write(f"**Due Date:** {format_due_date(task.get('due_date'))}")

        if overdue:
            st.error("This task is overdue.")

        action_col1, action_col2 = st.columns(2)
        if action_col1.button("View Task", key=f"view_{task['id']}", use_container_width=True):
            go_to("task_detail", task_id=task["id"])
        if action_col2.button("Edit Task", key=f"edit_{task['id']}", use_container_width=True):
            go_to("edit_task", task_id=task["id"])


def render_task_actions(task_list: list[dict[str, Any]], *, archive_mode: bool = False) -> None:
    st.markdown("<div class='section-title'>Quick Actions</div>", unsafe_allow_html=True)

    if not task_list:
        st.info("No tasks are available here right now.")
        return

    options = {
        f"{task['title']} • {task['status']} • {task['priority']}": task["id"]
        for task in task_list
    }
    selected_label = st.selectbox(
        "Choose a Task",
        list(options.keys()),
        key="archive_task_selector" if archive_mode else "active_task_selector",
    )
    selected_task_id = options[selected_label]

    if archive_mode:
        col1, col2, col3 = st.columns(3)

        if col1.button("View Task", use_container_width=True, key="archive_view"):
            go_to("task_detail", task_id=selected_task_id)

        if col2.button("Edit Task", use_container_width=True, key="archive_edit"):
            go_to("edit_task", task_id=selected_task_id)

        if col3.button("Delete Task", use_container_width=True, key="archive_delete"):
            st.session_state["delete_task_id"] = selected_task_id
            st.rerun()
    else:
        col1, col2, col3, col4 = st.columns(4)

        if col1.button("View Task", use_container_width=True, key="active_view"):
            go_to("task_detail", task_id=selected_task_id)

        if col2.button("Edit Task", use_container_width=True, key="active_edit"):
            go_to("edit_task", task_id=selected_task_id)

        if col3.button("Mark as Done", use_container_width=True, key="active_done"):
            with st.spinner("Updating task..."):
                ok, data = api_call(
                    "PATCH",
                    f"/tasks/{selected_task_id}/status",
                    json={"status": "done"},
                    require_auth=True,
                )
            if ok:
                set_flash_message("Task marked as done.", "success")
                st.rerun()
            else:
                st.error(str(data))

        if col4.button("Delete Task", use_container_width=True, key="active_delete"):
            st.session_state["delete_task_id"] = selected_task_id
            st.rerun()

    delete_task_id = st.session_state.get("delete_task_id")
    if delete_task_id == selected_task_id:
        st.warning("Are you sure you want to delete this task?")
        yes_col, no_col = st.columns(2)

        if yes_col.button("Yes, Delete", use_container_width=True, key="confirm_delete_yes"):
            with st.spinner("Deleting task..."):
                ok, data = api_call(
                    "DELETE",
                    f"/tasks/{selected_task_id}",
                    require_auth=True,
                )
            st.session_state["delete_task_id"] = None
            if ok:
                set_flash_message("Task deleted successfully.", "success")
                st.rerun()
            else:
                st.error(str(data))

        if no_col.button("Cancel", use_container_width=True, key="confirm_delete_no"):
            st.session_state["delete_task_id"] = None
            st.rerun()


def render_dashboard_page() -> None:
    if not require_login():
        return

    first_name = current_display_name().split()[0]
    render_page_header(
        f"Welcome, {first_name} 👋",
        "Track your work, find tasks quickly, and stay organized.",
    )
    show_flash_message()

    with st.spinner("Loading tasks..."):
        raw_task_list = fetch_tasks(
            st.session_state.get("status_filter", "All"),
            st.session_state.get("priority_filter", "All"),
        )

    if raw_task_list is None:
        return

    overdue_count = count_overdue_tasks(raw_task_list)
    summary = fetch_summary()
    if summary:
        render_summary_cards(summary, overdue_count)

    with st.container(border=True):
        st.markdown("<div class='section-title'>Find Tasks</div>", unsafe_allow_html=True)

        filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 1.4])

        with filter_col1:
            status_filter = st.selectbox(
                "Status",
                ["All", "pending", "in-progress", "done"],
                key="status_filter",
            )
        with filter_col2:
            priority_filter = st.selectbox(
                "Priority",
                ["All", "low", "medium", "high"],
                key="priority_filter",
            )
        with filter_col3:
            search_query = st.text_input(
                "Search by Title",
                value=st.session_state.get("search_query", ""),
                placeholder="Search tasks...",
            )
            st.session_state["search_query"] = search_query

    with st.spinner("Refreshing tasks..."):
        task_list = fetch_tasks(status_filter, priority_filter)

    if task_list is None:
        return

    visible_tasks = filter_tasks_by_search(task_list, search_query)
    active_tasks = [task for task in visible_tasks if task.get("status") != "done"]
    completed_tasks = [task for task in visible_tasks if task.get("status") == "done"]

    active_tab, archive_tab = st.tabs(["Tasks", "Completed / Archive"])

    with active_tab:
        st.markdown("<div class='section-title'>Your Tasks</div>", unsafe_allow_html=True)

        if not visible_tasks and not task_list:
            st.info("You do not have any tasks yet. Add your first task to get started.")
        elif not active_tasks:
            st.info("No active tasks matched your current search or filters.")
        else:
            for index, task in enumerate(active_tasks, start=1):
                render_task_card(task, index)
            render_task_actions(active_tasks, archive_mode=False)

    with archive_tab:
        st.markdown("<div class='section-title'>Completed Tasks</div>", unsafe_allow_html=True)

        if not completed_tasks:
            st.info("No completed tasks found yet.")
        else:
            for index, task in enumerate(completed_tasks, start=1):
                render_task_card(task, index)
            render_task_actions(completed_tasks, archive_mode=True)

    st.markdown("<div class='footer-text'>Task Manager • Elegant Productivity Dashboard</div>", unsafe_allow_html=True)


def render_add_task_page() -> None:
    if not require_login():
        return

    render_page_header("Add Task", "Create a new task with priority, status, and due date.")
    show_flash_message()

    with st.container(border=True):
        with st.form("add_task_form"):
            title = st.text_input("Title")
            description = st.text_area("Description")
            priority = st.selectbox("Priority", ["low", "medium", "high"])
            status = st.selectbox("Status", ["pending", "in-progress", "done"])
            due_date_value = st.date_input("Due Date", value=None)
            submitted = st.form_submit_button("Add Task", use_container_width=True)

        if submitted:
            validation_error = validate_task_form(title, description, due_date_value)
            if validation_error:
                st.error(validation_error)
                return

            payload = {
                "title": title.strip(),
                "description": description.strip(),
                "priority": priority,
                "status": status,
                "due_date": due_date_value.isoformat() if due_date_value else None,
            }

            with st.spinner("Creating task..."):
                ok, data = api_call(
                    "POST",
                    "/tasks/",
                    json=payload,
                    require_auth=True,
                )

            if ok:
                st.session_state["page"] = "dashboard"
                set_flash_message("Task created successfully.", "success")
                st.rerun()
            else:
                st.error(str(data))


def render_task_detail_page() -> None:
    if not require_login():
        return

    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        st.warning("No task selected.")
        if st.button("Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        return

    render_page_header("Task Details", "Review the selected task and manage it safely.")
    show_flash_message()

    with st.spinner("Loading task..."):
        task = fetch_task_detail(task_id)

    if not task:
        return

    with st.container(border=True):
        st.write(f"**Title:** {task.get('title', 'Untitled')}")
        st.write(f"**Description:** {task.get('description') or '-'}")
        st.write(f"**Priority:** {get_priority_badge_text(task.get('priority', 'low'))}")
        st.write(f"**Status:** {get_status_badge_text(task.get('status', 'pending'))}")
        st.write(f"**Due Date:** {format_due_date(task.get('due_date'))}")

        if is_overdue(task):
            st.error("This task is overdue.")

    delete_key = f"confirm_delete_detail_{task_id}"
    st.session_state.setdefault(delete_key, False)

    col1, col2, col3 = st.columns(3)

    if col1.button("Edit Task", use_container_width=True):
        go_to("edit_task", task_id=task_id)

    if col2.button("Delete Task", use_container_width=True):
        st.session_state[delete_key] = True
        st.rerun()

    if col3.button("Back to Dashboard", use_container_width=True):
        go_to("dashboard")

    if st.session_state.get(delete_key):
        st.warning("Are you sure you want to delete this task?")
        yes_col, no_col = st.columns(2)

        if yes_col.button("Yes, Delete", use_container_width=True):
            with st.spinner("Deleting task..."):
                ok, data = api_call("DELETE", f"/tasks/{task_id}", require_auth=True)

            st.session_state[delete_key] = False

            if ok:
                st.session_state["selected_task_id"] = None
                set_flash_message("Task deleted successfully.", "success")
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

    render_page_header("Update Task", "Edit the task details and save your changes.")
    show_flash_message()

    task = fetch_task_detail(task_id)
    if not task:
        return

    default_due_date = parse_due_date_for_input(task.get("due_date"))

    with st.container(border=True):
        with st.form("edit_task_form"):
            title = st.text_input("Title", value=task["title"])
            description = st.text_area("Description", value=task["description"])
            priority = st.selectbox(
                "Priority",
                ["low", "medium", "high"],
                index=["low", "medium", "high"].index(task["priority"]),
            )
            status_value = task["status"] if task["status"] in ["pending", "in-progress", "done"] else "pending"
            status = st.selectbox(
                "Status",
                ["pending", "in-progress", "done"],
                index=["pending", "in-progress", "done"].index(status_value),
            )
            due_date_value = st.date_input("Due Date", value=default_due_date)
            submitted = st.form_submit_button("Update Task", use_container_width=True)

        if submitted:
            validation_error = validate_task_form(title, description, due_date_value)
            if validation_error:
                st.error(validation_error)
                return

            payload = {
                "title": title.strip(),
                "description": description.strip(),
                "priority": priority,
                "status": status,
                "due_date": due_date_value.isoformat() if due_date_value else None,
            }

            with st.spinner("Updating task..."):
                ok, data = api_call(
                    "PUT",
                    f"/tasks/{task_id}",
                    json=payload,
                    require_auth=True,
                )

            if ok:
                set_flash_message("Task updated successfully.", "success")
                go_to("dashboard")
            else:
                st.error(str(data))


def main() -> None:
    st.set_page_config(
        page_title="Task Manager",
        page_icon="✨",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session_state()
    apply_custom_css()

    # Sidebar is rendered once here so navigation and auth state stay shared across all pages.
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
