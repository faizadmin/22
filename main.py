import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def pull(ctx, *, member_name: str):
    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("Tum kisi VC me nahi ho.")
        return
    
    target_member = None
    for member in ctx.guild.members:
        if member.name.lower() == member_name.lower() or member.display_name.lower() == member_name.lower():
            target_member = member
            break

    if not target_member:
        await ctx.send("Member nahi mila.")
        return

    if not target_member.voice:
        await ctx.send(f"{target_member.name} VC me nahi hai.")
        return

    try:
        await target_member.move_to(author_voice.channel)
        await ctx.send(f"{target_member.name} ko tumhare VC me move kar diya gaya.")
    except discord.Forbidden:
        await ctx.send("Bot ke paas permission nahi hai members ko move karne ki.")
    except Exception as e:
        await ctx.send(f"Kuch error hua: {e}")

keep_alive()
bot.run(os.getenv('TOKEN'))
