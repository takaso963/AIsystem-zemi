# AI授業支援システム v1

教師用ページ、生徒用ページ、AIチャット、講義要約、小テスト作成、質問履歴保存を備えたプロトタイプです。

## できること

- 教師用ページ
  - 講義内容を入力
  - AIで講義要約
  - AIで小テスト作成
  - 講義内容・要約・小テストをSQLiteに保存
  - 生徒からの質問を確認

- 生徒用ページ
  - 保存された講義を選択
  - AIに質問
  - 復習問題を作成
  - 自分の回答をAI採点
  - 質問履歴をSQLiteに保存

- 質問履歴・保存データ
  - 質問履歴を一覧表示
  - 講義一覧を表示
  - 小テスト結果を表示
  - CSVダウンロード

## フォルダ構成

```text
ai_class_support_v1/
├─ app.py                # Streamlit画面
├─ ai_client.py          # OpenAI API呼び出し
├─ database.py           # SQLite保存処理
├─ prompts.py            # AIに渡す指示文
├─ requirements.txt      # 必要ライブラリ
├─ .env.example          # APIキー設定例
├─ sample_lecture.txt    # 動作確認用の講義例
├─ setup_and_run.bat     # Windows用：初回セットアップ＋起動
└─ run_app.bat           # Windows用：2回目以降の起動
```

## 起動方法：Windowsで簡単に動かす場合

1. ZIPを解凍する
2. `ai_class_support_v1` フォルダを開く
3. `.env.example` をコピーして `.env` という名前に変更する
4. `.env` を開き、`OPENAI_API_KEY=` の右側にAPIキーを入れる
5. `setup_and_run.bat` をダブルクリックする

APIキーを入れなくてもデモ回答モードで画面確認できます。

## 起動方法：VS Codeのターミナルで動かす場合

```bash
cd ai_class_support_v1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Macの場合は仮想環境の有効化だけ次のようにします。

```bash
source .venv/bin/activate
```

## .env の例

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4.1-mini
```

## 動作確認の流れ

1. 教師用ページを開く
2. `sample_lecture.txt` の中身を講義内容に貼り付ける
3. 「講義を要約する」を押す
4. 「小テスト作成」を押す
5. 「保存」を押す
6. 生徒用ページを開く
7. 保存した講義を選択して質問する
8. 質問履歴・保存データで履歴を確認する

## 注意

- 本格運用ではログイン機能、権限管理、個人情報保護、利用規約、管理者画面が必要です。
- v1は授業・研究発表用のプロトタイプです。
- AIの回答には誤りが含まれる可能性があるため、教師が内容を確認してください。
