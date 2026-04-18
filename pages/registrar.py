
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
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0 0 10px rgba(0,0,0,0.3);
}

.stButton>button {
    background: linear-gradient(135deg, #38bdf8, #6366f1);
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: bold;
}

section[data-testid="stSidebar"] {
    background-color: #020617;
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;'>📊 Registrar Analytics Dashboard</h1>
<p style='text-align:center;color:#94a3b8;'>Student Performance • Reports • Insights</p>
""", unsafe_allow_html=True)


# ---------- DATA FUNCTIONS ----------
def _normalize_term_label(value):
    text = str(value).strip().lower()
    if "1st" in text: return "1st Semester"
    if "2nd" in text: return "2nd Semester"
    if "summer" in text: return "Summer"
    return text


@st.cache_data
def build_df():
    df = pd.DataFrame(get_grade_rows())
    if df.empty:
        return df

    students = {str(s["_id"]): s for s in get_students()}
    subjects = {str(s.get("subject_code")): s.get("subject_name", "") for s in get_subjects()}

    df["student_name"] = df["student_id"].astype(str).map(
        lambda x: students.get(x, {}).get("student_name", "Unknown")
    )
    df["program"] = df["student_id"].astype(str).map(
        lambda x: students.get(x, {}).get("Course", "")
    )
    df["subject_name"] = df["subject_code"].astype(str).map(subjects)
    df["term"] = df["term"].astype(str).map(_normalize_term_label)

    df["grade"] = pd.to_numeric(df["grade"], errors="coerce")
    df["pass_fail"] = df["grade"].apply(lambda x: "Pass" if x >= 75 else "Fail")

    return df


# ---------- MAIN ----------
def show_registrar_dashboard():
    df = build_df()

    if df.empty:
        st.error("No data found.")
        return

    # ---------- FILTERS ----------
    col1, col2, col3 = st.columns(3)

    term = col1.selectbox("📅 Term", ["All"] + sorted(df["term"].dropna().unique()))
    subject = col2.selectbox("📘 Subject", ["All"] + sorted(df["subject_code"].dropna().unique()))
    program = col3.selectbox("🎓 Program", ["All"] + sorted(df["program"].dropna().unique()))

    if term != "All":
        df = df[df["term"] == term]
    if subject != "All":
        df = df[df["subject_code"] == subject]
    if program != "All":
        df = df[df["program"] == program]

    # ---------- METRICS ----------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Records", len(df))
    c2.metric("👨‍🎓 Students", df["student_id"].nunique())
    c3.metric("📚 Subjects", df["subject_code"].nunique())
    c4.metric("📊 Avg Grade", round(df["grade"].mean(), 2))

    st.markdown("---")

    # ---------- GPA DISTRIBUTION ----------
    st.subheader("📊 GPA Distribution")
    gpa = df.groupby("student_id")["grade"].mean()

    fig, ax = plt.subplots()
    ax.hist(gpa.dropna(), bins=10)
    st.pyplot(fig)

    # ---------- DEAN'S LIST ----------
    st.subheader("🏆 Dean's List")
    dean = df.groupby(["student_id", "student_name"])["grade"].mean().reset_index()
    dean = dean[dean["grade"] >= 90]

    st.dataframe(dean.rename(columns={"grade": "GPA"}), use_container_width=True)

    # ---------- PROBATION ----------
    st.subheader("⚠️ Probation List")
    prob = df.groupby(["student_id", "student_name"])["grade"].mean().reset_index()
    prob = prob[prob["grade"] < 75]

    st.dataframe(prob.rename(columns={"grade": "GPA"}), use_container_width=True)

    # ---------- PASS FAIL ----------
    st.subheader("📊 Pass vs Fail")
    counts = df["pass_fail"].value_counts()

    fig, ax = plt.subplots()
    ax.bar(counts.index, counts.values)
    st.pyplot(fig)

    # ---------- ENROLLMENT ----------
    st.subheader("📈 Enrollment Trend")
    trend = df.groupby("term")["student_id"].nunique()

    st.line_chart(trend)

    # ---------- TOP STUDENTS ----------
    st.subheader("🌟 Top Performers")
    top = df.groupby(["program", "student_name"])["grade"].mean().reset_index()
    top = top.sort_values("grade", ascending=False).head(10)

    st.dataframe(top.rename(columns={"grade": "GPA"}), use_container_width=True)

    # ---------- TABLE ----------
    st.subheader("📋 Full Data")
    st.dataframe(df, use_container_width=True)