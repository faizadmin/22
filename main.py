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

special_user_id = 1176678272579424258
access_enabled = False
allowed_roles = []

def create_embed(text, author_name, author_avatar_url):
    embed = discord.Embed(
        description=text,
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(
        text=f"Requested by {author_name} | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        icon_url=author_avatar_url
    )
    return embed

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        embed = create_embed("✅ Bot access has been successfully enabled for **everyone**!\n\n🤖 Developed by **Faiz**.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        embed = create_embed("🔒 Bot access has been restricted to **authorized users only**.\n\n🛡️ Authorized person: **Faiz** (Bot Developer)", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        embed = create_embed("❌ Bot access is currently restricted to authorized users only.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        embed = create_embed("🔊 You must be connected to a voice channel first.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if member is None:
        embed = create_embed("❗ Please mention a member to pull. Example: `&pull @John`", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if not member.voice:
        embed = create_embed(f"❗ {member.name} is not connected to any voice channel.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    try:
        await member.move_to(author_voice.channel)
        embed = create_embed(f"✅ {member.name} has been moved to your voice channel by {ctx.author.name}.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    except discord.Forbidden:
        embed = create_embed("🚫 Bot does not have permission to move members.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    except Exception as e:
        embed = create_embed(f"⚠️ An error occurred: {e}", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        embed = create_embed("❌ Bot access is currently restricted to authorized users only.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        embed = create_embed("🔊 You must be connected to a voice channel first.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                embed = create_embed(f"🚫 Bot does not have permission to move {member.name}.", ctx.author.name, ctx.author.avatar.url)
                await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            except Exception as e:
                embed = create_embed(f"⚠️ An error occurred: {e}", ctx.author.name, ctx.author.avatar.url)
                await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    if moved > 0:
        embed = create_embed(f"✅ {moved} members have been successfully moved to your voice channel.", ctx.author.name, ctx.author.avatar.url)
    else:
        embed = create_embed("❗ No members were found in any voice channel or an error occurred.", ctx.author.name, ctx.author.avatar.url)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        embed = create_embed("📜 No roles have permission to use the bot.", ctx.author.name, ctx.author.avatar.url)
    else:
        roles_list = "\n".join([f"🔹 {role.name} (ID: {role.id})" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        embed = create_embed(f"📜 Roles allowed to use the bot:\n{roles_list}", ctx.author.name, ctx.author.avatar.url)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            embed = create_embed(f"✅ Role **{role.name}** has been granted permission to use the bot.", ctx.author.name, ctx.author.avatar.url)
        else:
            embed = create_embed(f"ℹ️ Role **{role.name}** already has permission.", ctx.author.name, ctx.author.avatar.url)
    else:
        embed = create_embed(f"❗ Role '{role_name_or_id}' not found.", ctx.author.name, ctx.author.avatar.url)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name, ctx.author.avatar.url)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            embed = create_embed(f"✅ Role **{role.name}** has been removed from allowed list.", ctx.author.name, ctx.author.avatar.url)
        else:
            embed = create_embed(f"ℹ️ Role **{role.name}** did not have permission.", ctx.author.name, ctx.author.avatar.url)
    else:
        embed = create_embed(f"❗ Role '{role_name_or_id}' not found.", ctx.author.name, ctx.author.avatar.url)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

keep_alive()
bot.run(os.getenv('TOKEN'))
