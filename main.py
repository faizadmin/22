import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

# Special user ID who can control the access
special_user_id = 1176678272579424258
access_enabled = False  # Default access is restricted to special user

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command to allow everyone to use the bot
@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send("Bot ka use sabhi users ke liye enable kar diya gaya hai.")
    else:
        await ctx.send("Sirf ek specific user ko yeh command use karne ka permission hai.")

# Command to restrict bot usage to only special user
@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send("Bot ka use sirf ek specific user ke liye restrict kar diya gaya hai.")
    else:
        await ctx.send("Sirf ek specific user ko yeh command use karne ka permission hai.")

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id:
        await ctx.send("Bot ka use abhi sirf ek specific user ke liye allowed hai.")
        return

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
    if not access_enabled and ctx.author.id != special_user_id:
        await ctx.send("Bot ka use abhi sirf ek specific user ke liye allowed hai.")
        return

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
