import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from datetime import datetime

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

# Embed creator function
def create_embed(text, author):
    embed = discord.Embed(
        description=text,
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    display_name = author.display_name
    embed.set_footer(
        text=f"Requested by {display_name} • 📅 {datetime.utcnow().strftime('%d/%m/%Y %I:%M %p')}",
        icon_url=author.display_avatar.url
    )
    return embed

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Command to allow everyone to use the bot
@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        embed = create_embed("✅ Bot access is now enabled for all users!", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        embed = create_embed("❌ Only authorized users can run this command.", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

# Command to restrict bot usage to only special user
@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        embed = create_embed(
            "🔒 Bot access has been restricted to authorized users only.\n👑 Authorized person: **Faiz** (Bot Developer)", 
            ctx.author
        )
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        embed = create_embed("❌ Only authorized users can run this command.", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

# Pull command
@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ You are not authorized to use this command.")
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("❌ You must be in a voice channel to use this command.")
        return

    if member is None:
        await ctx.send("❗ Please mention a member to pull. Example: `&pull @John`")
        return

    if not member.voice:
        await ctx.send(f"❗ {member.name} is not in a voice channel.")
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(f"✅ {member.name} has been moved to your voice channel.")
    except discord.Forbidden:
        await ctx.send("⚠️ Bot does not have permission to move members.")
    except Exception as e:
        await ctx.send(f"⚠️ An error occurred: {e}")

# Moveall command
@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("❌ You are not authorized to use this command.")
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("❌ You must be in a voice channel to use this command.")
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                await ctx.send(f"⚠️ Bot does not have permission to move {member.name}.")
            except Exception as e:
                await ctx.send(f"⚠️ An error occurred: {e}")

    if moved > 0:
        await ctx.send(f"✅ Successfully moved {moved} members to your voice channel.")
    else:
        await ctx.send("❗ No members were available in voice channels.")

# Command to list roles allowed to use the bot
@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        embed = create_embed("ℹ️ No roles have permission to use the bot.", ctx.author)
    else:
        roles_list = "\n".join([f"🔹 {role.name}" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        embed = create_embed(f"🔐 Roles with permission:\n{roles_list}", ctx.author)

    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

# Command to add a role to the allowed list
@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        embed = create_embed("❌ Only authorized users can modify permissions.", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            embed = create_embed(f"✅ Role '{role.name}' has been granted permission.", ctx.author)
        else:
            embed = create_embed(f"ℹ️ Role '{role.name}' already has permission.", ctx.author)
    else:
        embed = create_embed(f"❌ Role '{role_name_or_id}' not found.", ctx.author)

    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

# Command to remove a role from the allowed list
@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        embed = create_embed("❌ Only authorized users can modify permissions.", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            embed = create_embed(f"✅ Role '{role.name}' has been removed from permission list.", ctx.author)
        else:
            embed = create_embed(f"ℹ️ Role '{role.name}' did not have permission.", ctx.author)
    else:
        embed = create_embed(f"❌ Role '{role_name_or_id}' not found.", ctx.author)

    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

keep_alive()
bot.run(os.getenv('TOKEN'))
