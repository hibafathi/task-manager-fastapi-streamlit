from __future__ import annotations
from datetime import date,datetime
from typing import Any
import requests
import streamlit as st
API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 10
def init_session_state() -> None:
    defaults: dict[str, Any] = {
        "page": "lognn",
        "token": None,
        "email": None, 
        "selectd_task_id":None,
        "delete_task_id":None
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key,value)
def get_auth_headers()-> dict[str,str]:
    token=st.session_state.get("token")
    return {"authorization":f"Bearer {token}"}if token else{}
def api_call(
        method:str,
        endpoint:str,
        *,
        json:dict[str,Any]|None=None,
        params:dict[str,any]|None=None,
        require_auth:bool=False,
)->tuple[bool,Any]:
    url=f"{API_BASE_URL}{endpoint}"
    headers=get_auth_headers() if require_auth else{}
    try:
        response=requests.request(
            method=method,
            url=url,
            json=json,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT
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


def render_sidebar() -> None:
    with st.sidebar:
        st.title("Task Manager")

        email = st.session_state.get("email")
        if email:
            st.write(f"Logged in as: **{email}**")
            st.divider()
            if st.button("Dashboard", use_container_width=True):
                go_to("dashboard")
            if st.button("Add Task", use_container_width=True):
                go_to("add_task")
            if st.button("Logout", use_container_width=True):
                logout()
        else:
            st.write("Please login or register.")


def render_login_page() -> None:
    st.title("Login")

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
    st.title("Register")

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


def render_summary_cards(summary: dict[str, int]) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", summary.get("total", 0))
    col2.metric("Pending", summary.get("pending", 0))
    col3.metric("In Progress", summary.get("in_progress", 0))
    col4.metric("Done", summary.get("done", 0))


def render_task_actions(tasks: list[dict[str, Any]]) -> None:
    st.subheader("Task Actions")

    if not tasks:
        st.info("No tasks available.")
        return

    options = {
        f"#{task['id']} | {task['title']} | {task['status']} | {task['priority']}": task["id"]
        for task in tasks
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
        st.warning("Confirm delete?")
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


def render_dashboard_page() -> None:
    if not require_login():
        return

    st.title("Dashboard")

    summary = fetch_summary()
    if summary:
        render_summary_cards(summary)

    st.divider()

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
        tasks = fetch_tasks(status_filter, priority_filter)

    if tasks is None:
        return

    st.subheader("Your Tasks")

    if tasks:
        table_rows = []
        for task in tasks:
            table_rows.append(
                {
                    "ID": task["id"],
                    "Title": task["title"],
                    "Description": task["description"],
                    "Priority": task["priority"],
                    "Status": task["status"],
                    "Due Date": format_due_date(task.get("due_date")),
                }
            )
        st.dataframe(table_rows, use_container_width=True)
    else:
        st.info("No tasks found.")

    st.divider()
    render_task_actions(tasks)


def render_add_task_page() -> None:
    if not require_login():
        return

    st.title("Add Task")

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


def fetch_task_detail(task_id: int) -> dict[str, Any] | None:
    ok, data = api_call("GET", f"/tasks/{task_id}", require_auth=True)
    if ok:
        return data
    st.error(str(data))
    return None


def render_task_detail_page() -> None:
    if not require_login():
        return

    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        st.warning("No task selected.")
        if st.button("Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        return

    st.title("Task Detail")

    with st.spinner("Loading task..."):
        task = fetch_task_detail(task_id)

    if not task:
        return

    st.write(f"**ID:** {task['id']}")
    st.write(f"**Title:** {task['title']}")
    st.write(f"**Description:** {task['description'] or '-'}")
    st.write(f"**Priority:** {task['priority']}")
    st.write(f"**Status:** {task['status']}")
    st.write(f"**Due Date:** {format_due_date(task.get('due_date'))}")
    st.write(f"**Owner:** {task['owner_email']}")

    col1, col2, col3 = st.columns(3)

    if col1.button("Edit", use_container_width=True):
        go_to("edit_task", task_id=task_id)

    if col2.button("Delete", use_container_width=True):
        with st.spinner("Deleting task..."):
            ok, data = api_call("DELETE", f"/tasks/{task_id}", require_auth=True)
        if ok:
            st.success("Task deleted successfully.")
            st.session_state["selected_task_id"] = None
            go_to("dashboard")
        else:
            st.error(str(data))

    if col3.button("Back", use_container_width=True):
        go_to("dashboard")


def render_edit_task_page() -> None:
    if not require_login():
        return

    task_id = st.session_state.get("selected_task_id")
    if not task_id:
        st.warning("No task selected.")
        if st.button("Back to Dashboard", use_container_width=True):
            go_to("dashboard")
        return

    st.title("Edit Task")

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
        status_value = task["status"] if task["status"] in ["pending", "in-progress", "done"] else "pending"
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