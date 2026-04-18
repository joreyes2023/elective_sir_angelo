
import streamlit as st
from utils.auth import create_user, delete_user, list_user_accounts, update_user_password, update_user_role
from db import get_db


# ---------- CUSTOM CSS (DARK MODERN UI) ----------
st.markdown("""
<style>
.stApp {
    background-color: #0f172a;
    color: #e2e8f0;
}

h1, h2, h3 {
    color: #38bdf8;
}

[data-testid="metric-container"] {
    background-color: #1e293b;
    border: 1px solid #334155;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
}

.stButton>button {
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px;
    font-weight: bold;
}
.stButton>button:hover {
    background: linear-gradient(135deg, #0ea5e9, #4f46e5);
}

input, textarea {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

section[data-testid="stSidebar"] {
    background-color: #020617;
}

hr {
    border: 1px solid #334155;
}
</style>
""", unsafe_allow_html=True)

# ---------- CONSTANTS ----------
ALLOWED_ROLES = ["registrar", "faculty", "student"]
MANAGEABLE_ROLES = ["admin", "registrar", "faculty", "student"]

# ---------- DATABASE STATS ----------
def get_db_stats():
    try:
        db = get_db()
        return {
            "students": db.students.count_documents({}),
            "grades": db.grades.count_documents({}),
            "subjects": db.subjects.count_documents({}),
            "users": db.users.count_documents({}),
        }
    except Exception:
        return {"students": 0, "grades": 0, "subjects": 0, "users": 0}

# ---------- MAIN DASHBOARD ----------
def show_admin_dashboard():
    current_admin = st.session_state.get("username", "").strip().lower()

    # HEADER
    st.markdown("""
    <h1 style='text-align: center;'>⚙️ Admin Dashboard</h1>
    <p style='text-align: center; color:#94a3b8;'>
    Manage users, roles, and system data
    </p>
    """, unsafe_allow_html=True)

    # STATS
    stats = get_db_stats()
    col1, col2, col3, col4 = st.columns(4, gap="large")

    col1.metric("👨‍🎓 Students", stats["students"])
    col2.metric("📊 Grades", stats["grades"])
    col3.metric("📚 Subjects", stats["subjects"])
    col4.metric("👥 Users", stats["users"])

    st.markdown("---")

    # CREATE ACCOUNT SECTION
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("➕ Create New Account")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        role = st.selectbox("Role", ALLOWED_ROLES)

        if st.button("Create Account"):
            if not username.strip():
                st.error("Username cannot be empty.")
            elif password != password_confirm:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                if create_user(username, password, role):
                    st.success(f"{role.title()} account '{username}' created successfully.")
                else:
                    st.error("Username may already exist.")

    with col_right:
        st.subheader("📋 Existing Accounts")
        accounts = list_user_accounts()
        if accounts:
            st.dataframe(accounts, use_container_width=True)
        else:
            st.info("No accounts available.")

    st.markdown("---")

    # MANAGE ACCOUNT
    st.subheader("⚙️ Manage Account")

    accounts = list_user_accounts()
    usernames = [account["username"] for account in accounts]

    if usernames:
        selected_username = st.selectbox("Select User", usernames)
        selected_account = next(
            (acc for acc in accounts if acc["username"] == selected_username),
            {"username": selected_username, "role": "student"},
        )

        with st.form("manage_form"):
            new_role = st.selectbox("Role", MANAGEABLE_ROLES)
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("💾 Save Changes")

        if submitted:
            changed = False

            if selected_username == current_admin and new_role != "admin":
                st.error("You cannot change your own admin role.")
            else:
                if new_role != selected_account.get("role"):
                    if update_user_role(selected_username, new_role):
                        changed = True

                if new_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif len(new_password) < 6:
                        st.error("Password too short.")
                    elif update_user_password(selected_username, new_password):
                        changed = True

                if changed:
                    st.success("Account updated successfully.")
                    st.rerun()

        # DELETE ACCOUNT
        if selected_username != current_admin:
            if st.button("🗑 Delete Account"):
                if delete_user(selected_username):
                    st.success("Account deleted.")
                    st.rerun()
                else:
                    st.error("Failed to delete account.")
        else:
            st.warning("You cannot delete your own account.")

    else:
        st.info("No accounts available.")

    st.markdown("---")
    st.info("MongoDB connected: Data persists in BSIT3 database.")