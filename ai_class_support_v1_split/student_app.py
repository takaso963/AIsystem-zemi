import pandas as pd
import streamlit as st

from ai_client import OPENAI_API_KEY, OPENAI_MODEL, call_ai
from database import (
    get_lecture_by_id,
    get_recent_lectures,
    init_db,
    save_question,
    save_quiz_result,
)
from prompts import REVIEW_QUIZ_PROMPT, SCORING_PROMPT, STUDENT_CHAT_PROMPT

st.set_page_config(
    page_title="生徒用 AI学習支援システム",
    page_icon="🎓",
    layout="wide",
)

init_db()


def show_api_status() -> None:
    if OPENAI_API_KEY:
        st.sidebar.success(f"API接続モード：{OPENAI_MODEL}")
    else:
        st.sidebar.warning("APIキー未設定：デモ回答モード")
        st.sidebar.caption(".env に OPENAI_API_KEY を入れるとAI回答になります。")


def lecture_selector():
    lectures = get_recent_lectures()
    if not lectures:
        return None, "講義未選択"
    options = {f"{row['title']}（{row['created_at']}）": row["id"] for row in lectures}
    selected_label = st.selectbox("講義を選択", list(options.keys()))
    selected_id = options[selected_label]
    return get_lecture_by_id(selected_id), selected_label


def student_chat_page() -> None:
    st.header("AIチャット")
    st.write("授業内容についてAIに質問できます。")

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
            st.info("まだ講義がありません。先生が教師用ページで講義を保存すると選べます。")

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


def review_page() -> None:
    st.header("復習問題")
    st.write("先生が保存した講義をもとに、AIが復習問題を作ります。")

    student_name = st.text_input("名前", value="学生A")
    lecture, selected_label = lecture_selector()

    lecture_title = lecture["title"] if lecture else "講義未選択"
    lecture_context = ""
    if lecture:
        lecture_context = (
            f"講義タイトル：{lecture['title']}\n"
            f"講義要約：{lecture.get('summary') or ''}\n"
            f"講義内容：{lecture.get('content') or ''}"
        )
        with st.expander("選択中の講義要約"):
            st.write(lecture.get("summary") or "要約は未作成です。")
    else:
        st.info("まだ講義がありません。先生が教師用ページで講義を保存すると選べます。")

    if "review_quiz" not in st.session_state:
        st.session_state.review_quiz = ""

    if st.button("この講義の復習問題を作る", use_container_width=True):
        if not lecture_context:
            st.error("講義を選択してください。")
        else:
            with st.spinner("復習問題を作成しています..."):
                st.session_state.review_quiz = call_ai(REVIEW_QUIZ_PROMPT, lecture_context)

    st.subheader("AIが作成した復習問題")
    st.text_area(
        "review_quiz",
        value=st.session_state.review_quiz,
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


def my_log_page() -> None:
    st.header("自分の学習メモ")
    st.write("このページでは、今の画面で質問した内容を確認できます。")

    chat_log = st.session_state.get("chat_log", [])
    if not chat_log:
        st.info("まだこの画面での質問はありません。")
        return

    rows = []
    for i, item in enumerate(chat_log, start=1):
        rows.append({"番号": i, "質問": item["q"], "AI回答": item["a"]})
    st.dataframe(pd.DataFrame(rows), use_container_width=True)


st.title("🎓 生徒用 AI学習支援システム")
st.caption("AIチャット / 復習問題 / 自己採点 / 質問履歴保存")

show_api_status()
page = st.sidebar.radio(
    "生徒用メニュー",
    ["AIチャット", "復習問題", "自分の学習メモ"],
)

st.sidebar.divider()
st.sidebar.markdown("### 生徒用の流れ")
st.sidebar.write("1. 講義を選択")
st.sidebar.write("2. わからないところをAIに質問")
st.sidebar.write("3. 復習問題を作る")
st.sidebar.write("4. 自分の回答をAI採点")

if page == "AIチャット":
    student_chat_page()
elif page == "復習問題":
    review_page()
else:
    my_log_page()
