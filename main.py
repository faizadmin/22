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

def format_response(ctx, message):
    return f"{ctx.author.mention} {message}"

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

# Command to allow everyone to use the bot
@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send(format_response(ctx, "✅ Bot access has been successfully enabled for **everyone**!\n\n🤖 Developed by **Faiz**."))
    else:
        await ctx.send(format_response(ctx, "❌ You do not have permission to execute this command."))

# Command to restrict bot usage to only special user
@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send(format_response(ctx, "🔒 Bot access has been restricted to **authorized users only**.\n\n🛡️ Authorized person: **Faiz** (Bot Developer)"))
    else:
        await ctx.send(format_response(ctx, "❌ You do not have permission to execute this command."))

# Command to pull a member to your voice channel
@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Bot access is currently restricted to authorized users only.")
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("🔊 You must be connected to a voice channel first.")
        return

    if member is None:
        await ctx.send(format_response(ctx, "❗ Please mention a member to pull. Example: `&pull @John`"))
        return

    if not member.voice:
        await ctx.send(format_response(ctx, f"❗ {member.name} is not connected to any voice channel."))
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(f"✅ {member.name} has been moved to your voice channel by {ctx.author.name}.")
    except discord.Forbidden:
        await ctx.send(format_response(ctx, "🚫 Bot does not have permission to move members."))
    except Exception as e:
        await ctx.send(format_response(ctx, f"⚠️ An error occurred: {e}"))

# Command to move all members to your VC
@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send(format_response(ctx, "❌ Bot access is currently restricted to authorized users only."))
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(format_response(ctx, "🔊 You must be connected to a voice channel first."))
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(format_response(ctx, f"🚫 Bot does not have permission to move {member.name}."))
            except Exception as e:
                await ctx.send(format_response(ctx, f"⚠️ An error occurred: {e}"))

    if moved > 0:
        await ctx.send(format_response(ctx, f"✅ {moved} members have been successfully moved to your voice channel."))
    else:
        await ctx.send(format_response(ctx, "❗ No members were found in any voice channel or an error occurred."))

# Command to list all allowed roles
@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        await ctx.send(format_response(ctx, "📜 No roles have permission to use the bot."))
    else:
        roles_list = "\n".join([f"🔹 {role.name} (ID: {role.id})" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        await ctx.send(format_response(ctx, f"📜 Roles allowed to use the bot:\n{roles_list}"))

# Command to add a role to allowed list
@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(format_response(ctx, "❌ You do not have permission to execute this command."))
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            await ctx.send(format_response(ctx, f"✅ Role **{role.name}** has been granted permission to use the bot."))
        else:
            await ctx.send(format_response(ctx, f"ℹ️ Role **{role.name}** already has permission."))
    else:
        await ctx.send(format_response(ctx, f"❗ Role '{role_name_or_id}' not found."))

# Command to remove a role from allowed list
@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(format_response(ctx, "❌ You do not have permission to execute this command."))
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            await ctx.send(format_response(ctx, f"✅ Role **{role.name}** has been removed from allowed list."))
        else:
            await ctx.send(format_response(ctx, f"ℹ️ Role **{role.name}** did not have permission."))
    else:
        await ctx.send(format_response(ctx, f"❗ Role '{role_name_or_id}' not found."))

keep_alive()
bot.run(os.getenv('TOKEN'))
