import streamlit as st
import datetime
import pandas as pd
import re
import time
import random
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components
import google.generativeai as genai

# Initialize Gemini client
genai.configure(api_key="AIzaSyDTrzcaUzOX5XQvpf6JGByPNOzXtsEj3dg")
model = genai.GenerativeModel('gemini-pro')

# -----------------------------
# Scaffold: Smart Study Planner Hub
# -----------------------------

st.set_page_config(page_title="Smart Study Planner", page_icon="📘", layout="wide")
st.title("📘 Smart Study Planner Hub")

# Sidebar menu
menu = st.sidebar.radio("Navigate", [
    "Home", "Daily Planner", "Weekly Timetable",
    "Subjects & Goals", "Progress Tracker", "Settings", "Study Plan Generator"
])

# -----------------------------
# Home Page
# -----------------------------
if menu == "Home":
    st.header("Welcome!")
    st.write("Use the sidebar to explore features:")
    st.markdown("""
    - *Daily Planner*: Smart task breakdown
    - *Weekly Timetable*: Add fixed class/work events
    - *Subjects & Goals*: Track your academic goals
    - *Progress Tracker*: Visualize your study trends
    - *Settings*: Personal preferences
    """)

# -----------------------------
# Weekly Timetable Input
# -----------------------------
elif menu == "Weekly Timetable":
    st.header("📅 Weekly Timetable")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for day in days:
        with st.expander(f"Schedule for {day}"):
            st.text_area(f"Enter events for {day} (e.g., 9am-11am Physics)", key=day)

# -----------------------------
# Subjects & Goals
# -----------------------------
elif menu == "Subjects & Goals":
    st.header("🎯 Set Your Subjects & Goals")
    st.text_area("Enter subjects (one per line):", key="subjects")
    st.slider("Target GPA:", 2.0, 4.0, 3.5, 0.1)

# -----------------------------
# Progress Tracker (Dummy View)
# -----------------------------
elif menu == "Progress Tracker":
    st.header("📈 Study Progress")
    df = pd.DataFrame({
        "Date": pd.date_range(end=datetime.date.today(), periods=7),
        "Hours Studied": [2, 3, 1, 4, 3, 2.5, 4]
    }).set_index("Date")
    st.line_chart(df)
    st.info("Track your daily study hours here.")

# -----------------------------
# Settings Page
# -----------------------------
elif menu == "Settings":
    st.header("⚙ Settings")
    st.text_input("Your Name:")
    st.checkbox("Enable Dark Mode")

