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

special_user_id = 1176678272579424258
access_enabled = False
allowed_roles = []

sniped_messages = {}  # channel_id: list of deleted messages (up to 5 per channel)

# Helper to convert UTC to IST
def utc_to_ist(utc_dt):
    return utc_dt + timedelta(hours=5, minutes=30)

def create_embed(text, author):
    embed = discord.Embed(
        description=f"**{text}**",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Requested by {author.name}", icon_url=author.avatar.url if author.avatar else None)
    return embed

def has_bot_access(member):
    return member.id == special_user_id or (access_enabled and any(role.id in allowed_roles for role in member.roles))

def get_snipe_embed(ctx, index):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) <= index:
        return create_embed("❌ No deleted message found at that position.", ctx.author)

    data = sniped_messages[channel_id][index]
    author = data["author"]
    content = data["content"]
    sent_at = utc_to_ist(data["sent_at"])
    deleted_at = utc_to_ist(data["deleted_at"])

    embed = discord.Embed(
        title=f"🕵️ Deleted Message #{index + 1}",
        description=f"**[{author.name}](https://discord.com/users/{author.id})** said:\n```{content}```",
        color=discord.Color.orange()
    )
    embed.add_field(name="🕒 Sent At", value=sent_at.strftime('%Y-%m-%d %H:%M:%S IST'), inline=True)
    embed.add_field(name="❌ Deleted At", value=deleted_at.strftime('%Y-%m-%d %H:%M:%S IST'), inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    return embed

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    channel_id = message.channel.id
    if channel_id not in sniped_messages:
        sniped_messages[channel_id] = []

    sniped_messages[channel_id].insert(0, {
        "author": message.author,
        "content": message.content,
        "sent_at": message.created_at,
        "deleted_at": datetime.utcnow()
    })

    if len(sniped_messages[channel_id]) > 5:
        sniped_messages[channel_id].pop()

# ====== Voice Commands ======
@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not ctx.author.voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not member or not member.voice:
        await ctx.send(embed=create_embed("❗ Mention someone connected to a VC.", ctx.author), reference=ctx.message, mention_author=False)
        return

    await member.move_to(ctx.author.voice.channel)
    await ctx.send(embed=create_embed(f"✅ Moved **{member.name}** to your VC.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def move(ctx, member: discord.Member, vc_id: int):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author), reference=ctx.message, mention_author=False)
        return

    vc = discord.utils.get(ctx.guild.voice_channels, id=vc_id)
    if not vc:
        await ctx.send(embed=create_embed("❗ Invalid VC ID.", ctx.author), reference=ctx.message, mention_author=False)
        return

    await member.move_to(vc)
    await ctx.send(embed=create_embed(f"✅ Moved **{member.name}** to VC ID: `{vc.id}`", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def moveall(ctx):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not ctx.author.voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel.", ctx.author), reference=ctx.message, mention_author=False)
        return

    count = 0
    for member in ctx.guild.members:
        if member.voice and member.voice.channel.id != ctx.author.voice.channel.id:
            try:
                await member.move_to(ctx.author.voice.channel)
                count += 1
            except:
                pass

    await ctx.send(embed=create_embed(f"✅ Moved {count} members.", ctx.author), reference=ctx.message, mention_author=False)

# ====== Snipe & LastX Commands ======
@bot.command()
async def snipe(ctx):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ Access denied.", ctx.author), reference=ctx.message, mention_author=False)
        return
    await ctx.send(embed=get_snipe_embed(ctx, 0), reference=ctx.message, mention_author=False)

@bot.command()
async def last1(ctx):
    embed = discord.Embed(title="🕵️ Last Deleted Message", color=discord.Color.orange(), timestamp=datetime.utcnow())
    data = sniped_messages.get(ctx.channel.id, [])
    if len(data) > 0:
        msg = data[0]
        embed.add_field(name=f"**[{msg['author'].name}](https://discord.com/users/{msg['author'].id}) said:**", value=f"```{msg['content']}```", inline=False)
        embed.add_field(name="🕒 Sent At", value=msg["sent_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
        embed.add_field(name="❌ Deleted At", value=msg["deleted_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
    else:
        embed.description = "❌ No deleted messages found."

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last2(ctx):
    embed = discord.Embed(title="🕵️ Last 2 Deleted Messages", color=discord.Color.orange(), timestamp=datetime.utcnow())
    data = sniped_messages.get(ctx.channel.id, [])
    if len(data) >= 2:
        for i in range(2):
            msg = data[i]
            embed.add_field(name=f"**[{msg['author'].name}](https://discord.com/users/{msg['author'].id}) said:**", value=f"```{msg['content']}```", inline=False)
            embed.add_field(name="🕒 Sent At", value=msg["sent_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
            embed.add_field(name="❌ Deleted At", value=msg["deleted_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
    else:
        embed.description = "❌ Less than 2 deleted messages found."

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last3(ctx):
    embed = discord.Embed(title="🕵️ Last 3 Deleted Messages", color=discord.Color.orange(), timestamp=datetime.utcnow())
    data = sniped_messages.get(ctx.channel.id, [])
    if len(data) >= 3:
        for i in range(3):
            msg = data[i]
            embed.add_field(name=f"**[{msg['author'].name}](https://discord.com/users/{msg['author'].id}) said:**", value=f"```{msg['content']}```", inline=False)
            embed.add_field(name="🕒 Sent At", value=msg["sent_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
            embed.add_field(name="❌ Deleted At", value=msg["deleted_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
    else:
        embed.description = "❌ Less than 3 deleted messages found."

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last4(ctx):
    embed = discord.Embed(title="🕵️ Last 4 Deleted Messages", color=discord.Color.orange(), timestamp=datetime.utcnow())
    data = sniped_messages.get(ctx.channel.id, [])
    if len(data) >= 4:
        for i in range(4):
            msg = data[i]
            embed.add_field(name=f"**[{msg['author'].name}](https://discord.com/users/{msg['author'].id}) said:**", value=f"```{msg['content']}```", inline=False)
            embed.add_field(name="🕒 Sent At", value=msg["sent_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
            embed.add_field(name="❌ Deleted At", value=msg["deleted_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
    else:
        embed.description = "❌ Less than 4 deleted messages found."

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last5(ctx):
    embed = discord.Embed(title="🕵️ Last 5 Deleted Messages", color=discord.Color.orange(), timestamp=datetime.utcnow())
    data = sniped_messages.get(ctx.channel.id, [])
    if len(data) >= 5:
        for i in range(5):
            msg = data[i]
            embed.add_field(name=f"**[{msg['author'].name}](https://discord.com/users/{msg['author'].id}) said:**", value=f"```{msg['content']}```", inline=False)
            embed.add_field(name="🕒 Sent At", value=msg["sent_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
            embed.add_field(name="❌ Deleted At", value=msg["deleted_at"].strftime('%Y-%m-%d %H:%M:%S IST'), inline=False)
    else:
        embed.description = "❌ Less than 5 deleted messages found."

    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

# ====== Access Control ======
@bot.command()
async def allon(ctx):
    global access_enabled
    if ctx.author.id == special_user_id:
        access_enabled = True
        await ctx.send(embed=create_embed("✅ Access enabled for allowed roles.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    global access_enabled
    if ctx.author.id == special_user_id:
        access_enabled = False
        await ctx.send(embed=create_embed("🔒 Access restricted to developer only.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permadd(ctx, role_id: int):
    if ctx.author.id != special_user_id:
        return
    if role_id not in allowed_roles:
        allowed_roles.append(role_id)
    await ctx.send(embed=create_embed(f"✅ Role ID {role_id} added to access list.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permdel(ctx, role_id: int):
    if ctx.author.id != special_user_id:
        return
    if role_id in allowed_roles:
        allowed_roles.remove(role_id)
    await ctx.send(embed=create_embed(f"🗑️ Role ID {role_id} removed from access list.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if ctx.author.id != special_user_id:
        return
    text = "\n".join([f"🔹 {rid}" for rid in allowed_roles]) or "❌ No roles allowed."
    await ctx.send(embed=create_embed(f"Allowed Roles:\n{text}", ctx.author), reference=ctx.message, mention_author=False)

# ====== Run Bot ======
keep_alive()
bot.run(os.getenv("TOKEN"))
