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

def format_response(ctx, message, mention=True):
    if mention:
        return f"{ctx.author.mention} {message}"
    else:
        return message

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

# Command to allow everyone to use the bot
@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send(format_response(ctx, "✅ Bot access has been successfully enabled for **everyone**!"))
    else:
        await ctx.send(format_response(ctx, "❌ You do not have permission to execute this command."))

# Command to restrict bot usage to only special user
@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send(format_response(ctx, "🔒 Bot access has been restricted to **authorized users only**."))
    else:
        await ctx.send(format_response(ctx, "❌ You do not have permission to execute this command."))

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send(format_response(ctx, "🚫 You are not authorized to use this command right now.", mention=False))
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(format_response(ctx, "🎙️ Please join a voice channel first.", mention=False))
        return

    if member is None:
        await ctx.send(format_response(ctx, "🔎 Please mention a user to pull. Example: `&pull @Username`", mention=False))
        return

    if not member.voice:
        await ctx.send(format_response(ctx, f"🔇 {member.name} is not connected to any voice channel.", mention=False))
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(format_response(ctx, f"🎯 {member.name} has been moved to your voice channel.", mention=False))
    except discord.Forbidden:
        await ctx.send(format_response(ctx, "❗ I don't have permission to move members.", mention=False))
    except Exception as e:
        await ctx.send(format_response(ctx, f"⚠️ An unexpected error occurred: {e}", mention=False))

# New moveall command to move all members
@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send(format_response(ctx, "🚫 You are not authorized to use this command right now.", mention=False))
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(format_response(ctx, "🎙️ Please join a voice channel first.", mention=False))
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(format_response(ctx, f"❗ Cannot move {member.name} due to permission issues.", mention=False))
            except Exception as e:
                await ctx.send(format_response(ctx, f"⚠️ Error occurred while moving {member.name}: {e}", mention=False))

    if moved > 0:
        await ctx.send(format_response(ctx, f"🚀 {moved} members have been successfully moved to your voice channel.", mention=False))
    else:
        await ctx.send(format_response(ctx, "❌ No members found in voice channels or an error occurred.", mention=False))

# Command to list roles allowed to use the bot
@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        await ctx.send(format_response(ctx, "📋 No roles have been authorized yet."))
    else:
        roles_list = "\n".join([f"• Role ID: `{role_id}` | Name: **{role.name}**" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        await ctx.send(format_response(ctx, f"📜 **Authorized Roles:**\n{roles_list}"))

# Command to add a role to the allowed list
@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(format_response(ctx, "❌ You do not have permission to add roles."))
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            await ctx.send(format_response(ctx, f"✅ Role **{role.name}** has been successfully authorized."))
        else:
            await ctx.send(format_response(ctx, f"ℹ️ Role **{role.name}** is already authorized."))
    else:
        await ctx.send(format_response(ctx, f"❓ Role `{role_name_or_id}` not found."))

# Command to remove a role from the allowed list
@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(format_response(ctx, "❌ You do not have permission to remove roles."))
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            await ctx.send(format_response(ctx, f"🗑️ Role **{role.name}** has been removed from authorized list."))
        else:
            await ctx.send(format_response(ctx, f"ℹ️ Role **{role.name}** was not authorized earlier."))
    else:
        await ctx.send(format_response(ctx, f"❓ Role `{role_name_or_id}` not found."))

keep_alive()
bot.run(os.getenv('TOKEN'))
