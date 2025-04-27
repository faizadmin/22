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
async def pull(ctx, member: discord.Member = None):
    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("Tum kisi VC me nahi ho.")
        return

    if member is None:
        await ctx.send("Tumhe ek member ko mention karna hoga. Example: &pull @John")
        return

    if not member.voice:
        await ctx.send(f"{member.name} VC me nahi hai.")
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(f"{member.name} ko {ctx.author.name} ne tumhare VC me move kar diya gaya.")
    except discord.Forbidden:
        await ctx.send("Bot ke paas permission nahi hai members ko move karne ki.")
    except Exception as e:
        await ctx.send(f"Kuch error hua: {e}")

# New moveall command to move all members
@bot.command()
async def moveall(ctx):
    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("Tum kisi VC me nahi ho.")
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(f"Bot ke paas permission nahi hai {member.name} ko move karne ki.")
            except Exception as e:
                await ctx.send(f"Kuch error hua: {e}")

    if moved > 0:
        await ctx.send(f"{moved} members ko {ctx.author.name} ne tumhare VC me move kar diya gaya.")
    else:
        await ctx.send("Koi member VC me nahi tha ya koi error aayi.")

keep_alive()
bot.run(os.getenv('TOKEN'))
