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

# List to store role IDs that are allowed to use the bot
allowed_roles = []

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    for guild in bot.guilds:
        print(f'Connected to guild: {guild.name} (ID: {guild.id})')

@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send("✅ Bot access sabhi users ke liye successfully enable kar diya gaya hai.")
    else:
        await ctx.send("❌ Aapko is command ko execute karne ka adhikar nahi hai.")

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send("✅ Bot access ab sirf authorized user ke liye restrict kar diya gaya hai.")
    else:
        await ctx.send("❌ Aapko is command ko execute karne ka adhikar nahi hai.")

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Aapko bot ka use karne ka permission nahi hai.")
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("⚠️ Aap kisi voice channel mein maujood nahi hain. Pehle voice channel join kijiye.")
        return

    if member is None:
        await ctx.send("⚠️ Kripya karke ek member ko mention karein. Udaharan: `&pull @John`")
        return

    if not member.voice:
        await ctx.send(f"⚠️ {member.name} kisi bhi voice channel mein nahi hai.")
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(f"✅ {member.name} ko aapke voice channel mein move kar diya gaya hai.")
    except discord.Forbidden:
        await ctx.send("❌ Bot ke paas members ko move karne ki required permissions nahi hain.")
    except Exception as e:
        await ctx.send(f"❌ Ek error aayi hai: {e}")

@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Aapko bot ka use karne ka permission nahi hai.")
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("⚠️ Aap kisi voice channel mein maujood nahi hain. Pehle voice channel join kijiye.")
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(f"❌ Bot {member.name} ko move nahi kar paya due to missing permissions.")
            except Exception as e:
                await ctx.send(f"❌ Ek error aayi hai: {e}")

    if moved > 0:
        await ctx.send(f"✅ {moved} members ko aapke voice channel mein move kar diya gaya hai.")
    else:
        await ctx.send("⚠️ Koi members available nahi the ya ek error hui.")

@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        await ctx.send("ℹ️ Abhi kisi bhi role ko bot access ki anumati nahi di gayi hai.")
    else:
        roles_list = "\n".join(
            [f"Role ID: {role_id}, Role Name: {role.name}" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id]
        )
        await ctx.send(f"✅ Allowed roles:\n{roles_list}")

@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send("❌ Aapko is command ko execute karne ka adhikar nahi hai.")
        return

    role = None
    try:
        role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    except ValueError:
        pass

    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            await ctx.send(f"✅ Role '{role.name}' ko bot access ke liye authorize kar diya gaya hai.")
        else:
            await ctx.send(f"ℹ️ Role '{role.name}' already authorized hai.")
    else:
        await ctx.send(f"❌ Role '{role_name_or_id}' server mein nahi mila.")

@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send("❌ Aapko is command ko execute karne ka adhikar nahi hai.")
        return

    role = None
    try:
        role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    except ValueError:
        pass

    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            await ctx.send(f"✅ Role '{role.name}' se bot access ki permission hata di gayi hai.")
        else:
            await ctx.send(f"ℹ️ Role '{role.name}' ke paas pehle se koi special permission nahi thi.")
    else:
        await ctx.send(f"❌ Role '{role_name_or_id}' server mein nahi mila.")

keep_alive()
bot.run(os.getenv('TOKEN'))
