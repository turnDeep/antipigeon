# AntiCrow 🐦‍⬛

DiscordとAntigravityを行き来して、指示と結果を運ぶ“伝令カラス”システム。
どこからでもスマホのDiscordアプリで、自宅PCのAntigravityを遠隔操作できます。

## 特徴

*   **自動連携**: AntigravityのワークスペースごとにDiscordカテゴリとチャンネルを自動作成。
*   **自然言語対応**: 自然文の依頼を解析して即時実行。
*   **添付ファイル解析**: アップロードされたコードやテキストファイルを自動で読み込み、プロンプトの一部として使用。
*   **定期実行**: `/schedule` コマンドで定期的なタスクを設定可能。一時停止・再開にも対応。
*   **テンプレート実行**: `/templates` で登録したプロンプトを、好きなワークスペースで即時実行可能。
*   **コンテキスト継承**: 返信機能を使って会話の履歴をタスクのコンテキストとして引き継ぎ可能。
*   **セキュア**: Discord Bot TokenはOSのSecretStorage（Keyring）に暗号化して保存。

## 必要条件

*   Python 3.10+
*   Discord Bot Token
*   Antigravity (または互換性のあるAPI/モック)

## インストール

1.  リポジトリをクローンします。
2.  依存関係をインストールします:
    ```bash
    pip install -r requirements.txt
    ```

## 設定

### 1. Bot Tokenの設定 (推奨)

OSの安全な領域にTokenを保存するために、以下のスクリプトを実行してください:

```bash
python src/setup_token.py
```

### 2. 環境変数の設定 (オプション)

`.env` ファイルを作成して以下の設定を行えます:

```ini
# Bot Token (keyringが使えない場合のフォールバック)
DISCORD_TOKEN=your_token_here

# 使用許可ユーザーID (カンマ区切り)
ALLOWED_USER_IDS=123456789012345678,987654321098765432

# Antigravityのパス (オプション)
ANTIGRAVITY_PATH=/path/to/antigravity
```

## 実行

### Windows

1.  コマンドプロンプトまたはPowerShellを開きます。
2.  プロジェクトディレクトリに移動します。
3.  以下のコマンドでBotを起動します:
    ```cmd
    python src/bot.py
    ```

### Ubuntu (Linux)

1.  ターミナルを開きます。
2.  プロジェクトディレクトリに移動します。
3.  以下のコマンドでBotを起動します:
    ```bash
    python3 src/bot.py
    ```

#### 常駐化する場合 (Systemdの例)

バックグラウンドで常に実行したい場合は、Systemdサービスを作成することをお勧めします。

1.  `/etc/systemd/system/anticrow.service` を作成します:
    ```ini
    [Unit]
    Description=AntiCrow Discord Bot
    After=network.target

    [Service]
    User=your_username
    WorkingDirectory=/path/to/anticrow
    ExecStart=/path/to/anticrow/venv/bin/python3 src/bot.py
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
2.  サービスを有効化・起動します:
    ```bash
    sudo systemctl enable anticrow
    sudo systemctl start anticrow
    ```

## コマンド一覧

### 一般
*   `/models`: 利用可能なモデル一覧を表示・切替。
*   `/mode [mode]`: 実行モードの切り替え (planning / fast)。
*   `/workspaces`: ワークスペース一覧を表示。
*   `/status`: Botのステータスを表示。

### テンプレート
*   `/templates list`: テンプレート一覧を表示。
*   `/templates add [name] [content]`: テンプレートを登録。
*   `/templates remove [name]`: テンプレートを削除。
*   `/templates run [name]`: テンプレートを現在のワークスペースで即時実行。引数なしで選択UIを表示。

### スケジュール
*   `/schedule [cron] [prompt]`: 定期実行タスクの登録。
*   `/schedules`: 登録済みスケジュールの確認、削除、一時停止/再開（Pause/Resume）。

## 使い方

1.  Botを起動すると、Antigravityのワークスペースに対応したカテゴリがDiscord上に作成されます。
2.  そのカテゴリ内のチャンネルで指示を書き込むと、自動的にタスクとして実行されます。
3.  **添付ファイル**: `.py`, `.txt` などのファイルを添付すると、その内容も指示に含まれます。
4.  タスクの進捗はリアルタイムで通知されます。
5.  結果に対して返信を行うと、その内容をコンテキストとして引き継いで新たなタスクを実行できます。

## セキュリティ

*   **SSH公開なし**: PCローカル完結で動作します。
*   **ホワイトリスト制御**: `ALLOWED_USER_IDS` で許可されたユーザーのみ操作可能です。
*   **暗号化保存**: Tokenは `keyring` を使用して安全に保存されます。
