"""Small, pure authorization policies for NeuroLens staff operations.

These helpers are deliberately independent of Streamlit and database access so
that the access rules can be tested without loading the application.
"""

STAFF_TASK_STATUSES = {
    "Pending",
    "In Progress",
    "Completed",
    "On Hold",
}

STAFF_TASK_ROLES = {
    "Admin",
    "Researcher",
    "Moderator",
    "Support Staff",
}


def can_manage_staff(is_owner):
    """Only the authenticated platform Owner may provision or revoke staff."""
    return is_owner is True


def can_create_staff_task(is_owner):
    """Task assignment is controlled by the Owner, not by staff UI roles."""
    return is_owner is True


def can_update_staff_task(
    is_owner, active_role, actor_id, assigned_to, status
):
    """Owner can manage all tasks; staff can update only their own assigned task.

    The active role must come from the database, never from a caller-supplied
    role label. Admin's broader visibility does not grant task reassignment.
    """
    if is_owner is True:
        return status in STAFF_TASK_STATUSES

    if not actor_id or active_role not in STAFF_TASK_ROLES:
        return False

    if status not in STAFF_TASK_STATUSES:
        return False

    return str(actor_id) == str(assigned_to)