# -----------------------------
# Daily Planner (YOUR ORIGINAL CODE)
# -----------------------------
elif menu == "Daily Planner":
    st.title("📚 Smart Daily Study Plan Generator")

    # Theme
    theme = st.selectbox("Select Theme:", ["Light", "Dark"])
    if theme == "Dark":
        st.markdown("""
            <style>
            body { background-color: #0e1117; color: #fafafa; }
            .stApp { background-color: #0e1117; color: #fafafa; }
            </style>
        """, unsafe_allow_html=True)

    # Sidebar motivation
    quotes = [
        "Believe in yourself and all that you are.",
        "Push yourself, because no one else is going to do it for you.",
        "Success is the sum of small efforts repeated day in and day out.",
        "Stay positive, work hard, make it happen.",
        "Discipline is choosing between what you want now and what you want most."
    ]
    st.sidebar.title("Daily Motivation")
    st.sidebar.info(random.choice(quotes))

    # Inputs
    task_list = st.text_area("✍ Enter your tasks (one per line):", key="tasks")
    duration = st.text_input("⏳ Enter study duration (like '3 days', '1 week'):", key="duration")
    study_material = st.text_area("📖 Enter study materials (one per line, relevant for topics):", key="study_material")

    # Session vars
    if 'study_plan' not in st.session_state:
        st.session_state['study_plan'] = {}
    if 'completed' not in st.session_state:
        st.session_state['completed'] = []

    # Helper to parse duration
    def parse_duration(duration_str):
        match = re.match(r'(\d+)\s*(day|week|month)', duration_str.lower())
        if not match:
            return 1
        num = int(match.group(1))
        unit = match.group(2)
        return {
            'day': num,
            'week': num * 7,
            'month': num * 30
        }.get(unit, 1)

    # Generate Study Plan with Gemini AI
    if st.button("Generate Smart Study Plan with AI", use_container_width=True):
        if task_list.strip() and duration.strip():
            tasks = [t.strip() for t in task_list.splitlines() if t.strip()]
            study_materials = [sm.strip() for sm in study_material.splitlines() if sm.strip()]
            days = parse_duration(duration)
            
            try:
                # Generate prompt for Gemini
                prompt = f"""
                Create an optimized study plan with the following:
                - Tasks: {', '.join(tasks)}
                - Study materials: {', '.join(study_materials) if study_materials else 'None provided'}
                - Duration: {days} days
                
                The plan should:
                1. Group related topics together
                2. Balance workload across days
                3. Include estimated time per task
                4. Suggest study techniques for each topic
                5. Recommend relevant resources if none provided
                
                Format as a numbered list by day with clear sections.
                """
                
                # Call Gemini API
                response = model.generate_content(prompt)
                ai_plan = response.text
                
                # Parse the AI response into our daily plan format
                daily_plan = {}
                current_day = None
                
                for line in ai_plan.split('\n'):
                    if line.strip().startswith("Day") or line.strip().startswith("Week"):
                        current_day = line.strip()
                        daily_plan[current_day] = []
                    elif line.strip() and current_day:
                        # Extract task and materials from AI response
                        task_info = {"task": line.strip(), "study_material": ""}
                        if study_materials:
                            task_info["study_material"] = study_materials[len(daily_plan[current_day]) % len(study_materials)]
                        daily_plan[current_day].append(task_info)
                
                st.session_state['study_plan'] = daily_plan
                st.session_state['completed'] = []
                st.success("✅ AI-Generated Study Plan Ready!")
                
                # Show full AI response in expander
                with st.expander("See AI-Generated Plan Details"):
                    st.write(ai_plan)
                    
            except Exception as e:
                st.error(f"AI generation failed: {str(e)}")
                # Fall back to simple distribution if AI fails
                daily_plan = {f"Day {i+1}": [] for i in range(days)}
                for i, task in enumerate(tasks):
                    day = f"Day {(i % days) + 1}"
                    daily_plan[day].append({"task": task, "study_material": study_materials[i % len(study_materials)]})
                st.session_state['study_plan'] = daily_plan
                st.session_state['completed'] = []
                st.success("✅ Basic Study Plan Ready (AI failed)")
        else:
            st.warning("⚠ Please enter both tasks and duration.")

    # Display Plan (same as before)
    study_plan = st.session_state['study_plan']
    if study_plan:
        total_tasks = sum(len(day_tasks) for day_tasks in study_plan.values())

        for day, day_tasks in study_plan.items():
            with st.expander(f"📅 {day}"):
                for task_info in day_tasks:
                    task = task_info["task"]
                    study_material = task_info["study_material"]
                    task_key = f"{day}_{task}"
                    if st.checkbox(task, key=task_key):
                        if task_key not in st.session_state['completed']:
                            st.session_state['completed'].append(task_key)

                            # Emoji encouragement showers
                            encouragements = [
                                "✨ You're amazing! Keep it up! ✨",
                                "✅ Another task down! You're unstoppable! ✅",
                                "🌟 Great progress! Keep shining! 🌟",
                                "🔥 You're on fire! Smash the next one! 🔥",
                                "🏆 You're winning the day! Go go go! 🏆"
                            ]
                            shower_emojis = "🎉🎊👏🚀🌈⭐💪"
                            st.markdown(f"### {random.choice(encouragements)} {shower_emojis}")

                            # Display study material for the topic
                            st.write(f"📖 *Study Material*: {study_material}")

                            # Sound Effect (Browser notification)
                            components.html("""
                            <script>
                            var audio = new Audio('https://www.soundjay.com/button/beep-07.wav');
                            audio.play();
                            </script>
                            """, height=0)

                            # Animation (Confetti animation)
                            components.html("""
                            <script>
                            var confetti = document.createElement('script');
                            confetti.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.4.0/dist/confetti.browser.min.js';
                            document.body.appendChild(confetti);
                            window.addEventListener('load', function() {
                                confetti.create(document.body, { resize: true, useWorker: true })();
                            });
                            </script>
                            """, height=0)

                            # Insert the Emoji Shower here
                            emoji_shower = "🎉🎊💥✨🚀💫🔥🎯"
                            st.markdown(f"<h3 style='text-align:center;'>{emoji_shower}</h3>", unsafe_allow_html=True)

        # Progress
        completed = len(st.session_state['completed'])
        progress = completed / total_tasks if total_tasks else 0
        st.progress(progress)
        st.info(f"Progress: {completed}/{total_tasks} tasks completed ✅")

        # Chart
        chart_df = pd.DataFrame({
            'Status': ['Completed', 'Remaining'],
            'Tasks': [completed, total_tasks - completed]
        }).set_index("Status")
        st.bar_chart(chart_df)

        # Download
        plan_text = ""
        for day, day_tasks in study_plan.items():
            plan_text += f"{day}\n"
            for task_info in day_tasks:
                plan_text += f" - {task_info['task']} | Material: {task_info['study_material']}\n"
            plan_text += "\n"
        st.download_button("⬇ Download Study Plan", plan_text, file_name="study_plan.txt")

    # Pomodoro Timer
    with st.expander("⏱ Pomodoro Timer (Live)"):
        if 'timer_started' not in st.session_state:
            st.session_state.timer_started = False
        if 'start_time' not in st.session_state:
            st.session_state.start_time = None

        focus_minutes = st.slider("Select focus duration (minutes):", 1, 60, 25)

        if st.button("▶ Start Timer"):
            st.session_state.timer_started = True
            st.session_state.start_time = time.time()

        if st.session_state.timer_started and st.session_state.start_time:
            elapsed = int(time.time() - st.session_state.start_time)
            remaining = focus_minutes * 60 - elapsed
            if remaining > 0:
                mins, secs = divmod(remaining, 60)
                st.success(f"⏳ Time left: {mins:02}:{secs:02}")
                st_autorefresh(interval=1000, limit=None, key="pomodoro_refresh")
            else:
                st.session_state.timer_started = False
                st.success("✅ Time's up! Take a break!")

