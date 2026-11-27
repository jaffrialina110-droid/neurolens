
"""NeuroLens Staff Workspace — role-based workspace draft."""

from datetime import datetime
import streamlit as st


ROLES = [
    "Admin",
    "Researcher",
    "Moderator",
    "Support Staff",
]


def render(st):
    st.title("👥 NeuroLens Staff Workspace")

    st.caption("Staff projects, tasks and collaboration workspace.")

    st.warning(
        "Draft module: real staff authentication and server-side "
        "role permissions must be connected before deployment."
    )

    # The main application must set this after authenticating staff.
    staff_user = st.session_state.get("authenticated_staff")

    if not isinstance(staff_user, dict):
        st.error("Please sign in through the main staff login system.")
        return

    staff_name = str(staff_user.get("name", "Staff Member"))
    role = str(staff_user.get("role", ""))

    if role not in ROLES:
        st.error("Your staff role is not recognized.")
        return

    st.subheader(f"Welcome, {staff_name}")
    st.write("Role:", role)

    st.divider()
    st.subheader("My Workspace")

    tasks = st.session_state.get("nl_staff_tasks", [])

    my_tasks = [
        task for task in tasks
        if task.get("assigned_to") == staff_name
    ]

    st.metric("My Assigned Tasks", len(my_tasks))

    if my_tasks:
        for index, task in enumerate(my_tasks):
            with st.expander(
                task.get("title", f"Task {index + 1}")
            ):
                st.write("Description:", task.get("description", ""))
                st.write("Status:", task.get("status", "Pending"))
                st.write("Project:", task.get("project", "General"))
    else:
        st.info("No tasks assigned to you yet.")

    st.divider()
    st.subheader("Research Projects")

    projects = st.session_state.get("nl_staff_projects", [])

    if projects:
        for project in projects:
            st.write(
                f"**{project.get('name', 'Untitled project')}**"
            )
            st.caption(project.get("description", ""))
    else:
        st.caption("No research projects have been added yet.")

    # Only Admin can create and assign tasks in this draft.
    if role == "Admin":
        st.divider()
        st.subheader("Admin — Task Management")

        with st.form("nl_staff_task_form"):
            title = st.text_input("Task title", max_chars=120)
            description = st.text_area(
                "Task description", max_chars=1000
            )
            assigned_to = st.text_input(
                "Assign to staff member", max_chars=100
            )
            project_name = st.text_input(
                "Project name", max_chars=120
            )

            submitted = st.form_submit_button("Create task")

        if submitted:
            if not title.strip() or not assigned_to.strip():
                st.error("Task title and staff member are required.")
            else:
                new_task = {
                    "title": title.strip(),
                    "description": description.strip(),
                    "assigned_to": assigned_to.strip(),
                    "project": project_name.strip() or "General",
                    "status": "Pending",
                    "created_at": datetime.now().isoformat(),
                }

                tasks.append(new_task)
                st.session_state["nl_staff_tasks"] = tasks

                st.success("Task added to this session.")

    st.divider()
    st.subheader("My Task Updates")

    if my_tasks:
        selected_task = st.selectbox(
            "Select your task",
            my_tasks,
            format_func=lambda task: task.get("title", "Task"),
        )

        new_status = st.selectbox(
            "Update task status",
            ["Pending", "In Progress", "Completed"],
        )

        if st.button("Save task status"):
            selected_task["status"] = new_status
            st.session_state["nl_staff_tasks"] = tasks
            st.success("Task status updated in this session.")

    st.caption(
        "Tasks and projects are currently session-based. "
        "Persistent storage, verified staff identities, "
        "and database-enforced permissions are still required."
    )
