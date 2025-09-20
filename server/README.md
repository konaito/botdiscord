# Discord Bot FastAPI Server

Discordのスラッシュコマンド対応のFastAPIサーバーです。

## 機能

- Discord Botのスラッシュコマンド対応
- FastAPIベースのRESTful API
- ヘルスチェックエンドポイント
- Botの状態監視
- カスタムコマンド実行

## セットアップ

### 1. 仮想環境の作成と依存関係のインストール

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境をアクティベート
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate     # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

1. `env.example` を `.env` にコピー
2. Discord Developer Portal (https://discord.com/developers/applications) でBotトークンと公開鍵を取得
3. `.env` ファイルで `DISCORD_TOKEN` と `DISCORD_PUBLIC_KEY` を設定

```bash
cp env.example .env
# .envファイルを編集してDISCORD_TOKENとDISCORD_PUBLIC_KEYを設定
```

#### Discord Developer Portal での設定

1. **Discord Developer Portal** (https://discord.com/developers/applications) にアクセス
2. あなたのBotアプリケーションを選択
3. **General Information** タブで：
   - **Token** をコピーして `DISCORD_TOKEN` に設定
   - **Public Key** をコピーして `DISCORD_PUBLIC_KEY` に設定
4. **INTERACTIONS ENDPOINT URL** を設定：
   ```
   https://botdiscord-rust.vercel.app/interactions
   ```
5. **Save Changes** をクリック

### 3. サーバーの起動

```bash
# 仮想環境をアクティベート
source venv/bin/activate

# サーバーを起動
python main.py
```

サーバーは `http://localhost:8000` で起動します。

## API エンドポイント

### 基本エンドポイント

- `GET /` - サーバー情報
- `GET /health` - ヘルスチェック
- `GET /bot/status` - Botの状態

### Discord関連エンドポイント

- `POST /discord/interaction` - Discordインタラクション処理
- `POST /command` - カスタムコマンド実行

## 利用可能なスラッシュコマンド

- `/ping` - Botの応答時間を測定
- `/hello` - 挨拶
- `/serverinfo` - サーバー情報を表示
- `/userinfo` - ユーザー情報を表示

## 開発

### 新しいスラッシュコマンドの追加

1. `main.py` の `@bot.tree.command` デコレータを使用
2. コマンド関数を定義
3. Botを再起動してスラッシュコマンドを同期

### API ドキュメント

FastAPIの自動生成ドキュメントは以下で確認できます：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## トラブルシューティング

### Botが起動しない場合

1. `.env` ファイルで `DISCORD_TOKEN` が正しく設定されているか確認
2. Botに必要な権限が付与されているか確認
3. ログを確認してエラーメッセージをチェック

### スラッシュコマンドが表示されない場合

1. Botがサーバーに招待されているか確認
2. Botに `applications.commands` スコープが付与されているか確認
3. スラッシュコマンドの同期が完了しているか確認
