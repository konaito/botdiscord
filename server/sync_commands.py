#!/usr/bin/env python3
"""
Discordスラッシュコマンド同期スクリプト
Vercelにデプロイされたサーバーのスラッシュコマンドを手動で同期します。
"""

import requests
import json
import sys
import time

def sync_commands(vercel_url="https://botdiscord-rust.vercel.app"):
    """スラッシュコマンドを同期する"""
    
    print("🔄 Discordスラッシュコマンドを同期中...")
    
    # Botの状態を確認
    try:
        status_response = requests.get(f"{vercel_url}/bot/status", timeout=10)
        status_data = status_response.json()
        print(f"📊 Bot状態: {json.dumps(status_data, indent=2, ensure_ascii=False)}")
        
        if not status_data.get("bot_ready", False):
            print("⚠️ Botが起動していません。環境変数が設定されているか確認してください。")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Bot状態の確認に失敗しました: {e}")
        return False
    
    # スラッシュコマンドを同期
    try:
        sync_response = requests.post(f"{vercel_url}/bot/sync-commands", timeout=30)
        sync_data = sync_response.json()
        
        if sync_data.get("status") == "success":
            print("✅ スラッシュコマンドの同期が成功しました！")
            print(f"📝 同期されたコマンド数: {sync_data.get('synced_commands', 0)}")
            print(f"🔧 コマンド一覧: {', '.join(sync_data.get('commands', []))}")
            return True
        else:
            print(f"❌ スラッシュコマンドの同期に失敗しました: {sync_data}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 同期リクエストに失敗しました: {e}")
        return False

def main():
    """メイン関数"""
    print("🤖 Discord Bot スラッシュコマンド同期ツール")
    print("=" * 50)
    
    # コマンドライン引数からURLを取得
    vercel_url = sys.argv[1] if len(sys.argv) > 1 else "https://botdiscord-rust.vercel.app"
    
    print(f"🌐 対象URL: {vercel_url}")
    print()
    
    # 同期実行
    success = sync_commands(vercel_url)
    
    if success:
        print("\n🎉 同期が完了しました！")
        print("💡 Discordでスラッシュコマンドが利用可能になります。")
        sys.exit(0)
    else:
        print("\n💥 同期に失敗しました。")
        print("🔍 以下を確認してください:")
        print("  - Vercelにデプロイが完了しているか")
        print("  - 環境変数（DISCORD_TOKEN, DISCORD_PUBLIC_KEY）が設定されているか")
        print("  - BotがDiscordサーバーに招待されているか")
        sys.exit(1)

if __name__ == "__main__":
    main()
