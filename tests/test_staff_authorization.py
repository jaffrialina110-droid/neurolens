import unittest

from modules.staff_access import (
    can_view_staff_tasks,
    can_view_staff_directory,
    can_view_research_projects,
)

from modules.staff_access import (
    can_create_staff_task,
    can_manage_staff,
    can_update_staff_task,
)


class StaffAuthorizationPolicyTests(unittest.TestCase):
    def test_only_owner_can_manage_staff(self):
        self.assertTrue(can_manage_staff(True))
        self.assertFalse(can_manage_staff(False))
        self.assertFalse(can_manage_staff(None))

    def test_only_owner_can_create_staff_tasks(self):
        self.assertTrue(can_create_staff_task(True))
        self.assertFalse(can_create_staff_task(False))

    def test_staff_can_only_update_their_own_assigned_task(self):
        self.assertTrue(can_update_staff_task(
            False, "Researcher", "user-1", "user-1", "Completed"
        ))
        self.assertFalse(can_update_staff_task(
            False, "Researcher", "user-1", "user-2", "Completed"
        ))

    def test_unassigned_or_unknown_role_is_denied(self):
        self.assertFalse(can_update_staff_task(
            False, None, "user-1", "user-1", "Completed"
        ))
        self.assertFalse(can_update_staff_task(
            False, "Unknown", "user-1", "user-1", "Completed"
        ))

    def test_invalid_status_is_denied_even_for_owner(self):
        self.assertFalse(can_update_staff_task(
            True, None, "owner", "staff", "Delete Everything"
        ))
        self.assertFalse(can_update_staff_task(
            False, "Admin", "user-1", "user-1", "Delete Everything"
        ))

    def test_task_visibility_is_limited_to_owner_and_active_staff(self):
        self.assertTrue(can_view_staff_tasks(True, None))
        self.assertTrue(can_view_staff_tasks(False, "Researcher"))
        self.assertFalse(can_view_staff_tasks(False, None))
        self.assertFalse(can_view_staff_tasks(False, "Unknown"))

    def test_staff_directory_is_owner_or_admin_only(self):
        self.assertTrue(can_view_staff_directory(True, None))
        self.assertTrue(can_view_staff_directory(False, "Admin"))
        self.assertFalse(can_view_staff_directory(False, "Researcher"))
        self.assertFalse(can_view_staff_directory(False, "Moderator"))

    def test_research_projects_are_owner_admin_or_researcher(self):
        self.assertTrue(can_view_research_projects(True, None))
        self.assertTrue(can_view_research_projects(False, "Admin"))
        self.assertTrue(can_view_research_projects(False, "Researcher"))
        self.assertFalse(can_view_research_projects(False, "Moderator"))


if __name__ == "__main__":
    unittest.main()
