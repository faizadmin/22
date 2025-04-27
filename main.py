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

def format_response(message):
    return message

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send(format_response("✅ Bot access has been successfully enabled for **everyone**!\n\n🤖 Developed by **Faiz**."), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(format_response("❌ You do not have permission to execute this command."), reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send(format_response("🔒 Bot access has been restricted to **authorized users only**.\n\n🛡️ Authorized person: **Faiz** (Bot Developer)"), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(format_response("❌ You do not have permission to execute this command."), reference=ctx.message, mention_author=False)

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Bot access is currently restricted to authorized users only.", reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("🔊 You must be connected to a voice channel first.", reference=ctx.message, mention_author=False)
        return

    if member is None:
        await ctx.send("❗ Please mention a member to pull. Example: `&pull @John`", reference=ctx.message, mention_author=False)
        return

    if not member.voice:
        await ctx.send(f"❗ {member.name} is not connected to any voice channel.", reference=ctx.message, mention_author=False)
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(f"✅ {member.name} has been moved to your voice channel by {ctx.author.name}.", reference=ctx.message, mention_author=False)
    except discord.Forbidden:
        await ctx.send("🚫 Bot does not have permission to move members.", reference=ctx.message, mention_author=False)
    except Exception as e:
        await ctx.send(f"⚠️ An error occurred: {e}", reference=ctx.message, mention_author=False)

@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ Bot access is currently restricted to authorized users only.", reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("🔊 You must be connected to a voice channel first.", reference=ctx.message, mention_author=False)
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(f"🚫 Bot does not have permission to move {member.name}.", reference=ctx.message, mention_author=False)
            except Exception as e:
                await ctx.send(f"⚠️ An error occurred: {e}", reference=ctx.message, mention_author=False)

    if moved > 0:
        await ctx.send(f"✅ {moved} members have been successfully moved to your voice channel.", reference=ctx.message, mention_author=False)
    else:
        await ctx.send("❗ No members were found in any voice channel or an error occurred.", reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        await ctx.send("📜 No roles have permission to use the bot.", reference=ctx.message, mention_author=False)
    else:
        roles_list = "\n".join([f"🔹 {role.name} (ID: {role.id})" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        await ctx.send(f"📜 Roles allowed to use the bot:\n{roles_list}", reference=ctx.message, mention_author=False)

@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send("❌ You do not have permission to execute this command.", reference=ctx.message, mention_author=False)
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            await ctx.send(f"✅ Role **{role.name}** has been granted permission to use the bot.", reference=ctx.message, mention_author=False)
        else:
            await ctx.send(f"ℹ️ Role **{role.name}** already has permission.", reference=ctx.message, mention_author=False)
    else:
        await ctx.send(f"❗ Role '{role_name_or_id}' not found.", reference=ctx.message, mention_author=False)

@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send("❌ You do not have permission to execute this command.", reference=ctx.message, mention_author=False)
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            await ctx.send(f"✅ Role **{role.name}** has been removed from allowed list.", reference=ctx.message, mention_author=False)
        else:
            await ctx.send(f"ℹ️ Role **{role.name}** did not have permission.", reference=ctx.message, mention_author=False)
    else:
        await ctx.send(f"❗ Role '{role_name_or_id}' not found.", reference=ctx.message, mention_author=False)

keep_alive()
bot.run(os.getenv('TOKEN'))
