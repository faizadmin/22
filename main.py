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

# --- Helpers ---
def ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def format_ist(dt):
    return (dt + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S IST')

def create_embed(text, author):
    embed = discord.Embed(
        description=f"**{text}**",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
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
    embed = discord.Embed(
        title=f"🕵️ Deleted Message #{index + 1}",
        description=f"**[{data['author'].name}](https://discord.com/users/{data['author'].id})** said:\n```{data['content']}```",
        color=discord.Color.orange(),
        timestamp=data["deleted_at"]
    )
    embed.add_field(name="🕒 Sent At", value=format_ist(data["sent_at"]), inline=True)
    embed.add_field(name="❌ Deleted At", value=format_ist(data["deleted_at"]), inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    return embed

def get_multi_snipe_embed(ctx, count):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) == 0:
        return create_embed("❌ No deleted messages found.", ctx.author)

    data_list = sniped_messages[channel_id][:count]
    description = ""
    for i, data in enumerate(data_list):
        description += f"🕵️ **Deleted Message #{i+1}**\n"
        description += f"**[{data['author'].name}](https://discord.com/users/{data['author'].id})** said:\n"
        description += f"```{data['content']}```\n"
        description += f"📅 Sent At: {format_ist(data['sent_at'])}\n"
        description += f"❌ Deleted At: {format_ist(data['deleted_at'])}\n\n"

    embed = discord.Embed(
        title=f"🧾 Last {len(data_list)} Deleted Messages",
        description=description,
        color=discord.Color.dark_purple(),
        timestamp=ist_now()
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    return embed

def has_bot_access(member):
    return member.id == special_user_id if not access_enabled else any(role.id in allowed_roles for role in member.roles)

# --- Events ---
@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    channel_id = message.channel.id
    sniped_messages.setdefault(channel_id, []).insert(0, {
        "author": message.author,
        "content": message.content,
        "sent_at": message.created_at,
        "deleted_at": datetime.utcnow()
    })
    if len(sniped_messages[channel_id]) > 5:
        sniped_messages[channel_id].pop()

# --- Commands ---
@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        await ctx.send(embed=create_embed("✅ Access enabled for allowed roles only.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ You do not have permission.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        await ctx.send(embed=create_embed("🔒 Access now restricted to developer only.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ You do not have permission.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not ctx.author.voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not member:
        await ctx.send(embed=create_embed("❗ Mention a member to pull.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not member.voice:
        await ctx.send(embed=create_embed(f"{member.name} is not in any VC.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if member.voice.channel == ctx.author.voice.channel:
        await ctx.send(embed=create_embed(f"🧠 {member.name} is already in your VC.", ctx.author), reference=ctx.message, mention_author=False)
        return

    try:
        await member.move_to(ctx.author.voice.channel)
        await ctx.send(embed=create_embed(f"✅ {member.name} moved to your VC.", ctx.author), reference=ctx.message, mention_author=False)
    except discord.Forbidden:
        await ctx.send(embed=create_embed("🚫 Bot lacks permission to move members.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def moveall(ctx):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not ctx.author.voice:
        await ctx.send(embed=create_embed("🔊 You must be in a VC.", ctx.author), reference=ctx.message, mention_author=False)
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice and member.voice.channel != ctx.author.voice.channel:
            try:
                await member.move_to(ctx.author.voice.channel)
                moved += 1
            except:
                continue

    await ctx.send(embed=create_embed(f"✅ Moved {moved} members.", ctx.author), reference=ctx.message, mention_author=False)

# Role management
@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ Not allowed.", ctx.author), reference=ctx.message, mention_author=False)
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            await ctx.send(embed=create_embed(f"✅ Role **{role.name}** added.", ctx.author), reference=ctx.message, mention_author=False)
        else:
            await ctx.send(embed=create_embed(f"ℹ️ Role already added.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ Role not found.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ Not allowed.", ctx.author), reference=ctx.message, mention_author=False)
        return

    if not allowed_roles:
        await ctx.send(embed=create_embed("📜 No roles added yet.", ctx.author), reference=ctx.message, mention_author=False)
        return

    role_names = [role.name for role in ctx.guild.roles if role.id in allowed_roles]
    await ctx.send(embed=create_embed("📜 Allowed Roles:\n" + "\n".join(f"🔹 {r}" for r in role_names), ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permdel(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ Not allowed.", ctx.author), reference=ctx.message, mention_author=False)
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role and role.id in allowed_roles:
        allowed_roles.remove(role.id)
        await ctx.send(embed=create_embed(f"✅ Removed role **{role.name}**.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ Role not found or not in allowed list.", ctx.author), reference=ctx.message, mention_author=False)

# Snipe and LastX Commands
@bot.command()
async def snipe(ctx): await ctx.send(embed=get_snipe_embed(ctx, 0), reference=ctx.message, mention_author=False)

@bot.command()
async def last1(ctx): await ctx.send(embed=get_multi_snipe_embed(ctx, 1), reference=ctx.message, mention_author=False)

@bot.command()
async def last2(ctx): await ctx.send(embed=get_multi_snipe_embed(ctx, 2), reference=ctx.message, mention_author=False)

@bot.command()
async def last3(ctx): await ctx.send(embed=get_multi_snipe_embed(ctx, 3), reference=ctx.message, mention_author=False)

@bot.command()
async def last4(ctx): await ctx.send(embed=get_multi_snipe_embed(ctx, 4), reference=ctx.message, mention_author=False)

@bot.command()
async def last5(ctx): await ctx.send(embed=get_multi_snipe_embed(ctx, 5), reference=ctx.message, mention_author=False)

# Run
keep_alive()
bot.run(os.getenv("TOKEN"))
