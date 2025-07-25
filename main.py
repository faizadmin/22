from datetime import datetime, timedelta
import os
import discord
from discord.ext import commands
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

special_user_id = 839803217192812554  # Developer ID
access_enabled = False
allowed_roles = []

sniped_messages = {}  # channel_id: list of deleted messages (up to 5 per channel)

# --------- Timezone Helper ---------
def get_ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def format_ist(dt):
    return (dt + timedelta(hours=5, minutes=30)).strftime('%Y-%m-%d %H:%M:%S IST')

# --------- Embed Helpers ---------
def create_embed(text, author):
    ist_time = format_ist(datetime.utcnow())
    embed = discord.Embed(
        description=f"**{text}**",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f" | Requested by {author.name}", icon_url=author.avatar.url if author.avatar else None)
    return embed

def has_bot_access(member):
    print(f"[ACCESS CHECK] User: {member.name} ({member.id}) | Access Enabled: {access_enabled}")
    if access_enabled:
        return any(role.id in allowed_roles for role in member.roles) or member.id == special_user_id
    else:
        return member.id == special_user_id

def get_snipe_embed(ctx, index):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) <= index:
        return create_embed("❌ No deleted message found at that position.", ctx.author)

    data = sniped_messages[channel_id][index]
    ist_time = format_ist(datetime.utcnow())
    embed = discord.Embed(
        title=f"🕵️ Deleted Message #{index + 1}",
        description=f"[{data['author'].name}](https://discord.com/users/{data['author'].id}) said:\n```{data['content']}```",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🕒 Sent At", value=format_ist(data["sent_at"]), inline=True)
    embed.add_field(name="❌ Deleted At", value=format_ist(data["deleted_at"]), inline=True)
    embed.set_footer(text=f" | Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    return embed

def get_lastx_embed(ctx, count):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) < count:
        return create_embed("❌ Not enough deleted messages found.", ctx.author)

    lines = []
    for i in range(count):
        data = sniped_messages[channel_id][i]
        lines.append(
            f"**🕵️ Deleted Message #{i + 1}**\n"
            f"[{data['author'].name}](https://discord.com/users/{data['author'].id}) said:\n"
            f"```{data['content']}```\n"
            f"Sent At: {format_ist(data['sent_at'])}\n"
            f"Deleted At: {format_ist(data['deleted_at'])}\n"
        )
    ist_time = format_ist(datetime.utcnow())
    embed = discord.Embed(description="\n".join(lines), color=discord.Color.orange(), timestamp=datetime.utcnow())
    embed.set_footer(text=f"{ist_time} | Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    return embed

# --------- Events ---------
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

# --------- Access Control ---------
@bot.command()
async def idcheck(ctx):
    await ctx.send(f"Your ID: `{ctx.author.id}`")

@bot.command()
async def allon(ctx):
    global access_enabled
    if ctx.author.id == special_user_id:
        access_enabled = True
        await ctx.send(embed=create_embed("✅ Bot access enabled for allowed roles.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed(f"❌ Only developer can run this command. Your ID: `{ctx.author.id}`", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    global access_enabled
    if ctx.author.id == special_user_id:
        access_enabled = False
        await ctx.send(embed=create_embed("🔒 Bot access restricted to developer only.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ Only developer can run this command.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permadd(ctx, role: discord.Role):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ Only developer can run this command.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if role.id not in allowed_roles:
        allowed_roles.append(role.id)
        await ctx.send(embed=create_embed(f"✅ Role '{role.name}' added to allowed list.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed(f"ℹ️ Role '{role.name}' already in allowed list.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permdl(ctx, role: discord.Role):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ Only developer can run this command.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if role.id in allowed_roles:
        allowed_roles.remove(role.id)
        await ctx.send(embed=create_embed(f"✅ Role '{role.name}' removed from allowed list.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed(f"ℹ️ Role '{role.name}' not in allowed list.", ctx.author), reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if ctx.author.id != special_user_id:
        await ctx.send(embed=create_embed("❌ Only developer can run this command.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if not allowed_roles:
        await ctx.send(embed=create_embed("📃 No roles are currently allowed.", ctx.author), reference=ctx.message, mention_author=False)
        return
    roles = [f"🔹 {discord.utils.get(ctx.guild.roles, id=rid).name} (ID: {rid})" for rid in allowed_roles if discord.utils.get(ctx.guild.roles, id=rid)]
    await ctx.send(embed=create_embed("📃 Allowed Roles:\n" + "\n".join(roles), ctx.author), reference=ctx.message, mention_author=False)

# --------- Voice Commands ---------
@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use this command.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if not ctx.author.voice:
        await ctx.send(embed=create_embed("❗ Join a VC first.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if not member or not member.voice:
        await ctx.send(embed=create_embed("❗ Mention a user who is in VC.", ctx.author), reference=ctx.message, mention_author=False)
        return
    destination = ctx.author.voice.channel
    if not destination.permissions_for(ctx.author).connect:
        await ctx.send(embed=create_embed("❌ You don't have permission to join your own VC.", ctx.author), reference=ctx.message, mention_author=False)
        return
    await member.move_to(destination)
    await ctx.send(embed=create_embed(f"✅ Moved {member.name} to your VC.", ctx.author), reference=ctx.message, mention_author=False)


@bot.command()
async def move(ctx, member: discord.Member = None, vc_id: int = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if not member or vc_id is None:
        await ctx.send(embed=create_embed("❗ Usage: &move @user VC_ID", ctx.author), reference=ctx.message, mention_author=False)
        return
    vc = discord.utils.get(ctx.guild.voice_channels, id=vc_id)
    if vc:
        if not vc.permissions_for(ctx.author).connect:
            await ctx.send(embed=create_embed("❌ You don't have permission to join that VC.", ctx.author), reference=ctx.message, mention_author=False)
            return
        await member.move_to(vc)
        await ctx.send(embed=create_embed(f"✅ Moved {member.name} to VC ID {vc_id}.", ctx.author), reference=ctx.message, mention_author=False)
    else:
        await ctx.send(embed=create_embed("❌ VC not found with that ID.", ctx.author), reference=ctx.message, mention_author=False)


@bot.command()
async def moveall(ctx):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission.", ctx.author), reference=ctx.message, mention_author=False)
        return
    if not ctx.author.voice:
        await ctx.send(embed=create_embed("❗ Join a VC first.", ctx.author), reference=ctx.message, mention_author=False)
        return

    destination = ctx.author.voice.channel
    if not destination.permissions_for(ctx.author).connect:
        await ctx.send(embed=create_embed("❌ You don't have permission to join your own VC.", ctx.author), reference=ctx.message, mention_author=False)
        return

    moved = 0
    for vc in ctx.guild.voice_channels:
        for member in vc.members:
            if member != ctx.author and member.voice:
                try:
                    await member.move_to(destination)
                    moved += 1
                except discord.Forbidden:
                    await ctx.send(embed=create_embed(f"❌ Can't move {member.name} (missing permissions).", ctx.author), reference=ctx.message, mention_author=False)

    await ctx.send(embed=create_embed(f"✅ Moved {moved} member(s) to your VC.", ctx.author), reference=ctx.message, mention_author=False)


# --------- Snipe and LastX Commands ---------
@bot.command()
async def snipe(ctx):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ Access denied.", ctx.author), reference=ctx.message, mention_author=False)
        return
    await ctx.send(embed=get_snipe_embed(ctx, 0), reference=ctx.message, mention_author=False)

# Register last1 to last5 commands
for i in range(1, 6):
    async def lastx(ctx, i=i):
        if not has_bot_access(ctx.author):
            await ctx.send(embed=create_embed("❌ Access denied.", ctx.author), reference=ctx.message, mention_author=False)
            return
        await ctx.send(embed=get_lastx_embed(ctx, i), reference=ctx.message, mention_author=False)
    bot.command(name=f'last{i}')(lastx)

# --------- Start Bot ---------
keep_alive()
bot.run(os.getenv("TOKEN"))
    
