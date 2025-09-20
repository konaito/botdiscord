from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import json
import hashlib
import hmac
import base64
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# 環境変数を読み込み
load_dotenv()

# Discord公開鍵（環境変数から取得）
DISCORD_PUBLIC_KEY = os.getenv('DISCORD_PUBLIC_KEY')

def verify_signature(raw_body: bytes, signature: str, timestamp: str) -> bool:
    """Discordの署名を検証する"""
    if not DISCORD_PUBLIC_KEY:
        print("警告: DISCORD_PUBLIC_KEYが設定されていません")
        return False
    
    try:
        # 署名を検証
        message = timestamp.encode() + raw_body
        verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
        verify_key.verify(message, bytes.fromhex(signature))
        return True
    except (BadSignatureError, ValueError) as e:
        print(f"署名検証失敗: {e}")
        return False


# Botを起動する関数
async def start_bot():
    token = os.getenv("DISCORD_TOKEN")
    if not token or token == "your_discord_bot_token_here":
        print("警告: DISCORD_TOKENが設定されていません。Botは起動しません。")
        return

    try:
        await bot.start(token)
    except Exception as e:
        print(f"Botの起動に失敗しました: {e}")


# アプリケーションのライフサイクル管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    print("アプリケーションを起動中...")
    asyncio.create_task(start_bot())
    yield
    # 終了時
    print("アプリケーションを終了中...")
    await bot.close()


# FastAPIアプリケーションの初期化
app = FastAPI(
    title="Discord Bot API",
    description="Discordスラッシュコマンド対応のFastAPIサーバー",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Discord Botの設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# リクエストモデル
class DiscordInteraction(BaseModel):
    type: int
    data: Optional[Dict[str, Any]] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None
    user: Optional[Dict[str, Any]] = None


class CommandRequest(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None
    user_id: str
    guild_id: Optional[str] = None
    channel_id: str


# Botイベント
@bot.event
async def on_ready():
    print(f"{bot.user} がログインしました！")
    print(f"Bot ID: {bot.user.id}")

    # スラッシュコマンドを同期
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)} 個のスラッシュコマンドを同期しました")
    except Exception as e:
        print(f"スラッシュコマンドの同期に失敗しました: {e}")


# スラッシュコマンドの定義
@bot.tree.command(name="ping", description="Botの応答時間を測定します")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! 応答時間: {latency}ms")


@bot.tree.command(name="hello", description="挨拶をします")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"こんにちは、{interaction.user.mention}さん！"
    )


@bot.tree.command(name="serverinfo", description="サーバー情報を表示します")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    embed = discord.Embed(title=f"{guild.name} の情報", color=discord.Color.blue())
    embed.add_field(name="メンバー数", value=guild.member_count, inline=True)
    embed.add_field(name="サーバーID", value=guild.id, inline=True)
    embed.add_field(
        name="作成日", value=guild.created_at.strftime("%Y年%m月%d日"), inline=True
    )
    embed.add_field(name="オーナー", value=guild.owner.mention, inline=True)
    embed.add_field(name="チャンネル数", value=len(guild.channels), inline=True)
    embed.add_field(name="ロール数", value=len(guild.roles), inline=True)

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="userinfo", description="ユーザー情報を表示します")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user

    embed = discord.Embed(title=f"{user.display_name} の情報", color=user.color)
    embed.add_field(name="ユーザー名", value=user.name, inline=True)
    embed.add_field(name="ディスプレイ名", value=user.display_name, inline=True)
    embed.add_field(name="ユーザーID", value=user.id, inline=True)
    embed.add_field(
        name="アカウント作成日",
        value=user.created_at.strftime("%Y年%m月%d日"),
        inline=True,
    )
    embed.add_field(
        name="サーバー参加日",
        value=user.joined_at.strftime("%Y年%m月%d日"),
        inline=True,
    )
    embed.add_field(name="ロール数", value=len(user.roles), inline=True)

    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="here", description="現在のサーバー、カテゴリ、チャンネル情報を表示します")
