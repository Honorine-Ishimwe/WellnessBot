"""
Goal service — business logic for wellness goal management.
No Flask imports — pure Python logic.
"""

from backend.repositories import goal_repo

# Valid categories and statuses (must match schema.sql CHECK constraints)
VALID_CATEGORIES = {"sleep", "hydration", "mindfulness", "activity", "nutrition", "other"}
VALID_STATUSES = {"active", "in_progress", "completed", "abandoned"}


def create(user_id, title, category, target_date=None, initial_progress=0):
    """Create a new wellness goal with validation.

    Returns the created goal dict.
    Raises ValueError for invalid inputs.
    """
    if not title or not title.strip():
        raise ValueError("Goal title cannot be empty")

    category = (category or "").lower().strip()
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"Invalid category '{category}'. "
            f"Must be one of: {', '.join(sorted(VALID_CATEGORIES))}"
        )

    # Clamp progress to 0-100
    initial_progress = max(0, min(100, int(initial_progress)))

    row = goal_repo.create(
        user_id=user_id,
        title=title.strip(),
        category=category,
        target_date=target_date,
        initial_progress=initial_progress,
    )
    return _serialize_goal(row)


def list_for_user(user_id, status_filter="active", limit=10):
    """List goals for a user with optional status filter.

    Returns a list of goal dicts with ISO-formatted dates.
    """
    if status_filter and status_filter != "all" and status_filter not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status filter '{status_filter}'. "
            f"Must be one of: {', '.join(sorted(VALID_STATUSES))}, all"
        )

    rows = goal_repo.list_by_user(user_id, status_filter, limit)
    return [_serialize_goal(row) for row in rows]


def update(user_id, goal_id, progress_pct=None, status=None, notes=None):
    """Update a goal's progress, status, or notes.

    Returns the updated goal dict or None if not found/unauthorized.
    Raises ValueError for invalid inputs.
    """
    if progress_pct is not None:
        progress_pct = max(0, min(100, int(progress_pct)))

    if status is not None:
        status = status.lower().strip()
        if status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Must be one of: {', '.join(sorted(VALID_STATUSES))}"
            )

    row = goal_repo.update(
        goal_id=goal_id,
        user_id=user_id,
        progress_pct=progress_pct,
        status=status,
        notes=notes,
    )

    if row is None:
        return None

    return _serialize_goal(row)


def get_by_id(user_id, goal_id):
    """Get a single goal by ID, scoped to the user.

    Returns goal dict or None.
    """
    row = goal_repo.find_by_id_and_user(goal_id, user_id)
    if row is None:
        return None
    return _serialize_goal(row)


def _serialize_goal(row):
    """Convert a goal DB row to a JSON-safe dict with ISO dates."""
    goal = dict(row)
    if goal.get("created_at"):
        goal["created_at"] = goal["created_at"].isoformat()
    if goal.get("updated_at"):
        goal["updated_at"] = goal["updated_at"].isoformat()
    if goal.get("target_date"):
        goal["target_date"] = goal["target_date"].isoformat()
    return goal
