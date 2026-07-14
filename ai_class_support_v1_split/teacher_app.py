from typing import Dict, List

import pandas as pd
import streamlit as st

from ai_client import OPENAI_API_KEY, OPENAI_MODEL, call_ai
from database import (
    clear_all_data,
    get_questions,
    get_quiz_results,
    get_recent_lectures,
    init_db,
    save_lecture,
)
from prompts import TEACHER_QUIZ_PROMPT, TEACHER_SUMMARY_PROMPT
from document_loader import extract_text_from_file

st.set_page_config(
    page_title="教師用 AI授業支援システム",
    page_icon="👨‍🏫",
    layout="wide",
)

init_db()

MAX_LECTURE_TEXT_CHARS = 60000


def to_csv_bytes(rows: List[Dict]) -> bytes:
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8-sig")


def show_api_status() -> None:
    if OPENAI_API_KEY:
        st.sidebar.success(f"API接続モード：{OPENAI_MODEL}")
    else:
        st.sidebar.warning("APIキー未設定：デモ回答モード")
        st.sidebar.caption(".env に OPENAI_API_KEY を入れるとAI回答になります。")


def teacher_create_page() -> None:
    st.header("教師用ページ")
    st.write("講義資料PDFなどをアップロード、またはテキストを入力して、要約・小テストを作成します。")

    if "lecture_title" not in st.session_state:
        st.session_state.lecture_title = "生成AIと教育"
    if "lecture_content" not in st.session_state:
        st.session_state.lecture_content = ""
    if "summary" not in st.session_state:
        st.session_state.summary = ""
    if "quiz" not in st.session_state:
        st.session_state.quiz = ""

    st.subheader("1. 講義資料をアップロード")
    uploaded_files = st.file_uploader(
        "PDF、Word、PowerPoint、テキストを追加できます",
        type=["pdf", "docx", "pptx", "txt", "md", "csv"],
        accept_multiple_files=True,
        help="画像だけのPDFは文字を読み取れない場合があります。その場合はOCRが必要です。",
    )

    col_upload_a, col_upload_b = st.columns([1, 1])
    with col_upload_a:
        read_upload_btn = st.button("アップロード資料を講義内容に反映", use_container_width=True)
    with col_upload_b:
        clear_content_btn = st.button("講義内容をクリア", use_container_width=True)

    if clear_content_btn:
        st.session_state.lecture_content = ""
        st.session_state.summary = ""
        st.session_state.quiz = ""
        st.success("講義内容をクリアしました。")

    if read_upload_btn:
        if not uploaded_files:
            st.error("先にPDFなどの講義資料をアップロードしてください。")
        else:
            extracted_blocks = []
            for uploaded_file in uploaded_files:
                file_text, message = extract_text_from_file(uploaded_file.name, uploaded_file.getvalue())
                if file_text:
                    extracted_blocks.append(f"===== {uploaded_file.name} =====\n{file_text}")
                    st.success(f"{uploaded_file.name}: {message}")
                else:
                    st.warning(f"{uploaded_file.name}: {message}")

            if extracted_blocks:
                combined = "\n\n".join(extracted_blocks)
                if len(combined) > MAX_LECTURE_TEXT_CHARS:
                    combined = (
                        combined[:MAX_LECTURE_TEXT_CHARS]
                        + "\n\n【注意】資料が長いため、最初の一部だけを読み込みました。必要なページだけに分けてください。"
                    )
                    st.warning("資料が長いため、一部だけを読み込みました。")

                # すでに手入力した内容がある場合は、下に追加する
                if st.session_state.lecture_content.strip():
                    st.session_state.lecture_content += "\n\n" + combined
                else:
                    st.session_state.lecture_content = combined

                # タイトルが初期値のままなら、最初のファイル名をタイトルにする
                if st.session_state.lecture_title in {"", "生成AIと教育"}:
                    st.session_state.lecture_title = uploaded_files[0].name.rsplit(".", 1)[0]

                st.info("抽出した内容を下の『講義内容・資料テキスト』に入れました。必要に応じて修正してから要約・保存してください。")

    st.divider()
    st.subheader("2. 要約・小テスト作成")

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        title = st.text_input("講義タイトル", key="lecture_title")
        content = st.text_area(
            "講義内容・資料テキスト",
            height=350,
            key="lecture_content",
            placeholder="ここに講義資料、授業メモ、スライドの内容などを貼り付けます。PDF等をアップロードすると自動で入ります。",
        )

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            summary_btn = st.button("講義を要約する", use_container_width=True)
        with col_b:
            quiz_btn = st.button("小テスト作成", use_container_width=True)
        with col_c:
            save_btn = st.button("保存", use_container_width=True)

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
                st.info("保存した講義は、生徒用ページから選択できます。")

    with col_right:
        st.subheader("要約結果")
        st.text_area("summary", value=st.session_state.get("summary", ""), height=250, label_visibility="collapsed")

        st.subheader("小テスト")
        st.text_area("quiz", value=st.session_state.get("quiz", ""), height=300, label_visibility="collapsed")


def teacher_questions_page() -> None:
    st.header("生徒からの質問確認")
    questions = get_questions(limit=300)
    if not questions:
        st.info("まだ質問履歴はありません。")
        return

    df = pd.DataFrame(questions)
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "質問履歴CSVをダウンロード",
        data=to_csv_bytes(questions),
        file_name="questions.csv",
        mime="text/csv",
    )

    st.subheader("質問カード表示")
    for q in questions[:20]:
        with st.expander(f"{q['created_at']} / {q['student_name']} / {q['lecture_title'] or '講義未選択'}"):
            st.markdown("**質問**")
            st.write(q["question"])
            st.markdown("**AI回答**")
            st.write(q["ai_answer"])


def teacher_data_page() -> None:
    st.header("保存データ確認")
    tab1, tab2 = st.tabs(["講義一覧", "小テスト結果"])

    with tab1:
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

    with tab2:
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


st.title("👨‍🏫 教師用 AI授業支援システム")
st.caption("講義要約 / 小テスト作成 / 生徒の質問確認 / 学習ログ確認")

show_api_status()
page = st.sidebar.radio(
    "教師用メニュー",
    ["講義作成", "生徒の質問確認", "保存データ確認"],
)

st.sidebar.divider()
st.sidebar.markdown("### 教師用の流れ")
st.sidebar.write("1. 講義作成で資料を入力")
st.sidebar.write("2. 要約・小テストを作成")
st.sidebar.write("3. 保存")
st.sidebar.write("4. 生徒の質問確認で履歴を見る")

if page == "講義作成":
    teacher_create_page()
elif page == "生徒の質問確認":
    teacher_questions_page()
else:
    teacher_data_page()
