import io
from typing import Dict, List

import pandas as pd
import streamlit as st

from ai_client import OPENAI_API_KEY, OPENAI_MODEL, call_ai
from database import (
    clear_all_data,
    get_lecture_by_id,
    get_questions,
    get_quiz_results,
    get_recent_lectures,
    init_db,
    save_lecture,
    save_question,
    save_quiz_result,
)
from prompts import (
    REVIEW_QUIZ_PROMPT,
    SCORING_PROMPT,
    STUDENT_CHAT_PROMPT,
    TEACHER_QUIZ_PROMPT,
    TEACHER_SUMMARY_PROMPT,
)

st.set_page_config(
    page_title="AI授業支援システム v1",
    page_icon="🎓",
    layout="wide",
)

init_db()


def to_csv_bytes(rows: List[Dict]) -> bytes:
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8-sig")


def lecture_selector():
    lectures = get_recent_lectures()
    if not lectures:
        return None, "講義未選択"
    options = {f"{row['title']}（{row['created_at']}）": row["id"] for row in lectures}
    selected_label = st.selectbox("講義を選択", list(options.keys()))
    selected_id = options[selected_label]
    return get_lecture_by_id(selected_id), selected_label


def show_api_status():
    if OPENAI_API_KEY:
        st.sidebar.success(f"API接続モード：{OPENAI_MODEL}")
    else:
        st.sidebar.warning("APIキー未設定：デモ回答モード")
        st.sidebar.caption(".env に OPENAI_API_KEY を入れるとAI回答になります。")


