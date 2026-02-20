# Antipigeon 🕊️

DiscordとAntigravityを行き来して、指示と結果を運ぶ“伝書鳩”システム。
どこからでもスマホのDiscordアプリで、自宅PCのAntigravityを遠隔操作できます。

## 特徴

*   **サンドボックス化**: Dockerコンテナ内で動作するため、ホストOS（Raspberry PiやWindows WSL）への影響を最小限に抑えます。
*   **自動連携**: AntigravityのワークスペースごとにDiscordカテゴリとチャンネルを自動作成。
*   **自然言語対応**: 自然文の依頼を解析して即時実行。
*   **添付ファイル解析**: アップロードされたコードやテキストファイルを自動で読み込み、プロンプトの一部として使用。
*   **定期実行**: `/schedule` コマンドで定期的なタスクを設定可能。一時停止・再開にも対応。
*   **テンプレート実行**: `/templates` で登録したプロンプトを、好きなワークスペースで即時実行可能。

## 必要条件

*   Docker / Docker Compose
*   Discord Bot Token
*   Google Antigravity (または互換性のあるAPIサーバー)

## インストール & 実行 (Docker)

推奨される実行方法は Docker Compose です。

1.  リポジトリをクローンします。
2.  設定ファイルを作成します:
    ```bash
    cp .env.example .env
    ```
3.  `.env` ファイルを編集し、`DISCORD_TOKEN` と `ALLOWED_USER_IDS` を設定します。
    ```ini
    DISCORD_TOKEN=your_actual_token_here
    ALLOWED_USER_IDS=123456789012345678

    # 本物のAntigravity APIを使用する場合（未設定の場合はモックモードになります）
    # ANTIGRAVITY_API_URL=http://localhost:8080/api/v1
    ```
4.  Docker Compose で起動します:
    ```bash
    docker-compose up -d
    ```

### Antigravity との連携について
Google Antigravity (Preview) がローカルサーバーとして動作している場合、そのAPIエンドポイントを `ANTIGRAVITY_API_URL` に設定することで連携可能です。
APIが公開されていない、またはCLIのみの場合は、`src/core/antigravity.py` 内の `HttpAntigravityClient` またはCLIラッパー（要実装）を環境に合わせて調整してください。
デフォルトでは「Simulation Mode（モック）」で動作し、UIやスケジューリングの挙動を確認できます。

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
*   `/templates run [name]`: テンプレートを現在のワークスペースで即時実行。

### スケジュール
*   `/schedule [cron] [prompt]`: 定期実行タスクの登録。
*   `/schedules`: 登録済みスケジュールの確認、削除、一時停止/再開。
