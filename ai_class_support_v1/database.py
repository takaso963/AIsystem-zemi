import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path(__file__).with_name("class_support.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lectures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                summary TEXT,
                quiz TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                lecture_title TEXT,
                question TEXT NOT NULL,
                ai_answer TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                lecture_title TEXT,
                quiz_question TEXT NOT NULL,
                student_answer TEXT NOT NULL,
                score TEXT,
                feedback TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_lecture(title: str, content: str, summary: str = "", quiz: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO lectures (title, content, summary, quiz, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, content, summary, quiz, now_text()),
        )
        conn.commit()
        return int(cur.lastrowid)


def save_question(student_name: str, lecture_title: str, question: str, ai_answer: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO questions (student_name, lecture_title, question, ai_answer, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (student_name, lecture_title, question, ai_answer, now_text()),
        )
        conn.commit()
        return int(cur.lastrowid)


def save_quiz_result(
    student_name: str,
    lecture_title: str,
    quiz_question: str,
    student_answer: str,
    score: str,
    feedback: str,
) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO quiz_results
            (student_name, lecture_title, quiz_question, student_answer, score, feedback, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (student_name, lecture_title, quiz_question, student_answer, score, feedback, now_text()),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_recent_lectures(limit: int = 30) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, title, content, summary, quiz, created_at
            FROM lectures
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_lecture_by_id(lecture_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, title, content, summary, quiz, created_at
            FROM lectures
            WHERE id = ?
            """,
            (lecture_id,),
        ).fetchone()
    return dict(row) if row else None


def get_questions(limit: int = 100) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, student_name, lecture_title, question, ai_answer, created_at
            FROM questions
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_quiz_results(limit: int = 100) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, student_name, lecture_title, quiz_question, student_answer, score, feedback, created_at
            FROM quiz_results
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def clear_all_data() -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM quiz_results")
        conn.execute("DELETE FROM questions")
        conn.execute("DELETE FROM lectures")
        conn.commit()
