
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from db import get_grade_rows, get_students, get_subjects



# ---------- MODERN DARK UI ----------
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
    padding: 14px;
    border-radius: 12px;
    box-shadow: 0 0 8px rgba(0,0,0,0.3);
}

.stButton>button {
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    color: white;
    border-radius: 10px;
    font-weight: bold;
    border: none;
}

section[data-testid="stSidebar"] {
    background-color: #020617;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;'>🎓 Student Performance Dashboard</h1>
<p style='text-align:center;color:#94a3b8;'>
Grades • Progress • Curriculum • Analytics
</p>
""", unsafe_allow_html=True)


# ---------- HELPERS ----------
def _grade_ranges(grades: pd.Series):
    bins = [0, 59.99, 69.99, 79.99, 89.99, 100]
    labels = ["Below 60", "60-69", "70-79", "80-89", "90-100"]
    return pd.cut(grades, bins=bins, labels=labels, include_lowest=True)


@st.cache_data
def load_data():
    df = pd.DataFrame(get_grade_rows())
    if df.empty:
        return df

    students = {str(s["_id"]): s for s in get_students()}
    subjects = {str(s.get("subject_code")): s.get("subject_name","") for s in get_subjects()}

    df["student_name"] = df["student_id"].astype(str).map(
        lambda x: students.get(x, {}).get("student_name","Unknown")
    )

    df["program"] = df["student_id"].astype(str).map(
        lambda x: students.get(x, {}).get("Course","")
    )

    df["subject_name"] = df["subject_code"].astype(str).map(subjects)
    df["grade"] = pd.to_numeric(df["grade"], errors="coerce")

    df["pass_fail"] = df["grade"].apply(lambda x: "Pass" if pd.notna(x) and x >= 75 else "Fail")

    return df


# ---------- MAIN ----------
def show_students_dashboard():

    df = load_data()
    if df.empty:
        st.warning("No data available.")
        return

    # ---------- FILTERS ----------
    col1, col2, col3 = st.columns(3)

    student = col1.selectbox("🎓 Student", ["All"] + sorted(df["student_name"].unique()))
    subject = col2.selectbox("📘 Subject", ["All"] + sorted(df["subject_code"].unique()))
    term = col3.selectbox("📅 Term", ["All"] + sorted(df["term"].unique()))

    if student != "All":
        df = df[df["student_name"] == student]
    if subject != "All":
        df = df[df["subject_code"] == subject]
    if term != "All":
        df = df[df["term"] == term]

    if df.empty:
        st.warning("No matching records.")
        return

    # ---------- METRICS ----------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", len(df))
    c2.metric("Students", df["student_id"].nunique())
    c3.metric("Subjects", df["subject_code"].nunique())
    c4.metric("Average Grade", round(df["grade"].mean(), 2))

    st.markdown("---")

    # ---------- TABS ----------
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Grades",
        "📈 Progress",
        "⚠️ Risk Analysis",
        "📋 Curriculum"
    ])

    # ---------- TAB 1 ----------
    with tab1:
        st.subheader("Grade Distribution")

        clean = df.dropna(subset=["grade"])
        if not clean.empty:
            clean["Range"] = _grade_ranges(clean["grade"])

            dist = clean["Range"].value_counts().reindex(
                ["Below 60","60-69","70-79","80-89","90-100"]
            ).fillna(0)

            fig, ax = plt.subplots()
            dist.plot(kind="bar", ax=ax, color="skyblue", edgecolor="black")
            st.pyplot(fig)

    # ---------- TAB 2 ----------
    with tab2:
        st.subheader("Performance Trend")

        if student == "All":
            st.info("Select a student to view trend.")
        else:
            trend = df[df["student_name"] == student].groupby("term")["grade"].mean()

            st.line_chart(trend)

    # ---------- TAB 3 ----------
    with tab3:
        st.subheader("At Risk Students")

        risk = df[(df["grade"] < 75) | (df["grade"].isna())]

        st.dataframe(
            risk[["student_name","subject_code","grade","term"]],
            use_container_width=True
        )

    # ---------- TAB 4 ----------
    with tab4:
        st.subheader("Curriculum Overview")

        df["status"] = df["grade"].apply(
            lambda x: "Completed" if pd.notna(x) and x >= 75
            else ("Pending" if pd.isna(x) else "Failed")
        )

        st.dataframe(
            df[["student_name","subject_code","term","grade","status"]],
            use_container_width=True
        )