def teacher_page():
    st.header("教師用ページ")
    st.write("講義資料や授業メモを入力して、要約・小テストを作成します。")

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        title = st.text_input("講義タイトル", value="生成AIと教育")
        content = st.text_area(
            "講義内容・資料テキスト",
            height=350,
            placeholder="ここに講義資料、授業メモ、スライドの内容などを貼り付けます。",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            summary_btn = st.button("講義を要約する", use_container_width=True)
        with col_b:
            quiz_btn = st.button("小テスト作成", use_container_width=True)
        with col_c:
            save_btn = st.button("保存", use_container_width=True)

        if "summary" not in st.session_state:
            st.session_state.summary = ""
        if "quiz" not in st.session_state:
            st.session_state.quiz = ""

        if summary_btn:
            if not content.strip():
                st.error("講義内容を入力してください。")
            else:
                with st.spinner("AIが要約しています..."):
                    st.session_state.summary = call_ai(
                        TEACHER_SUMMARY_PROMPT,
                        f"講義タイトル：{title}\n\n講義内容：\n{content}",
                    )

        if quiz_btn:
            if not content.strip():
                st.error("講義内容を入力してください。")
            else:
                with st.spinner("AIが小テストを作成しています..."):
                    st.session_state.quiz = call_ai(
                        TEACHER_QUIZ_PROMPT,
                        f"講義タイトル：{title}\n\n講義内容：\n{content}",
                    )

        if save_btn:
            if not title.strip() or not content.strip():
                st.error("講義タイトルと講義内容を入力してください。")
            else:
                lecture_id = save_lecture(title, content, st.session_state.summary, st.session_state.quiz)
                st.success(f"保存しました。講義ID：{lecture_id}")

    with col_right:
        st.subheader("要約結果")
        st.text_area("summary", value=st.session_state.get("summary", ""), height=250, label_visibility="collapsed")

        st.subheader("小テスト")
        st.text_area("quiz", value=st.session_state.get("quiz", ""), height=300, label_visibility="collapsed")

    st.divider()
    st.subheader("生徒からの最近の質問")
    questions = get_questions(limit=10)
    if questions:
        for q in questions:
            with st.expander(f"{q['created_at']} / {q['student_name']} / {q['lecture_title'] or '講義未選択'}"):
                st.markdown("**質問**")
                st.write(q["question"])
                st.markdown("**AI回答**")
                st.write(q["ai_answer"])
    else:
        st.info("まだ質問履歴はありません。")


def student_page():
    st.header("生徒用ページ")
    st.write("授業内容についてAIに質問したり、復習問題を作ったりできます。")

    if "chat_log" not in st.session_state:
        st.session_state.chat_log = []

    col_left, col_right = st.columns([1, 1])

    with col_left:
        student_name = st.text_input("名前", value="学生A")
        lecture, selected_label = lecture_selector()

        lecture_title = lecture["title"] if lecture else "講義未選択"
        lecture_context = ""
        if lecture:
            with st.expander("選択中の講義内容を確認"):
                st.markdown("**要約**")
                st.write(lecture.get("summary") or "要約は未作成です。")
                st.markdown("**講義本文**")
                st.write(lecture.get("content") or "")
            lecture_context = (
                f"講義タイトル：{lecture['title']}\n"
                f"講義要約：{lecture.get('summary') or ''}\n"
                f"講義内容：{lecture.get('content') or ''}"
            )
        else:
            st.info("教師用ページで講義を保存すると、ここで選択できます。")

        question = st.text_area(
            "AIに質問する内容",
            height=180,
            placeholder="例：今日の授業の機械学習がよくわかりません。簡単に説明してください。",
        )
        ask_btn = st.button("AIに質問する", use_container_width=True)

        if ask_btn:
            if not question.strip():
                st.error("質問内容を入力してください。")
            else:
                user_prompt = f"{lecture_context}\n\n学生名：{student_name}\n質問：{question}"
                with st.spinner("AIが回答しています..."):
                    answer = call_ai(STUDENT_CHAT_PROMPT, user_prompt)
                save_question(student_name, lecture_title, question, answer)
                st.session_state.chat_log.append({"q": question, "a": answer})
                st.success("質問履歴に保存しました。")

        review_btn = st.button("この講義の復習問題を作る", use_container_width=True)
        if review_btn:
            if not lecture_context:
                st.error("講義を選択してください。")
            else:
                with st.spinner("復習問題を作成しています..."):
                    review_quiz = call_ai(REVIEW_QUIZ_PROMPT, lecture_context)
                st.session_state.review_quiz = review_quiz

    with col_right:
        st.subheader("AIチャット結果")
        if st.session_state.chat_log:
            for item in reversed(st.session_state.chat_log[-10:]):
                with st.chat_message("user"):
                    st.write(item["q"])
                with st.chat_message("assistant"):
                    st.write(item["a"])
        else:
            st.info("まだこの画面でのチャットはありません。")

        st.subheader("復習問題")
        st.text_area(
            "review_quiz",
            value=st.session_state.get("review_quiz", ""),
            height=280,
            label_visibility="collapsed",
        )

    st.divider()
    st.subheader("復習問題の自己採点")
    with st.form("score_form"):
        quiz_question = st.text_area("問題文", height=120)
        student_answer = st.text_area("自分の回答", height=120)
        submitted = st.form_submit_button("AIに採点してもらう")

    if submitted:
        if not quiz_question.strip() or not student_answer.strip():
            st.error("問題文と回答を入力してください。")
        else:
            scoring_input = (
                f"講義タイトル：{lecture_title}\n"
                f"問題：{quiz_question}\n"
                f"学生の回答：{student_answer}"
            )
            with st.spinner("採点しています..."):
                feedback = call_ai(SCORING_PROMPT, scoring_input)
            save_quiz_result(student_name, lecture_title, quiz_question, student_answer, "AI採点", feedback)
            st.markdown("**採点結果**")
            st.write(feedback)


def history_page():
    st.header("質問履歴・保存データ")

    tab1, tab2, tab3 = st.tabs(["質問履歴", "講義一覧", "小テスト結果"])

    with tab1:
        rows = get_questions(limit=500)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "質問履歴CSVをダウンロード",
                data=to_csv_bytes(rows),
                file_name="questions.csv",
                mime="text/csv",
            )
        else:
            st.info("質問履歴はありません。")

    with tab2:
        rows = get_recent_lectures(limit=500)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df[["id", "title", "created_at", "summary", "quiz"]], use_container_width=True)
            st.download_button(
                "講義一覧CSVをダウンロード",
                data=to_csv_bytes(rows),
                file_name="lectures.csv",
                mime="text/csv",
            )
        else:
            st.info("保存された講義はありません。")

    with tab3:
        rows = get_quiz_results(limit=500)
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "小テスト結果CSVをダウンロード",
                data=to_csv_bytes(rows),
                file_name="quiz_results.csv",
                mime="text/csv",
            )
        else:
            st.info("小テスト結果はありません。")

    st.divider()
    with st.expander("危険操作：全データ削除"):
        st.warning("保存された講義・質問履歴・小テスト結果をすべて削除します。")
        confirm = st.checkbox("削除することを理解しました")
        if st.button("全データ削除", disabled=not confirm):
            clear_all_data()
            st.success("全データを削除しました。ページを再読み込みしてください。")


st.title("🎓 AI授業支援システム v1")
st.caption("教師用ページ / 生徒用ページ / AIチャット / 講義要約 / 小テスト作成 / 質問履歴保存")

show_api_status()
page = st.sidebar.radio(
    "メニュー",
    ["教師用ページ", "生徒用ページ", "質問履歴・保存データ"],
)

st.sidebar.divider()
st.sidebar.markdown("### 使い方")
st.sidebar.write("1. 教師用ページで講義内容を入力")
st.sidebar.write("2. 要約・小テストを作成")
st.sidebar.write("3. 保存")
st.sidebar.write("4. 生徒用ページで質問")
st.sidebar.write("5. 履歴ページで確認")

if page == "教師用ページ":
    teacher_page()
elif page == "生徒用ページ":
    student_page()
else:
    history_page()
