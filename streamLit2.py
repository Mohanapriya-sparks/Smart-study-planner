import streamlit as st
import datetime
import pandas as pd
import re
import time
import random
import hashlib
import json
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import google.generativeai as genai

# -----------------------------
# Gemini Setup (SAFE VERSION)
# -----------------------------
genai.configure(api_key=st.secrets["AIzaSyAw6O9NY6QfsmT7laWHV_tDMNr3zKanGCg"])
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="Smart Study Planner", page_icon="📘", layout="wide")
st.title("📘 Smart Study Planner Hub")

menu = st.sidebar.radio("Navigate", [
    "Home", "Daily Planner", "Weekly Timetable",
    "Subjects & Goals", "Progress Tracker", "Settings",
    "Study Plan Generator"
])

# -----------------------------
# Home
# -----------------------------
if menu == "Home":
    st.header("Welcome!")
    st.write("Use sidebar to explore features 🚀")

# -----------------------------
# Weekly Timetable
# -----------------------------
elif menu == "Weekly Timetable":
    st.header("📅 Weekly Timetable")
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    for day in days:
        with st.expander(day):
            st.text_area(f"Events for {day}", key=day)

# -----------------------------
# Subjects & Goals
# -----------------------------
elif menu == "Subjects & Goals":
    st.header("🎯 Subjects & Goals")
    st.text_area("Subjects (one per line)", key="subjects")
    st.slider("Target GPA", 2.0, 4.0, 3.5)

# -----------------------------
# Progress Tracker
# -----------------------------
elif menu == "Progress Tracker":
    st.header("📈 Progress Tracker")
    df = pd.DataFrame({
        "Date": pd.date_range(end=datetime.date.today(), periods=7),
        "Hours": [2,3,1,4,3,2.5,4]
    }).set_index("Date")
    st.line_chart(df)

# -----------------------------
# Settings
# -----------------------------
elif menu == "Settings":
    st.header("⚙ Settings")
    st.text_input("Your Name")
    st.checkbox("Enable Dark Mode")

# -----------------------------
# DAILY PLANNER (FIXED)
# -----------------------------
elif menu == "Daily Planner":
    st.title("📚 Smart Daily Study Plan")

    theme = st.selectbox("Theme", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("""
        <style>
        .stApp { background-color:#0e1117; color:white; }
        </style>
        """, unsafe_allow_html=True)

    quotes = [
        "Push yourself 💪",
        "Stay consistent 🔥",
        "Small steps daily 📈",
        "You got this 🚀"
    ]
    st.sidebar.info(random.choice(quotes))

    task_list = st.text_area("Tasks (one per line)")
    duration = st.text_input("Duration (e.g. 3 days, 1 week)")
    study_material = st.text_area("Study material (optional)")

    if "study_plan" not in st.session_state:
        st.session_state.study_plan = {}
    if "completed" not in st.session_state:
        st.session_state.completed = []

    # FIXED duration parser
    def parse_duration(text):
        match = re.match(r'(\d+)\s*(day|days|week|weeks|month|months)', text.lower())
        if not match:
            return 1
        num = int(match.group(1))
        unit = match.group(2)

        return {
            "day": num,
            "days": num,
            "week": num * 7,
            "weeks": num * 7,
            "month": num * 30,
            "months": num * 30
        }.get(unit, 1)

    # ---------------- AI PLAN ----------------
    if st.button("Generate Plan 🤖"):
        if task_list and duration:
            tasks = [t.strip() for t in task_list.splitlines() if t.strip()]
            materials = [m.strip() for m in study_material.splitlines() if m.strip()]
            days = parse_duration(duration)

            prompt = f"""
Return ONLY valid JSON like:
{{
  "Day 1": [{{"task":"...", "material":"..."}}],
  "Day 2": []
}}

Tasks: {tasks}
Materials: {materials}
Duration: {days} days
"""

            try:
                response = model.generate_content(prompt)
                text = response.text.strip()

                # safer JSON extraction
                text = text.replace("```json", "").replace("```", "")
                daily_plan = json.loads(text)

                st.session_state.study_plan = daily_plan
                st.session_state.completed = []

                st.success("AI Plan Generated ✅")

            except Exception as e:
                st.error("AI failed, using fallback plan")

                fallback = {f"Day {i+1}": [] for i in range(days)}
                for i, task in enumerate(tasks):
                    day = f"Day {(i % days) + 1}"
                    fallback[day].append({
                        "task": task,
                        "material": materials[i % len(materials)] if materials else ""
                    })

                st.session_state.study_plan = fallback
                st.session_state.completed = []

    # ---------------- DISPLAY PLAN ----------------
    plan = st.session_state.study_plan

    if plan:
        total = sum(len(v) for v in plan.values())

        for day, tasks in plan.items():
            with st.expander(day):
                for t in tasks:
                    task = t["task"]
                    mat = t.get("material", "")

                    key = hashlib.md5(f"{day}{task}".encode()).hexdigest()

                    if st.checkbox(task, key=key):
                        if key not in st.session_state.completed:
                            st.session_state.completed.append(key)

                            st.success(random.choice([
                                "Nice work 🔥",
                                "Keep going 💪",
                                "Great progress 🚀"
                            ]))

                            if mat:
                                st.write("📖", mat)

                            st.balloons()

        done = len(st.session_state.completed)
        st.progress(done / total if total else 0)
        st.info(f"{done}/{total} completed")

# -----------------------------
# AI Study Plan Generator
# -----------------------------
elif menu == "Study Plan Generator":
    st.title("🤖 AI Study Planner")

    topic = st.text_input("Topic")
    duration = st.selectbox("Duration", ["1 week","2 weeks","1 month","3 months"])
    level = st.selectbox("Level", ["Beginner","Intermediate","Advanced"])

    if st.button("Generate"):
        if topic:
            prompt = f"""
Create a structured study plan:

Topic: {topic}
Duration: {duration}
Level: {level}

Include:
- weekly breakdown
- resources
- practice tasks
- projects
"""

            try:
                res = model.generate_content(prompt)
                st.markdown(res.text)

                st.download_button(
                    "Download Plan",
                    res.text,
                    file_name=f"{topic}_plan.txt"
                )

            except Exception as e:
                st.error(str(e))
            st.warning("Please enter a topic to generate a study plan.")
