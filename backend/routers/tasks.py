from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.auth import get_current_user
from backend.database import get_connection
from backend.schemas import (
    MessageResponse,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TaskSummary,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _row_to_task_response(row) -> TaskResponse:
    due_date = row["due_date"]
    parsed_due_date = date.fromisoformat(due_date) if due_date else None

    return TaskResponse(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        status=row["status"],
        due_date=parsed_due_date,
        owner_email=row["owner_email"],
    )


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    current_user: str = Depends(get_current_user),
) -> TaskResponse:
    due_date = payload.due_date.isoformat() if payload.due_date else None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (title, description, priority, status, due_date, owner_email)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.title,
                payload.description,
                payload.priority,
                payload.status,
                due_date,
                current_user,
            ),
        )
        conn.commit()
        task_id = cursor.lastrowid

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task",
        )

    return _row_to_task_response(row)


@router.get("/", response_model=list[TaskResponse])
def get_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    current_user: str = Depends(get_current_user),
) -> list[TaskResponse]:
    query = "SELECT * FROM tasks WHERE owner_email = ?"
    params: list[str] = [current_user]

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY id ASC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

    return [_row_to_task_response(row) for row in rows]


@router.get("/summary", response_model=TaskSummary)
def get_task_summary(current_user: str = Depends(get_current_user)) -> TaskSummary:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'in-progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'done' THEN 1 ELSE 0 END) AS done
            FROM tasks
            WHERE owner_email = ?
            """,
            (current_user,),
        )
        row = cursor.fetchone()

    return TaskSummary(
        total=row["total"] or 0,
        pending=row["pending"] or 0,
        in_progress=row["in_progress"] or 0,
        done=row["done"] or 0,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    current_user: str = Depends(get_current_user),
) -> TaskResponse:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if row["owner_email"] != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this task",
        )

    return _row_to_task_response(row)


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    current_user: str = Depends(get_current_user),
) -> TaskResponse:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing_task = cursor.fetchone()

        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        if existing_task["owner_email"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to update this task",
            )

        due_date = payload.due_date.isoformat() if payload.due_date else None

        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, status = ?, due_date = ?
            WHERE id = ?
            """,
            (
                payload.title,
                payload.description,
                payload.priority,
                payload.status,
                due_date,
                task_id,
            ),
        )
        conn.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_row = cursor.fetchone()

    return _row_to_task_response(updated_row)


@router.patch("/{task_id}/status", response_model=MessageResponse)
def update_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    current_user: str = Depends(get_current_user),
) -> MessageResponse:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing_task = cursor.fetchone()

        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        if existing_task["owner_email"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to update this task",
            )

        cursor.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (payload.status, task_id),
        )
        conn.commit()

    return MessageResponse(message="Task status updated successfully")


@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: int,
    current_user: str = Depends(get_current_user),
) -> MessageResponse:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing_task = cursor.fetchone()

        if not existing_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        if existing_task["owner_email"] != current_user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to delete this task",
            )

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()

    return MessageResponse(message="Task deleted successfully")