# -----------------------------
# Study Plan Generator Using AI (New Feature)
# -----------------------------
elif menu == "Study Plan Generator":
    st.title("🤖 AI-Generated Study Plan")

    # Get topic for AI-generated plan
    topic = st.text_input("Enter the topic or course you want to study:")
    duration = st.selectbox("Select duration:", ["1 week", "2 weeks", "1 month", "3 months", "6 months"])
    level = st.selectbox("Select your level:", ["Beginner", "Intermediate", "Advanced"])

    if st.button("Generate Comprehensive Study Plan"):
        if topic:
            try:
                # Generate prompt for Gemini
                prompt = f"""
                Create a comprehensive study plan for: {topic}
                - Duration: {duration}
                - Level: {level}
                
                The plan should include:
                1. Clear milestones and learning objectives
                2. Recommended study resources (books, websites, videos)
                3. Weekly breakdown of topics
                4. Practice exercises/projects
                5. Assessment methods
                6. Time estimates for each section
                
                Format with clear headings and bullet points.
                """
                
                # Call Gemini API
                response = model.generate_content(prompt)
                ai_plan = response.text
                
                st.markdown(f"### 📚 AI-Generated Study Plan for {topic} ({level})")
                st.markdown(ai_plan)
                
                # Add download button
                st.download_button(
                    "⬇ Download Full Study Plan",
                    ai_plan,
                    file_name=f"{topic.replace(' ', '_')}_study_plan.txt"
                )
                
            except Exception as e:
                st.error(f"Error generating study plan: {str(e)}")
        else:
            st.warning("Please enter a topic to generate a study plan.")