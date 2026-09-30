"""
Goal routes — REST endpoints for user wellness goals.
Thin handlers that delegate to goal_service.
"""

from flask import Blueprint, request, jsonify, g

from backend.middleware.auth import require_auth
from backend.services import goal_service

goals_bp = Blueprint("goals", __name__)


@goals_bp.get("/goals")
@require_auth
def list_goals():
    """List goals for the authenticated user."""
    status_filter = request.args.get("status", "active")
    limit = request.args.get("limit", 10, type=int)

    try:
        goals = goal_service.list_for_user(
            user_id=g.user_id,
            status_filter=status_filter,
            limit=limit,
        )
        return jsonify({"goals": goals, "count": len(goals)})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@goals_bp.post("/goals")
@require_auth
def create_goal():
    """Create a new wellness goal for the authenticated user."""
    data = request.get_json(force=True) or {}
    title = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip()
    target_date = data.get("target_date")
    initial_progress = data.get("initial_progress", 0)

    try:
        goal = goal_service.create(
            user_id=g.user_id,
            title=title,
            category=category,
            target_date=target_date,
            initial_progress=initial_progress,
        )
        return jsonify({"goal": goal, "message": "Goal created successfully"}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@goals_bp.get("/goals/<int:goal_id>")
@require_auth
def get_goal(goal_id):
    """Get a specific goal by ID for the authenticated user."""
    goal = goal_service.get_by_id(user_id=g.user_id, goal_id=goal_id)
    if goal is None:
        return jsonify({"error": "Goal not found"}), 404

    return jsonify({"goal": goal})


@goals_bp.put("/goals/<int:goal_id>")
@require_auth
def update_goal(goal_id):
    """Update progress, status, or notes on an existing wellness goal."""
    data = request.get_json(force=True) or {}
    progress_pct = data.get("progress_pct")
    status = data.get("status")
    notes = data.get("notes")

    try:
        goal = goal_service.update(
            user_id=g.user_id,
            goal_id=goal_id,
            progress_pct=progress_pct,
            status=status,
            notes=notes,
        )
        if goal is None:
            return jsonify({"error": "Goal not found"}), 404

        return jsonify({"goal": goal, "message": "Goal updated successfully"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
