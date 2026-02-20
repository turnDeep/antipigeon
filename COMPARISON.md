# Antigravity Discord Bot リポジトリ比較レポート

## 1. 概要
本レポートは、現在のリポジトリ（以下、**Python版**）と、[Sunwood-ai-labs/antigravity-discord-bot](https://github.com/Sunwood-ai-labs/antigravity-discord-bot)（以下、**Node.js版**）のシステムアーキテクチャおよび機能の比較結果をまとめたものです。

### 結論要約
*   **Python版 (本リポジトリ):** **API通信**を前提とした堅牢な設計。スケジュール実行やテンプレート管理など、ボットとしての付加価値機能が充実しています。将来的にAntigravityがAPIを提供する場合、あるいはMock環境での開発に適しています。
*   **Node.js版 (比較対象):** **CDP (Chrome DevTools Protocol)** を用いたGUI操作自動化ツール。APIが存在しない現行のAntigravity (VS Codeフォーク) を外部から無理やり操作するためのハック的なアプローチを採用しています。

---

## 2. アーキテクチャの比較

| 項目 | Python版 (本リポジトリ) | Node.js版 (比較対象) |
| :--- | :--- | :--- |
| **開発言語** | Python (`discord.py`) | JavaScript/Node.js (`discord.js`) |
| **Antigravityとの通信** | **HTTP API (REST)** または **Mock** | **CDP (WebSocket)** によるDOM操作 |
| **操作対象** | バックエンドサービス (想定) | ローカルで起動中のGUIアプリ (VS Code) |
| **タスク管理** | `asyncio` + `apscheduler` | `ws` (WebSocket) + イベントループ |
| **拡張性** | `Cogs` による機能分割 (General, Scheduler) | 単一ファイル (`discord_bot.js`) に集約 |
| **データ永続化** | JSONファイル (`data/`) | 環境変数 (`.env`) のみ |

### Python版の特徴
*   **構造化された設計:** `src/core`, `src/cogs` とディレクトリが整理されており、保守性が高い。
*   **抽象化:** `BaseAntigravityClient` により、Mockと実APIの切り替えが容易。
*   **非同期処理:** Pythonの `asyncio` を活用し、Discordボットとバックエンド処理を効率的に並行実行。

### Node.js版の特徴
*   **GUIオートメーション:** `puppeteer` 相当の技術 (CDP) を使い、ボタンのクリックやテキスト入力をシミュレート。
*   **実用性重視:** APIがない現状のAntigravityに対し、即座に外部操作を実現するためのスクリプト。
*   **脆さ:** GUIの構造（DOMのクラス名やID）が変わると動作しなくなるリスクが高い。

---

## 3. 機能比較

### Python版 (本リポジトリ) の独自機能
1.  **スケジュール実行 (`/schedule`):**
    *   Cron形式での定期実行が可能。
    *   特定のワークスペース、プロンプトを指定して自動実行。
2.  **テンプレート管理 (`/templates`):**
    *   よく使うプロンプトを名前付きで保存・呼び出し可能。
3.  **ワークスペース同期:**
    *   AntigravityのワークスペースをDiscordのカテゴリ・チャンネルとして自動同期。
4.  **Mockモード:**
    *   Antigravityが起動していなくても、ボットの動作確認やUIテストが可能。

### Node.js版 (比較対象) の独自機能
1.  **スクリーンショット (`/screenshot`):**
    *   CDP経由で現在のAntigravityウィンドウの画面キャプチャを取得し、Discordに送信。
2.  **ファイル監視 (File Watcher):**
    *   `chokidar` を使用し、指定ディレクトリ (`WATCH_DIR`) 内のファイル変更を検知してDiscordに通知。
3.  **承認フローの自動連携:**
    *   画面上に「Approve/Reject」ボタンが出現した際、DOM解析で検知し、Discord上にボタンを表示して代理クリックさせる。
4.  **添付ファイル自動ダウンロード:**
    *   Discordにアップロードされたファイルをローカルの指定フォルダに自動保存。

---

## 4. コード品質と保守性

### Python版
*   **型ヒント:** `typing` モジュールや `dataclasses` を活用し、データ構造が明確。
*   **設定管理:** `pydantic` 風の `config.py` で環境変数を管理。
*   **ログ:** 標準の `logging` モジュールを使用し、構造化されたログ出力。

### Node.js版
*   **スクリプト指向:** `discord_bot.js` 1ファイルに約800行のロジックが詰め込まれており、可読性は低い。
*   **セレクタ分離:** `selectors.js` にDOMセレクタを分離している点は評価できるが、依存度は高い。
*   **エラーハンドリング:** CDPの切断やタイムアウトに対する再接続ロジックが含まれている。

## 5. まとめ

**Python版**は「理想的なAPIが存在する世界」での堅牢なボットシステムを目指しており、スケジュール機能やテンプレート機能など、Discordボットとしての利便性を追求しています。

一方、**Node.js版**は「APIがない現実の世界」でAntigravityを動かすための、実用本位のブリッジツールです。スクリーンショットやGUI操作など、APIでは実現しにくい（あるいはAPIが提供されていない）部分をカバーしています。

今後の方針として、AntigravityがAPIを提供するようになればPython版のアーキテクチャが優位になりますが、現状のGUI操作を維持する必要がある場合は、Python版にSeleniumやPlaywright、あるいはCDPライブラリ (`pyppeteer` 等) を組み込んでNode.js版の機能を移植することも検討できます。
