# AI授業支援システム v1 分割版

教師用ページと生徒用ページを、別々のアプリとして起動できるように分けた版です。

## できること

### 教師用アプリ

- 講義内容を入力
- 講義資料PDF、Word、PowerPoint、テキストをアップロード
- AIで講義要約
- AIで小テスト作成
- 講義内容・要約・小テストをSQLiteに保存
- 生徒からの質問を確認
- 質問履歴、講義一覧、小テスト結果をCSVでダウンロード

### 生徒用アプリ

- 保存された講義を選択
- AIに質問
- 復習問題を作成
- 自分の回答をAI採点
- 質問履歴をSQLiteに保存

## フォルダ構成

```text
ai_class_support_v1_split/
├─ teacher_app.py              # 教師用アプリ
├─ student_app.py              # 生徒用アプリ
├─ app.py                      # 旧版：教師用・生徒用を1つにまとめたアプリ
├─ ai_client.py                # OpenAI API呼び出し
├─ database.py                 # SQLite保存処理
├─ prompts.py                  # AIに渡す指示文
├─ requirements.txt            # 必要ライブラリ
├─ .env.example                # APIキー設定例
├─ sample_lecture.txt          # 動作確認用の講義例
├─ setup_and_run_teacher.bat   # 初回用：教師用をセットアップして起動
├─ setup_and_run_student.bat   # 初回用：生徒用をセットアップして起動
├─ run_teacher.bat             # 2回目以降：教師用を起動
└─ run_student.bat             # 2回目以降：生徒用を起動
```

## 最初の準備

1. ZIPを解凍する
2. `ai_class_support_v1_split` フォルダを開く
3. `.env.example` をコピーして `.env` という名前に変更する
4. `.env` を開き、`OPENAI_API_KEY=` の右側にAPIキーを入れる

APIキーを入れなくても、デモ回答モードで画面確認できます。

## 起動方法：ダブルクリック

### 初回

教師用を開く場合：

```text
setup_and_run_teacher.bat
```

生徒用を開く場合：

```text
setup_and_run_student.bat
```

### 2回目以降

教師用を開く場合：

```text
run_teacher.bat
```

生徒用を開く場合：

```text
run_student.bat
```

## 起動方法：cmdで開く場合

### 教師用

```cmd
cd "C:\Users\souta\OneDrive\デスクトップ\授業\ai_class_support_v1_split"
"C:\Users\souta\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run teacher_app.py --server.port 8501
```

教師用URL：

```text
http://localhost:8501
```

### 生徒用

```cmd
cd "C:\Users\souta\OneDrive\デスクトップ\授業\ai_class_support_v1_split"
"C:\Users\souta\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run student_app.py --server.port 8502
```

生徒用URL：

```text
http://localhost:8502
```

## 動作確認の流れ

1. 教師用アプリを開く
2. PDFなどの講義資料をアップロードして「アップロード資料を講義内容に反映」を押す
   または、`sample_lecture.txt` の中身を講義内容に貼り付ける
3. 「講義を要約する」を押す
4. 「小テスト作成」を押す
5. 「保存」を押す
6. 生徒用アプリを開く
7. 保存した講義を選択して質問する
8. 教師用アプリの「生徒の質問確認」で質問履歴を確認する

## 注意

- 教師用と生徒用は、同じ `class_support.db` を使います。
- そのため、教師用で保存した講義が生徒用に表示されます。
- v1は授業・研究発表用のプロトタイプです。
- 本格運用ではログイン機能、権限管理、個人情報保護、利用規約、管理者画面が必要です。
- PDF、Word、PowerPoint、テキストの読み込みに対応しています。画像だけのPDFは文字抽出できない場合があります。
- AIの回答には誤りが含まれる可能性があるため、教師が内容を確認してください。
