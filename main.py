import discord
from discord.ext import commands
import random
import asyncio
import os
import datetime

# ボットの設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

# おみくじの結果リスト
fortunes = [
    "😊 大吉！最高の運気まさ！",
    "😊 中吉！ほどよくがんばるまさ！",
    "😌 小吉！小さな幸せまさ！",
    "😅 末吉！油断禁物まさ！",
    "😱 凶！今日は慎重にまさ！"
]

# リマインダーを保存するリスト
reminders = []
reminder_tasks = {}  # キャンセル用のタスクを保存

# ボットが起動したとき
@bot.event
async def on_ready():
    print(f'{bot.user} が起動しました！')

# おみくじ（「今日の運勢」で反応）
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content == "今日の運勢":
        result = random.choice(fortunes)
        await message.channel.send(f"🎲 今日のおみくじ結果は...\n{result}")
    await bot.process_commands(message)  # コマンドも処理

# リマインダーコマンド
@bot.command()
async def remind(ctx, date: str, time: str, *, msg: str):
    try:
        # 日付と時間を結合して解析
        remind_time = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        now = datetime.datetime.now()
        if remind_time < now:
            await ctx.send("過去の時間は設定できないよ！未来の時間を入れてね！")
            return
        
        # 待機時間（秒）を計算
        wait_seconds = (remind_time - now).total_seconds()
        reminder_id = len(reminders) + 1
        reminders.append({
            'id': reminder_id,
            'user': ctx.author,
            'time': remind_time,
            'message': msg,
            'channel': ctx.channel
        })
        await ctx.send(f"{ctx.author.mention} さん、{remind_time.strftime('%Y年%m月%d日 %H:%M')} に「{msg}」をリマインドするよ！（ID: {reminder_id}）")
        
        # 非同期タスクを作成
        async def reminder_task():
            await asyncio.sleep(wait_seconds)
            if any(r['id'] == reminder_id for r in reminders):  # まだ存在するか確認
                await ctx.send(f"{ctx.author.mention} さん、リマインダー：{msg}")
                reminders[:] = [r for r in reminders if r['id'] != reminder_id]
        
        task = asyncio.create_task(reminder_task())
        reminder_tasks[reminder_id] = task
    except ValueError:
        await ctx.send("使い方: /remind 2025-09-19 14:30 メッセージ\n日付はYYYY-MM-DD、時間はHH:MMで入れてね！")

# リマインダーのエラー処理
@remind.error
async def remind_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("使い方: /remind 2025-09-19 14:30 メッセージ")
    else:
        await ctx.send("何か間違えたみたい！使い方: /remind 2025-09-19 14:30 メッセージ")

# リマインダー一覧表示
@bot.command()
async def list(ctx):
    user_reminders = [r for r in reminders if r['user'] == ctx.author]
    if not user_reminders:
        await ctx.send(f"{ctx.author.mention} さん、設定中のリマインダーはないよ！")
        return
    
    response = f"{ctx.author.mention} さんのリマインダー一覧:\n"
    for r in user_reminders:
        response += f"ID: {r['id']} | {r['time'].strftime('%Y年%m月%d日 %H:%M')} | {r['message']}\n"
    await ctx.send(response)

# リマインダー取り消し
@bot.command()
async def cancel(ctx, reminder_id: int):
    for r in reminders:
        if r['id'] == reminder_id and r['user'] == ctx.author:
            reminders.remove(r)
            reminder_tasks[reminder_id].cancel()
            del reminder_tasks[reminder_id]
            await ctx.send(f"{ctx.author.mention} さん、リマインダー（ID: {reminder_id}）を取り消したよ！")
            return
    await ctx.send(f"{ctx.author.mention} さん、ID: {reminder_id} のリマインダーが見つからないよ！")

# キャンセルのエラー処理
@cancel.error
async def cancel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("使い方: /cancel <リマインダーID>")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("IDは数字で入れてね！")

# ボット起動
bot.run(os.getenv('DISCORD_TOKEN'))
