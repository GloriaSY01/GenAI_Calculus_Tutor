"""Thin HTTP client shared by the student and teacher Streamlit pages."""
import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


# --------------------------------------------------------------------------- #
# Practice / tutor (reused by the student page)
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=60)
def fetch_topics():
    r = requests.get(f"{BACKEND_URL}/topics", timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def fetch_learning_path():
    r = requests.get(f"{BACKEND_URL}/learning-path", timeout=15)
    r.raise_for_status()
    return r.json()


def generate_question(qtype, topic, difficulty):
    r = requests.post(f"{BACKEND_URL}/generate",
                      json={"type": qtype, "topic": topic, "difficulty": difficulty},
                      timeout=60)
    r.raise_for_status()
    return r.json()


def grade_answer(payload):
    r = requests.post(f"{BACKEND_URL}/grade", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def start_session(problem_id, condition, student_id):
    r = requests.post(f"{BACKEND_URL}/session/start",
                      json={"problem_id": problem_id, "condition": condition,
                            "student_id": student_id}, timeout=30)
    r.raise_for_status()
    return r.json()


def send_message(session_id, text):
    r = requests.post(f"{BACKEND_URL}/session/{session_id}/message",
                      json={"text": text}, timeout=60)
    r.raise_for_status()
    return r.json()


# --------------------------------------------------------------------------- #
# Teacher analytics + assignments
# --------------------------------------------------------------------------- #
def fetch_class_analytics():
    r = requests.get(f"{BACKEND_URL}/analytics/class", timeout=30)
    r.raise_for_status()
    return r.json()


def ask_analytics(question):
    r = requests.post(f"{BACKEND_URL}/analytics/ask",
                      json={"question": question}, timeout=60)
    r.raise_for_status()
    return r.json()


def fetch_assignments():
    r = requests.get(f"{BACKEND_URL}/assignments", timeout=15)
    r.raise_for_status()
    return r.json()


def create_assignment(payload):
    r = requests.post(f"{BACKEND_URL}/assignments", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


def delete_assignment(assignment_id):
    r = requests.delete(f"{BACKEND_URL}/assignments/{assignment_id}", timeout=15)
    r.raise_for_status()
    return r.json()
