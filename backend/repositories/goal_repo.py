"""
Goal repository — data access for the goals table.
"""

from backend.db import query, execute


def create(user_id, title, category, target_date=None, initial_progress=0):
    """Create a new goal and return the created row."""
    return query(
        """
        INSERT INTO goals (user_id, title, category, target_date, progress_pct)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, title, category, target_date, status, progress_pct,
                  notes, created_at, updated_at
        """,
        (user_id, title, category, target_date, initial_progress),
        fetchone=True,
    )


def list_by_user(user_id, status_filter=None, limit=10):
    """List goals for a user, optionally filtered by status."""
    if status_filter and status_filter != "all":
        return query(
            """
            SELECT id, title, category, target_date, status, progress_pct,
                   notes, created_at, updated_at
            FROM goals
            WHERE user_id = %s AND status = %s
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (user_id, status_filter, limit),
            fetchall=True,
        ) or []
    else:
        return query(
            """
            SELECT id, title, category, target_date, status, progress_pct,
                   notes, created_at, updated_at
            FROM goals
            WHERE user_id = %s
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            (user_id, limit),
            fetchall=True,
        ) or []


def find_by_id_and_user(goal_id, user_id):
    """Find a goal by ID, scoped to a user."""
    return query(
        """
        SELECT id, title, category, target_date, status, progress_pct,
               notes, created_at, updated_at
        FROM goals
        WHERE id = %s AND user_id = %s
        """,
        (goal_id, user_id),
        fetchone=True,
    )


def update(goal_id, user_id, progress_pct=None, status=None, notes=None):
    """Update goal fields. Only non-None fields are updated.

    Returns the updated row or None if not found / not owned.
    """
    goal = find_by_id_and_user(goal_id, user_id)
    if goal is None:
        return None

    new_progress = progress_pct if progress_pct is not None else goal["progress_pct"]
    new_status = status if status is not None else goal["status"]

    # Append notes rather than replace
    if notes:
        existing = goal["notes"] or ""
        separator = "\n" if existing else ""
        new_notes = existing + separator + notes
    else:
        new_notes = goal["notes"]

    return query(
        """
        UPDATE goals
        SET progress_pct = %s, status = %s, notes = %s
        WHERE id = %s AND user_id = %s
        RETURNING id, title, category, target_date, status, progress_pct,
                  notes, created_at, updated_at
        """,
        (new_progress, new_status, new_notes, goal_id, user_id),
        fetchone=True,
    )