async def here(interaction: discord.Interaction):
    guild = interaction.guild
    channel = interaction.channel
    
    embed = discord.Embed(
        title="📍 現在の場所情報",
        color=discord.Color.green()
    )
    
    # サーバー情報
    if guild:
        embed.add_field(
            name="🏰 サーバー",
            value=f"**{guild.name}**\nID: `{guild.id}`\nメンバー数: {guild.member_count}",
            inline=False
        )
    else:
        embed.add_field(name="🏰 サーバー", value="DM", inline=False)
    
    # チャンネル情報
    if isinstance(channel, discord.TextChannel):
        embed.add_field(
            name="💬 チャンネル",
            value=f"**#{channel.name}**\nID: `{channel.id}`",
            inline=True
        )
        
        # カテゴリ情報
        if channel.category:
            embed.add_field(
                name="📁 カテゴリ",
                value=f"**{channel.category.name}**\nID: `{channel.category.id}`",
                inline=True
            )
        else:
            embed.add_field(name="📁 カテゴリ", value="なし", inline=True)
            
        # チャンネル作成日
        embed.add_field(
            name="📅 チャンネル作成日",
            value=channel.created_at.strftime("%Y年%m月%d日 %H:%M"),
            inline=True
        )
        
    elif isinstance(channel, discord.DMChannel):
        embed.add_field(
            name="💬 チャンネル",
            value="DM",
            inline=True
        )
        embed.add_field(name="📁 カテゴリ", value="なし", inline=True)
    
    # ユーザー情報
    user = interaction.user
    embed.add_field(
        name="👤 あなた",
        value=f"**{user.display_name}**\nID: `{user.id}`",
        inline=False
    )
    
    # タイムスタンプ
    embed.timestamp = discord.utils.utcnow()
    
    await interaction.response.send_message(embed=embed)


# FastAPIエンドポイント
@app.get("/")
async def root():
    return {
        "message": "Discord Bot API Server",
        "status": "running",
        "updated": "1758356604",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "bot_ready": bot.is_ready()}


@app.post("/discord/interaction")
async def handle_discord_interaction(interaction: DiscordInteraction):
    """Discordのインタラクションを処理するエンドポイント"""
    try:
        if interaction.type == 1:  # PING
            return {"type": 1}
        elif interaction.type == 2:  # APPLICATION_COMMAND
            # スラッシュコマンドの処理
            command_name = interaction.data.get("name", "")

            if command_name == "ping":
                return {
                    "type": 4,
                    "data": {"content": "🏓 Pong! API経由で応答しました"},
                }
            elif command_name == "hello":
                user_id = interaction.user.get("id", "unknown")
                return {
                    "type": 4,
                    "data": {"content": f"こんにちは、<@{user_id}>さん！"},
                }
            else:
                return {
                    "type": 4,
                    "data": {
                        "content": f"コマンド '{command_name}' は認識されませんでした。"
                    },
                }
        else:
            return {
                "type": 4,
                "data": {"content": "不明なインタラクションタイプです。"},
            }

    except Exception as e:
        print(f"インタラクション処理エラー: {e}")
        return {"type": 4, "data": {"content": "エラーが発生しました。"}}


