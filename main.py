import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

special_user_id = 1176678272579424258  # Developer ID
access_enabled = False
allowed_roles = []

sniped_messages = {}  # channel_id: list of deleted messages (up to 5 per channel)

# --------- Embed Helper ---------
def create_embed(text, author):
    # Convert UTC to IST (UTC + 5:30)
    current_time = datetime.utcnow() + timedelta(hours=5, minutes=30)
    
    embed = discord.Embed(
        description=f"**{text}**",
        color=discord.Color.blue(),
        timestamp=current_time
    )
    embed.set_footer(
        text=f"Requested By {author.name}",
        icon_url=author.avatar.url if author.avatar else None
    )
    return embed

def get_snipe_embed(ctx, index):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) <= index:
        return create_embed("❌ No deleted message found at that position.", ctx.author)

    data = sniped_messages[channel_id][index]
    
    # Convert UTC to IST (UTC + 5:30)
    sent_at = data["sent_at"] + timedelta(hours=5, minutes=30)
    deleted_at = data["deleted_at"] + timedelta(hours=5, minutes=30)
    
    embed = discord.Embed(
        title=f"🕵️ Deleted Message #{index + 1}",
        description=f"**{data['author']}** said:\n```{data['content']}```",
        color=discord.Color.orange(),
        timestamp=deleted_at
    )
    embed.add_field(name="🕒 Sent At", value=sent_at.strftime('%Y-%m-%d %H:%M:%S IST'), inline=True)
    embed.add_field(name="❌ Deleted At", value=deleted_at.strftime('%Y-%m-%d %H:%M:%S IST'), inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    return embed

# --------- Voice Commands ---------
@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        embed = create_embed("✅ Bot access has been enabled for allowed roles only.\n\n🤖 Developed by Faiz.", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ You do not have permission to execute this command.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        embed = create_embed("🔒 Bot access is now restricted to developer only.\n\n🛡️ Authorized: Faiz", ctx.author)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ You do not have permission to execute this command.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author), reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel first.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if member is None:
        await ctx.send(embed=create_embed("❗ Please mention a member to pull. Example: `&pull @John`", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not member.voice:
        await ctx.send(embed=create_embed(f"❗ {member.name} is not connected to any voice channel.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if member.voice.channel.id == author_voice.channel.id:
        await ctx.send(embed=create_embed(f"🧠 Abe tu Thoda sa ******* Hai kya? {member.name} already tumhare VC me hai...", ctx.author), reference=ctx.message, mention_author=False)
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(embed=create_embed(f"✅ {member.name} has been moved to your voice channel by {ctx.author.name}.", ctx.author), reference=ctx.message, mention_author=False)
    except discord.Forbidden:
        await ctx.send(embed=create_embed("🚫 Bot does not have permission to move members.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def moveall(ctx):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author), reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel first.", ctx.author), reference=ctx.message, mention_author=False)
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice and member.voice.channel.id != author_voice.channel.id:
            try:
                if author_voice.channel.permissions_for(ctx.author).connect:
                    await member.move_to(author_voice.channel)
                    moved += 1
            except:
                pass

    if moved > 0:
        await ctx.send(embed=create_embed(f"✅ {moved} members moved to your voice channel.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❗ No members moved or already in your voice channel.", ctx.author), reference=ctx.message, mention_author=False)

# --------- Role Permissions ---------
@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ You do not have permission to execute this command.", ctx.author), reference=ctx.message, mention_author=False)
        return

    try:
        role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    except ValueError:
        role = None

    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            embed = create_embed(f"✅ Role **{role.name}** has been granted permission to use the bot.", ctx.author)
        else:
            embed = create_embed(f"ℹ️ Role **{role.name}** already has permission.", ctx.author)
    else:
        embed = create_embed(f"❗ Role '{role_name_or_id}' not found.", ctx.author)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permdel(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ You do not have permission to execute this command.", ctx.author), reference=ctx.message, mention_author=False)
        return

    try:
        role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    except ValueError:
        role = None

    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            embed = create_embed(f"✅ Role **{role.name}** has been removed from allowed list.", ctx.author)
        else:
            embed = create_embed(f"ℹ️ Role **{role.name}** did not have permission.", ctx.author)
    else:
        embed = create_embed(f"❗ Role '{role_name_or_id}' not found.", ctx.author)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ You do not have permission to execute this command.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not allowed_roles:
        embed = create_embed("📜 No roles have permission to use the bot.", ctx.author)
    else:
        roles_list = "\n".join([f"🔹 {role.name} (ID: {role.id})" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        embed = create_embed(f"📜 Roles allowed to use the bot:\n{roles_list}", ctx.author)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

# --------- Snipe & Purge Commands ---------
@bot.command()
async def snipe(ctx):
    await ctx.send(embed=get_snipe_embed(ctx, 0), reference=ctx.message, mention_author=False)

@bot.command()
async def last1(ctx):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) == 0:
        await ctx.send(embed=create_embed("❌ No deleted messages found.", ctx.author), reference=ctx.message, mention_author=False)
        return
    
    # Convert UTC to IST (UTC + 5:30)
    data = sniped_messages[channel_id][0]
    sent_at = data['sent_at'] + timedelta(hours=5, minutes=30)
    deleted_at = data['deleted_at'] + timedelta(hours=5, minutes=30)

    # Create a combined embed with the last 1 deleted message
    embed = discord.Embed(
        title="🕵️ Deleted Message #1",
        color=discord.Color.orange(),
        timestamp=deleted_at
    )
    
    embed.add_field(
        name=f"🕵️ Deleted Message #1",
        value=f"**{data['author']}** said:\n```{data['content']}```\n"
              f"🕒 Sent At: {sent_at.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
              f"❌ Deleted At: {deleted_at.strftime('%Y-%m-%d %H:%M:%S IST')}",
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last2(ctx):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) < 2:
        await ctx.send(embed=create_embed("❌ Less than 2 deleted messages found.", ctx.author), reference=ctx.message, mention_author=False)
        return
    
    # Convert UTC to IST (UTC + 5:30)
    embed = discord.Embed(
        title="🕵️ Deleted Messages #1 and #2",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow() + timedelta(hours=5, minutes=30)
    )
    
    for i in range(2):
        data = sniped_messages[channel_id][i]
        sent_at = data['sent_at'] + timedelta(hours=5, minutes=30)
        deleted_at = data['deleted_at'] + timedelta(hours=5, minutes=30)
        
        embed.add_field(
            name=f"🕵️ Deleted Message #{i + 1}",
            value=f"**{data['author']}** said:\n```{data['content']}```\n"
                  f"🕒 Sent At: {sent_at.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
                  f"❌ Deleted At: {deleted_at.strftime('%Y-%m-%d %H:%M:%S IST')}",
            inline=False
        )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last3(ctx):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) < 3:
        await ctx.send(embed=create_embed("❌ Less than 3 deleted messages found.", ctx.author), reference=ctx.message, mention_author=False)
        return
    
    # Convert UTC to IST (UTC + 5:30)
    embed = discord.Embed(
        title="🕵️ Deleted Messages #1, #2, and #3",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow() + timedelta(hours=5, minutes=30)
    )
    
    for i in range(3):
        data = sniped_messages[channel_id][i]
        sent_at = data['sent_at'] + timedelta(hours=5, minutes=30)
        deleted_at = data['deleted_at'] + timedelta(hours=5, minutes=30)
        
        embed.add_field(
            name=f"🕵️ Deleted Message #{i + 1}",
            value=f"**{data['author']}** said:\n```{data['content']}```\n"
                  f"🕒 Sent At: {sent_at.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
                  f"❌ Deleted At: {deleted_at.strftime('%Y-%m-%d %H:%M:%S IST')}",
            inline=False
        )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last4(ctx):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) < 4:
        await ctx.send(embed=create_embed("❌ Less than 4 deleted messages found.", ctx.author), reference=ctx.message, mention_author=False)
        return
    
    # Convert UTC to IST (UTC + 5:30)
    embed = discord.Embed(
        title="🕵️ Deleted Messages #1, #2, #3, and #4",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow() + timedelta(hours=5, minutes=30)
    )
    
    for i in range(4):
        data = sniped_messages[channel_id][i]
        sent_at = data['sent_at'] + timedelta(hours=5, minutes=30)
        deleted_at = data['deleted_at'] + timedelta(hours=5, minutes=30)
        
        embed.add_field(
            name=f"🕵️ Deleted Message #{i + 1}",
            value=f"**{data['author']}** said:\n```{data['content']}```\n"
                  f"🕒 Sent At: {sent_at.strftime('%Y-%m-%d %H:%M:%S IST')}\n"
                  f"❌ Deleted At: {deleted_at.strftime('%Y-%m-%d %H:%M:%S IST')}",
            inline=False
        )
    
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
