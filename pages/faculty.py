
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from db import get_grade_rows, get_students, get_subjects



# ---------- MODERN UI ----------
st.markdown("""
<style>
.stApp {background-color:#0f172a;color:#e2e8f0;}
h1,h2,h3 {color:#38bdf8;}
[data-testid="metric-container"] {
    background:#1e293b;border:1px solid #334155;
    padding:15px;border-radius:12px;
}
.stButton>button {
    background:linear-gradient(135deg,#38bdf8,#6366f1);
    color:white;border-radius:10px;font-weight:bold;
}
section[data-testid="stSidebar"] {background:#020617;}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<h1 style='text-align:center;'>👨‍🏫 Faculty Analytics Dashboard</h1>
<p style='text-align:center;color:#94a3b8;'>Performance • Monitoring • Insights</p>
""", unsafe_allow_html=True)

# ---------- DATA ----------
@st.cache_data
def load_data():
    df = pd.DataFrame(get_grade_rows())
    students = {str(s["_id"]): s for s in get_students()}
    subjects = {str(s.get("subject_code")): s.get("subject_name","") for s in get_subjects()}

    if df.empty:
        return df

    df["student_name"] = df["student_id"].astype(str).map(
        lambda x: students.get(x, {}).get("student_name","Unknown")
    )
    df["program"] = df["student_id"].astype(str).map(
        lambda x: students.get(x, {}).get("Course","")
    )
    df["subject_name"] = df["subject_code"].astype(str).map(subjects)

    df["grade"] = pd.to_numeric(df["grade"], errors="coerce")
    df["pass_fail"] = df["grade"].apply(lambda x: "Pass" if x>=75 else "Fail")

    return df

# ---------- MAIN ----------
def show_faculty_dashboard():
    df = load_data()
    if df.empty:
        st.error("No data found.")
        return

    # ---------- FILTERS ----------
    col1,col2,col3,col4 = st.columns(4)
    teacher = col1.selectbox("👨‍🏫 Teacher", ["All"]+sorted(df["teacher"].dropna().unique()))
    subject = col2.selectbox("📘 Subject", ["All"]+sorted(df["subject_code"].dropna().unique()))
    term = col3.selectbox("📅 Term", ["All"]+sorted(df["term"].dropna().unique()))
    program = col4.selectbox("🎓 Program", ["All"]+sorted(df["program"].dropna().unique()))

    if teacher!="All": df=df[df["teacher"]==teacher]
    if subject!="All": df=df[df["subject_code"]==subject]
    if term!="All": df=df[df["term"]==term]
    if program!="All": df=df[df["program"]==program]

    if df.empty:
        st.warning("No data after filtering.")
        return

    # ---------- METRICS ----------
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📄 Records", len(df))
    c2.metric("👨‍🎓 Students", df["student_id"].nunique())
    c3.metric("📚 Subjects", df["subject_code"].nunique())
    c4.metric("📊 Avg Grade", round(df["grade"].mean(),2))

    st.markdown("---")

    # ---------- TABS ----------
    tab1,tab2,tab3,tab4,tab5 = st.tabs([
        "📊 Distribution",
        "📈 Progress",
        "⚠️ At Risk",
        "📋 Submission",
        "📑 Data"
    ])

    # ---------- DISTRIBUTION ----------
    with tab1:
        st.subheader("Grade Distribution")
        fig,ax=plt.subplots()
        ax.hist(df["grade"].dropna(),bins=10)
        st.pyplot(fig)

        pf=df["pass_fail"].value_counts()
        fig,ax=plt.subplots()
        ax.bar(pf.index,pf.values)
        st.pyplot(fig)

    # ---------- PROGRESS ----------
    with tab2:
        st.subheader("Student Progress")
        progress=df.groupby(["term","student_name"])["grade"].mean().unstack()
        st.line_chart(progress)

    # ---------- AT RISK ----------
    with tab3:
        st.subheader("At Risk Students")
        risk=df[(df["grade"]<75) | (df["grade"].isna())]
        st.dataframe(risk[["student_name","subject_code","grade"]],use_container_width=True)

    # ---------- SUBMISSION ----------
    with tab4:
        st.subheader("Submission Status")
        df["submitted"]=df["grade"].notna()
        sub=df.groupby("subject_code")["submitted"].mean()*100
        st.bar_chart(sub)

    # ---------- FULL DATA ----------
    with tab5:
        st.subheader("Full Dataset")
        st.dataframe(df,use_container_width=True)