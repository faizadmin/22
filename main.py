import discord
from discord.ext import commands
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

special_user_id = 1176678272579424258
access_enabled = False
allowed_roles = []

def format_response(ctx, message, mention=True):
    if mention:
        return f"{ctx.author.mention} {message}"
    else:
        return message

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send(format_response(ctx, "Bot ka use sabhi users ke liye enable kar diya gaya hai."))
    else:
        await ctx.send(format_response(ctx, "Aapko is command ka use karne ki permission nahi hai."))

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send(format_response(ctx, "Bot ka use sirf specific user ke liye restrict kar diya gaya hai."))
    else:
        await ctx.send(format_response(ctx, "Aapko is command ka use karne ki permission nahi hai."))

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send(format_response(ctx, "Bot ka use abhi sirf specific user ya authorized roles ke liye allowed hai.", mention=False))
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(format_response(ctx, "Aap kisi VC me nahi ho.", mention=False))
        return

    if member is None:
        await ctx.send(format_response(ctx, "Aapko ek member ko mention karna hoga. Example: `&pull @John`", mention=False))
        return

    if not member.voice:
        await ctx.send(format_response(ctx, f"{member.name} VC me nahi hai.", mention=False))
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(format_response(ctx, f"{member.name} ko aapke VC me move kar diya gaya hai.", mention=False))
    except discord.Forbidden:
        await ctx.send(format_response(ctx, "Bot ke paas members ko move karne ki permission nahi hai.", mention=False))
    except Exception as e:
        await ctx.send(format_response(ctx, f"Kuch error aayi: {e}", mention=False))

@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send(format_response(ctx, "Bot ka use abhi sirf specific user ya authorized roles ke liye allowed hai.", mention=False))
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(format_response(ctx, "Aap kisi VC me nahi ho.", mention=False))
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(format_response(ctx, f"Bot ke paas {member.name} ko move karne ki permission nahi hai.", mention=False))
            except Exception as e:
                await ctx.send(format_response(ctx, f"Kuch error aayi: {e}", mention=False))

    if moved > 0:
        await ctx.send(format_response(ctx, f"{moved} members ko aapke VC me move kar diya gaya hai.", mention=False))
    else:
        await ctx.send(format_response(ctx, "Koi member VC me nahi tha ya koi error aayi.", mention=False))

@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        await ctx.send(format_response(ctx, "Abhi koi roles ko permission nahi di gayi hai."))
    else:
        roles_list = "\n".join([f"Role ID: {role_id}, Role Name: {role.name}" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        await ctx.send(format_response(ctx, f"Allowed Roles:\n{roles_list}"))

@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(format_response(ctx, "Aapko is command ka use karne ki permission nahi hai."))
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            await ctx.send(format_response(ctx, f"Role '{role.name}' ko bot use karne ki permission de di gayi hai."))
        else:
            await ctx.send(format_response(ctx, f"Role '{role.name}' already allowed hai."))
    else:
        await ctx.send(format_response(ctx, f"Role '{role_name_or_id}' nahi mila."))

@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(format_response(ctx, "Aapko is command ka use karne ki permission nahi hai."))
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            await ctx.send(format_response(ctx, f"Role '{role.name}' ko permission se hata diya gaya hai."))
        else:
            await ctx.send(format_response(ctx, f"Role '{role.name}' ke paas pehle se permission nahi thi."))
    else:
        await ctx.send(format_response(ctx, f"Role '{role_name_or_id}' nahi mila."))

# Keep alive server
keep_alive()
bot.run(os.getenv('TOKEN'))
