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

special_user_id = 1176678272579424258  # Developer ID
access_enabled = False
allowed_roles = []

sniped_messages = {}  # channel_id: list of deleted messages (up to 5 per channel)

# --------- Embed Helper ---------
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

def get_snipe_embed(ctx, count):
    channel_id = ctx.channel.id
    if channel_id not in sniped_messages or len(sniped_messages[channel_id]) == 0:
        return create_embed("❌ No deleted messages found.", ctx.author)

    messages = sniped_messages[channel_id][:count]
    embed = discord.Embed(
        title=f"🕵️ Last {count} Deleted Messages",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    for idx, data in enumerate(messages):
        embed.add_field(
            name=f"Message #{idx + 1} from {data['author'].name}",
            value=f"```{data['content']}```",
            inline=False
        )
        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
    return embed

def has_bot_access(member):
    if access_enabled:
        return any(role.id in allowed_roles for role in member.roles)
    else:
        return member.id == special_user_id

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

# --------- Snipe Commands ---------
@bot.command()
async def snipe(ctx, count: int = 1):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use this command.", ctx.author), reference=ctx.message, mention_author=False)
        return

    embed = get_snipe_embed(ctx, count)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def last1(ctx):
    await snipe(ctx, count=1)

@bot.command()
async def last2(ctx):
    await snipe(ctx, count=2)

@bot.command()
async def last3(ctx):
    await snipe(ctx, count=3)

@bot.command()
async def last4(ctx):
    await snipe(ctx, count=4)

@bot.command()
async def last5(ctx):
    await snipe(ctx, count=5)

keep_alive()
bot.run(os.getenv("TOKEN"))
