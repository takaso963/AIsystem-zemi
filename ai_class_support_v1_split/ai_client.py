import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini"


def _extract_output_text(data: dict) -> str:
    """OpenAI Responses APIの返答からテキストだけを取り出す。"""
    texts = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                texts.append(content.get("text", ""))
    return "\n".join(texts).strip()


def _demo_response(system_prompt: str, user_prompt: str) -> str:
    """APIキー未設定でも画面確認できるデモ回答。"""
    lower = (system_prompt + user_prompt).lower()
    if "小テスト" in system_prompt or "quiz" in lower:
        return (
            "【デモ回答：APIキー未設定】\n"
            "小テスト例\n"
            "1. 今日の講義で最も重要なキーワードを1つ答えなさい。\n"
            "2. そのキーワードの意味を自分の言葉で説明しなさい。\n"
            "3. AIを学習に使うときの注意点を1つ答えなさい。\n\n"
            "解答例\n"
            "1. 生成AI\n"
            "2. 文章や画像などを自動で作成できるAI。\n"
            "3. AIの回答をそのまま信じず、資料や先生の説明と照らし合わせる。"
        )
    if "要約" in system_prompt or "summary" in lower:
        return (
            "【デモ回答：APIキー未設定】\n"
            "この講義では、AIを教育に活用する方法について学ぶ。教師は講義資料の要約や小テスト作成にAIを使い、"
            "生徒は自分専用のAIに質問して復習できる。AIの回答には誤りがある可能性もあるため、確認しながら使うことが重要である。"
        )
    if "採点" in system_prompt:
        return "【デモ回答：APIキー未設定】\n点数：80点\n良い点：内容の方向性は合っています。\n改善点：具体例を1つ入れるとさらに良いです。"
    return (
        "【デモ回答：APIキー未設定】\n"
        "質問ありがとうございます。授業内容に合わせて、できるだけ簡単に説明します。"
        "まず重要な言葉を1つずつ確認し、具体例と一緒に理解していきましょう。"
    )


def call_ai(system_prompt: str, user_prompt: str, temperature: float = 0.4, max_output_tokens: Optional[int] = None) -> str:
    """
    OpenAI Responses APIを呼び出す。
    .env に OPENAI_API_KEY がない場合はデモ回答を返す。
    """
    if not OPENAI_API_KEY:
        return _demo_response(system_prompt, user_prompt)

    payload = {
        "model": OPENAI_MODEL,
        "instructions": system_prompt,
        "input": user_prompt,
        "temperature": temperature,
    }
    if max_output_tokens:
        payload["max_output_tokens"] = max_output_tokens

    try:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        text = _extract_output_text(data)
        if not text:
            return "AIからテキスト回答を取得できませんでした。モデル名やAPI設定を確認してください。"
        return text
    except requests.exceptions.HTTPError as e:
        detail = ""
        try:
            detail = response.json().get("error", {}).get("message", "")
        except Exception:
            detail = response.text[:500]
        return f"APIエラーが発生しました。\n{e}\n{detail}"
    except requests.exceptions.RequestException as e:
        return f"通信エラーが発生しました。インターネット接続やAPIキーを確認してください。\n{e}"
