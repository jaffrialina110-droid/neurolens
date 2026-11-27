
"""NeuroLens Appointments — appointment request module."""

from datetime import date, datetime, time
import streamlit as st


def render(st):
    st.title("📅 Appointments with Ayna Jaffri")

    st.write(
        "Request a session for NeuroLens discussion, "
        "research guidance or collaboration."
    )

    st.info(
        "This form submits a request. Your appointment is not "
        "confirmed until availability is reviewed and confirmed."
    )

    with st.form("nl_appointment_request"):
        purpose = st.selectbox(
            "Appointment purpose",
            [
                "NeuroLens Discussion",
                "Research Guidance",
                "Research Collaboration",
                "Cognitive Neuroscience Discussion",
                "Other",
            ],
        )

        preferred_date = st.date_input(
            "Preferred date",
            min_value=date.today(),
        )

        preferred_time = st.selectbox(
            "Preferred time",
            [
                "Morning",
                "Afternoon",
                "Evening",
            ],
        )

        communication = st.radio(
            "Preferred communication method",
            [
                "Text",
                "Email",
                "Video call (if available and agreed)",
                "Voice call (if available and agreed)",
            ],
        )

        contact = st.text_input(
            "Your email or preferred contact detail",
            max_chars=150,
        )

        message = st.text_area(
            "Additional details",
            max_chars=1000,
        )

        submitted = st.form_submit_button(
            "Submit appointment request",
            use_container_width=True,
        )

    if submitted:
        if not contact.strip():
            st.error("Please enter a contact detail.")
        else:
            request = {
                "purpose": purpose,
                "date": preferred_date.isoformat(),
                "time_preference": preferred_time,
                "communication": communication,
                "contact": contact.strip(),
                "message": message.strip(),
                "status": "Pending review",
                "created_at": datetime.now().isoformat(),
            }

            requests = st.session_state.get(
                "nl_appointment_requests", []
            )
            requests.append(request)

            st.session_state["nl_appointment_requests"] = requests

            st.success(
                "Your appointment request has been recorded "
                "in this session. It is not yet confirmed."
            )

    st.divider()
    st.subheader("Payment information")

    st.write(
        "Any applicable fee and payment instructions must be "
        "shown and confirmed before a booking is accepted."
    )

    st.caption(
        "Payment credentials and fees must be configured securely "
        "by the platform owner. No payment is collected by this draft module."
    )

    st.divider()
    st.subheader("My appointment requests")

    requests = st.session_state.get(
        "nl_appointment_requests", []
    )

    if not requests:
        st.caption("You have no appointment requests in this session.")
    else:
        for index, request in enumerate(reversed(requests), 1):
            with st.expander(
                f"Request {index} — {request['purpose']}"
            ):
                st.write("Date:", request["date"])
                st.write("Preferred time:", request["time_preference"])
                st.write("Communication:", request["communication"])
                st.write("Status:", request["status"])