@app.post("/interactions")
async def handle_interactions(request: Request):
    """Vercel用のインタラクションエンドポイント（署名検証付き）"""
    try:
        # 生のリクエストボディを取得
        raw_body = await request.body()
        
        # 署名ヘッダーを取得
        signature = request.headers.get("X-Signature-Ed25519")
        timestamp = request.headers.get("X-Signature-Timestamp")
        
        if not signature or not timestamp:
            print("署名ヘッダーが不足しています")
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # 署名を検証
        if not verify_signature(raw_body, signature, timestamp):
            print("署名検証に失敗しました")
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # JSONをパース
        body = json.loads(raw_body.decode('utf-8'))
        
        # デバッグ用ログ（本番環境では削除推奨）
        print(f"受信したインタラクション: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        # DiscordのPINGリクエスト（type: 1）を処理
        if body.get("type") == 1:
            return {"type": 1}
        
        # スラッシュコマンド（type: 2）を処理
        elif body.get("type") == 2:
            command_name = body.get("data", {}).get("name", "")
            
            # ユーザー情報を正しく取得
            user_info = body.get("member", {}).get("user") or body.get("user", {})
            user_id = user_info.get("id", "unknown")
            username = user_info.get("username", "Unknown")
            
            if command_name == "ping":
                return {
                    "type": 4,
                    "data": {"content": "🏓 Pong! Vercel経由で応答しました"}
                }
            elif command_name == "hello":
                return {
                    "type": 4,
                    "data": {"content": f"こんにちは、<@{user_id}>さん！"}
                }
            elif command_name == "here":
                # サーバー、カテゴリ、チャンネル情報を取得
                guild_id = body.get("guild_id", "DM")
                channel_id = body.get("channel_id", "unknown")
                
                # 基本的な情報を返す（実際のDiscord APIから詳細情報を取得する場合は別途実装が必要）
                return {
                    "type": 4,
                    "data": {
                        "content": f"📍 **現在の場所情報**\n\n🏰 **サーバー**: {guild_id}\n💬 **チャンネル**: <#{channel_id}>\n👤 **ユーザー**: <@{user_id}>"
                    }
                }
            else:
                return {
                    "type": 4,
                    "data": {"content": f"コマンド '{command_name}' は認識されませんでした。"}
                }
        else:
            return {
                "type": 4,
                "data": {"content": "不明なインタラクションタイプです。"}
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"インタラクション処理エラー: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/test-interaction")
async def test_interaction(request: Request):
    """テスト用のインタラクションエンドポイント（署名検証なし）"""
    try:
        body = await request.json()
        
        # デバッグ用ログ
        print(f"テスト用インタラクション受信: {json.dumps(body, indent=2, ensure_ascii=False)}")
        
        # DiscordのPINGリクエスト（type: 1）を処理
        if body.get("type") == 1:
            return {"type": 1}
        
        # スラッシュコマンド（type: 2）を処理
        elif body.get("type") == 2:
            command_name = body.get("data", {}).get("name", "")
            
            # ユーザー情報を正しく取得
            user_info = body.get("member", {}).get("user") or body.get("user", {})
            user_id = user_info.get("id", "unknown")
            username = user_info.get("username", "Unknown")
            
            print(f"ユーザー情報: ID={user_id}, Username={username}")
            
            if command_name == "ping":
                return {
                    "type": 4,
                    "data": {"content": "🏓 Pong! テスト経由で応答しました"}
                }
            elif command_name == "hello":
                return {
                    "type": 4,
                    "data": {"content": f"こんにちは、<@{user_id}>さん！"}
                }
            elif command_name == "here":
                # サーバー、カテゴリ、チャンネル情報を取得
                guild_id = body.get("guild_id", "DM")
                channel_id = body.get("channel_id", "unknown")
                
                return {
                    "type": 4,
                    "data": {
                        "content": f"📍 **現在の場所情報**\n\n🏰 **サーバー**: {guild_id}\n💬 **チャンネル**: <#{channel_id}>\n👤 **ユーザー**: <@{user_id}>"
                    }
                }
            else:
                return {
                    "type": 4,
                    "data": {"content": f"コマンド '{command_name}' は認識されませんでした。"}
                }
        else:
            return {
                "type": 4,
                "data": {"content": "不明なインタラクションタイプです。"}
            }
    
    except Exception as e:
        print(f"テストインタラクション処理エラー: {e}")
        return {"type": 4, "data": {"content": "エラーが発生しました。"}}

@app.post("/command")
async def execute_command(command_request: CommandRequest):
    """カスタムコマンドを実行するエンドポイント"""
    try:
        command = command_request.command
        user_id = command_request.user_id
        guild_id = command_request.guild_id
        channel_id = command_request.channel_id

        # チャンネルとユーザーを取得
        channel = bot.get_channel(int(channel_id))
        if not channel:
            raise HTTPException(status_code=404, detail="チャンネルが見つかりません")

        user = bot.get_user(int(user_id))
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        # コマンドの実行
        if command == "ping":
            latency = round(bot.latency * 1000)
            await channel.send(f"🏓 Pong! 応答時間: {latency}ms (API経由)")
            return {"message": "Pingコマンドを実行しました"}

        elif command == "hello":
            await channel.send(f"こんにちは、{user.mention}さん！ (API経由)")
            return {"message": "Helloコマンドを実行しました"}

        elif command == "serverinfo":
            if guild_id:
                guild = bot.get_guild(int(guild_id))
                if guild:
                    embed = discord.Embed(
                        title=f"{guild.name} の情報", color=discord.Color.blue()
                    )
                    embed.add_field(
                        name="メンバー数", value=guild.member_count, inline=True
                    )
                    embed.add_field(name="サーバーID", value=guild.id, inline=True)
                    embed.add_field(
                        name="作成日",
                        value=guild.created_at.strftime("%Y年%m月%d日"),
                        inline=True,
                    )
                    embed.add_field(
                        name="オーナー", value=guild.owner.mention, inline=True
                    )
                    embed.add_field(
                        name="チャンネル数", value=len(guild.channels), inline=True
                    )
                    embed.add_field(
                        name="ロール数", value=len(guild.roles), inline=True
                    )

                    if guild.icon:
                        embed.set_thumbnail(url=guild.icon.url)

                    await channel.send(embed=embed)
                    return {"message": "サーバー情報を送信しました"}
                else:
                    raise HTTPException(
                        status_code=404, detail="サーバーが見つかりません"
                    )
            else:
                raise HTTPException(status_code=400, detail="サーバーIDが必要です")

        else:
            raise HTTPException(status_code=400, detail=f"不明なコマンド: {command}")

    except Exception as e:
        print(f"コマンド実行エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bot/status")
async def get_bot_status():
    """Botの状態を取得"""
    return {
        "bot_ready": bot.is_ready(),
        "bot_user": str(bot.user) if bot.user else None,
        "bot_id": bot.user.id if bot.user else None,
        "guilds": len(bot.guilds),
        "users": len(bot.users),
    }

@app.post("/bot/sync-commands")
async def sync_commands():
    """スラッシュコマンドを手動で同期"""
    try:
        if not bot.is_ready():
            return {"error": "Bot is not ready", "status": "failed"}
        
        synced = await bot.tree.sync()
        return {
            "status": "success",
            "synced_commands": len(synced),
            "commands": [cmd.name for cmd in synced]
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
