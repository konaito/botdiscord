from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn

# 環境変数を読み込み
load_dotenv()


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
async def handle_interactions(interaction: DiscordInteraction):
    """Vercel用のインタラクションエンドポイント"""
    return await handle_discord_interaction(interaction)


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


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
