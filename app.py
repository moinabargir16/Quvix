import streamlit as st
import pandas as pd

from adaptive import update_difficulty, get_next_question
from classifier import predict_level
from database import (
    create_table,
    save_result,
    get_history,
    register_user,
    get_user_stats
)
from performance import show_performance_chart


# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="Quvix",
    page_icon="🎯",
    layout="wide"
)

# ---------------- DATABASE ----------------

create_table()

# ---------------- SUBJECTS ----------------

SUBJECTS = [
    "Programming",
    "Artificial Intelligence",
    "Mathematics",
    "General Knowledge",
    "Science",
    "English",
    "Computer Science",
    "Logical Reasoning",
    "Business and Economics"
]

# ---------------- CUSTOM DESIGN ----------------

st.markdown("""
<style>

.stApp {
    background-color: #0B0B18;
    color: white;
}

h1, h2, h3 {
    color: #B69CFF;
}

div.stButton > button {
    background-color: #7047EB;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
}

div.stButton > button:hover {
    background-color: #936EFF;
    color: white;
}

</style>
""", unsafe_allow_html=True)


# ---------------- LOAD QUESTIONS ----------------

@st.cache_data
def load_questions():

    df = pd.read_csv("questions.csv")

    required = [
        "id", "topic", "difficulty", "question",
        "option1", "option2", "option3", "option4",
        "answer"
    ]

    if not all(column in df.columns for column in required):
        raise ValueError("The question CSV is missing required columns.")

    df["id"] = pd.to_numeric(df["id"], errors="raise")

    if df["id"].duplicated().any():
        raise ValueError("Question IDs must be unique.")

    if not df["difficulty"].isin(
        ["Easy", "Medium", "Hard"]
    ).all():
        raise ValueError("Invalid difficulty in question bank.")

    for _, row in df.iterrows():
        options = [
            row["option1"], row["option2"],
            row["option3"], row["option4"]
        ]

        if row["answer"] not in options:
            raise ValueError(
                f"Answer does not match an option for question {row['id']}."
            )

    return df


try:
    questions = load_questions()
except Exception as error:
    st.error(f"Could not load question bank: {error}")
    st.stop()


# ---------------- SESSION STATE ----------------

defaults = {
    "username": "",
    "started": False,
    "finished": False,
    "asked_ids": [],
    "score": 0,
    "correct_count": 0,
    "question_number": 0,
    "difficulty": "Easy",
    "streak": 0,
    "current_question": None,
    "topic_scope": "All Subjects",
    "mode": "Mixed Subjects",
    "total_questions": 10,
    "quiz_saved": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------- QUESTION SELECTION ----------------

def select_question():

    return get_next_question(
        questions,
        st.session_state.topic_scope,
        st.session_state.difficulty,
        st.session_state.asked_ids
    )


def start_quiz():

    st.session_state.asked_ids = []
    st.session_state.score = 0
    st.session_state.correct_count = 0
    st.session_state.question_number = 0
    st.session_state.streak = 0
    st.session_state.difficulty = "Easy"
    st.session_state.finished = False
    st.session_state.quiz_saved = False

    if st.session_state.mode == "Random Questions":
        st.session_state.difficulty = "Medium"

    st.session_state.current_question = select_question()

    st.session_state.started = (
        st.session_state.current_question is not None
    )


# ---------------- HEADER ----------------

st.title("🎯 QUVIX")
st.subheader("Every Question Moves You Forward.")
st.caption("AI-POWERED ADAPTIVE LEARNING")

st.divider()


# ---------------- SIDEBAR ----------------

st.sidebar.title("QUVIX MENU")

page = st.sidebar.radio(
    "Navigate",
    ["Home", "Dashboard", "Quiz History"]
)
# ---------------- USER PROFILE ----------------

st.sidebar.divider()
st.sidebar.subheader("Your Profile")

with st.sidebar.form("profile_form"):

    profile_name = st.text_input(
        "Enter your username",
        value=st.session_state.username,
        placeholder="Your unique username"
    )

    load_profile = st.form_submit_button("Load Profile")

    if load_profile:

        if not profile_name.strip():
            st.sidebar.warning("Please enter a username.")

        else:
            user_id = register_user(profile_name)

            if user_id is not None:
                st.session_state.username = profile_name.strip()

                # Reset an unfinished quiz when switching profiles
                st.session_state.started = False
                st.session_state.finished = False
                st.session_state.current_question = None

                st.rerun()


# ---------------- HOME ----------------

if page == "Home":

    st.header("Welcome to Quvix!")

    name = st.text_input(
        "Enter your display name",
        value=st.session_state.username
    )

    mode = st.selectbox(
        "Choose Quiz Mode",
        [
            "Individual Subject",
            "Mixed Subjects",
            "Random Questions"
        ]
    )

    subject = st.selectbox(
        "Choose Subject",
        SUBJECTS
    )

    total = st.slider(
        "Number of Questions",
        min_value=3,
        max_value=10,
        value=5
    )

    st.caption(
        "Individual Subject uses your selected subject. "
        "Mixed Subjects draws across subjects. "
        "Random Questions also randomizes the starting difficulty."
    )

    if st.button("Start Quiz"):

        if not name.strip():
            st.warning("Please enter your display name.")

        elif mode == "Individual Subject" and subject not in SUBJECTS:
            st.warning("Please select a valid subject.")

        else:

            st.session_state.username = name.strip()

            # Register or retrieve the user
            register_user(st.session_state.username)

            st.session_state.mode = mode
            st.session_state.topic_scope = (
                subject if mode == "Individual Subject"
                else "All Subjects"
            )
            st.session_state.total_questions = total

            start_quiz()

            if st.session_state.started:
                st.rerun()
            else:
                st.warning("No questions are available for this selection.")


    # ---------------- ACTIVE QUIZ ----------------

    if st.session_state.started and not st.session_state.finished:

        q = st.session_state.current_question

        st.divider()

        st.subheader(
            f"Question {st.session_state.question_number + 1} "
            f"of {st.session_state.total_questions}"
        )

        st.progress(
            st.session_state.question_number /
            st.session_state.total_questions
        )

        st.caption(
            f"Subject: {q['topic']} | "
            f"Difficulty: {st.session_state.difficulty}"
        )

        st.markdown(f"### {q['question']}")

        options = [
            q["option1"], q["option2"],
            q["option3"], q["option4"]
        ]

        selected = st.radio(
            "Select your answer",
            options,
            key=f"answer_{int(q['id'])}"
        )

        if st.button("Submit Answer"):

            correct = selected == q["answer"]

            if correct:
                st.session_state.score += 1
                st.session_state.correct_count += 1
                st.success("Correct answer!")
            else:
                st.error(
                    f"Incorrect. Correct answer: {q['answer']}"
                )

            new_difficulty, new_streak = update_difficulty(
                st.session_state.difficulty,
                correct,
                st.session_state.streak
            )

            st.session_state.difficulty = new_difficulty
            st.session_state.streak = new_streak

            st.session_state.asked_ids.append(int(q["id"]))
            st.session_state.question_number += 1

            if (
                st.session_state.question_number
                >= st.session_state.total_questions
            ):
                st.session_state.finished = True
                st.session_state.started = False

            else:
                next_q = select_question()

                if next_q is None:
                    st.session_state.finished = True
                    st.session_state.started = False
                else:
                    st.session_state.current_question = next_q

            st.rerun()


    # ---------------- RESULTS ----------------

    if st.session_state.finished:

        st.divider()
        st.header("Quiz Completed! 🎉")

        score = st.session_state.score
        total = st.session_state.question_number

        accuracy = (
            (score / total) * 100 if total else 0
        )

        st.metric("Your Score", f"{score}/{total}")
        st.metric("Accuracy", f"{accuracy:.1f}%")

        level = predict_level(
            accuracy,
            total,
            score
        )

        st.subheader(f"Performance Level: {level}")

        if not st.session_state.quiz_saved:

            save_result(
                st.session_state.username,
                st.session_state.topic_scope,
                score,
                total,
                accuracy,
                level
            )

            st.session_state.quiz_saved = True

        if st.button("Start Another Quiz"):

            st.session_state.started = False
            st.session_state.finished = False
            st.rerun()


# ---------------- DASHBOARD ----------------

elif page == "Dashboard":

    st.header("📊 Performance Dashboard")

    if not st.session_state.username:
        st.info("Complete a quiz first to view your dashboard.")

    else:

        history = get_history(st.session_state.username)

        if not history:
            st.info("No quiz history available yet.")

        else:

            df = pd.DataFrame(
                history,
                columns=[
                    "Subject", "Score", "Total",
                    "Accuracy", "Level", "Date"
                ]
            )

            st.metric("Total Quizzes", len(df))

            stats = get_user_stats(st.session_state.username)

            total_quizzes = stats[0]
            total_correct = stats[1]
            total_questions = stats[2]
            average_accuracy = stats[3]

            col1, col2, col3 = st.columns(3)

            col1.metric("Total Quizzes", total_quizzes)

            col2.metric(
            "Overall Accuracy",
            f"{average_accuracy:.1f}%"
            )

            col3.metric(
            "Questions Attempted",
            total_questions
            )       

            fig = show_performance_chart(history)

            if fig is not None:
                st.pyplot(fig)


# ---------------- HISTORY ----------------

elif page == "Quiz History":

    st.header("📚 Quiz History")

    if not st.session_state.username:
        st.info("Enter your display name and complete a quiz first.")

    else:

        history = get_history(st.session_state.username)

        if history:

            df = pd.DataFrame(
                history,
                columns=[
                    "Subject", "Score", "Total",
                    "Accuracy", "Level", "Date"
                ]
            )

            st.dataframe(
                df,
                use_container_width=True
            )

        else:
            st.info("No previous quizzes found.")