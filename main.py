import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='&', intents=intents)

# IDs
owner_id = 123456789012345678  # <-- Apna OWNER ID daal yaha
perm_roles = [111111111111111111, 222222222222222222]  # <-- IDs of roles allowed to use when 'allon' enabled

# Bot Permission Toggle
bot_permission = False  # Initially off

def create_embed(message, author_name):
    embed = discord.Embed(description=message, color=discord.Color.blurple())
    embed.set_footer(text=f"Requested by {author_name}")
    return embed

def has_bot_access(member):
    global bot_permission
    if member.id == owner_id:
        return True
    if bot_permission:
        return any(role.id in perm_roles for role in member.roles)
    return False

@bot.command()
async def allon(ctx):
    global bot_permission
    if ctx.author.id == owner_id:
        bot_permission = True
        await ctx.send(embed=create_embed("✅ Bot access granted to selected roles.", ctx.author.name))
    else:
        await ctx.send(embed=create_embed("❌ Only the owner can use this command.", ctx.author.name))

@bot.command()
async def alloff(ctx):
    global bot_permission
    if ctx.author.id == owner_id:
        bot_permission = False
        await ctx.send(embed=create_embed("🚫 Bot access disabled for everyone except owner.", ctx.author.name))
    else:
        await ctx.send(embed=create_embed("❌ Only the owner can use this command.", ctx.author.name))

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author.name))
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel first.", ctx.author.name))
        return

    if member is None:
        await ctx.send(embed=create_embed("❗ Please mention a member to pull. Example: `&pull @John`", ctx.author.name))
        return

    if not member.voice:
        await ctx.send(embed=create_embed(f"❗ {member.name} is not connected to any voice channel.", ctx.author.name))
        return

    if not author_voice.channel.permissions_for(ctx.author).connect:
        await ctx.send(embed=create_embed("🚫 You don't have permission to join your own voice channel.", ctx.author.name))
        return

    if member.voice.channel.id == author_voice.channel.id:
        await ctx.send(embed=create_embed(f"😂 Tu thoda sa *** hai kya? Yeh already is VC pe hai...", ctx.author.name))
        return

    try:
        await member.move_to(author_voice.channel)
        await ctx.send(embed=create_embed(f"✅ {member.name} has been moved to your voice channel by {ctx.author.name}.", ctx.author.name))
    except discord.Forbidden:
        await ctx.send(embed=create_embed("🚫 Bot does not have permission to move members.", ctx.author.name))
    except Exception as e:
        await ctx.send(embed=create_embed(f"⚠️ An error occurred: {e}", ctx.author.name))

@bot.command()
async def move(ctx, member: discord.Member = None, channel_name_or_id: str = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author.name))
        return

    if not member or not channel_name_or_id:
        await ctx.send(embed=create_embed("❗ Please mention a member and channel. Example: `&move @John VCName`", ctx.author.name))
        return

    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name_or_id)
    if not channel:
        try:
            channel_id = int(channel_name_or_id)
            channel = discord.utils.get(ctx.guild.voice_channels, id=channel_id)
        except ValueError:
            pass

    if not channel:
        await ctx.send(embed=create_embed(f"❗ No voice channel found with the name or ID '{channel_name_or_id}'.", ctx.author.name))
        return

    if not member.voice:
        await ctx.send(embed=create_embed(f"❗ {member.name} is not connected to any voice channel.", ctx.author.name))
        return

    if not channel.permissions_for(ctx.author).connect:
        await ctx.send(embed=create_embed("🚫 You don't have permission to join the target voice channel.", ctx.author.name))
        return

    if member.voice.channel.id == channel.id:
        await ctx.send(embed=create_embed(f"😂 Tu thoda sa *** hai kya? Yeh already is VC pe hai...", ctx.author.name))
        return

    try:
        await member.move_to(channel)
        await ctx.send(embed=create_embed(f"✅ {member.name} has been moved to the voice channel '{channel.name}'.", ctx.author.name))
    except discord.Forbidden:
        await ctx.send(embed=create_embed("🚫 Bot does not have permission to move members.", ctx.author.name))
    except Exception as e:
        await ctx.send(embed=create_embed(f"⚠️ An error occurred: {e}", ctx.author.name))

@bot.command()
async def moveall(ctx, target_channel: discord.VoiceChannel = None):
    if not has_bot_access(ctx.author):
        await ctx.send(embed=create_embed("❌ You do not have permission to use the bot.", ctx.author.name))
        return

    if not ctx.author.voice:
        await ctx.send(embed=create_embed("🔊 You must be connected to a voice channel first.", ctx.author.name))
        return

    source_channel = ctx.author.voice.channel

    if target_channel is None:
        await ctx.send(embed=create_embed("❗ Please mention the target voice channel. Example: `&moveall #VCName`", ctx.author.name))
        return

    if not target_channel.permissions_for(ctx.author).connect:
        await ctx.send(embed=create_embed("🚫 You don't have permission to join the target voice channel.", ctx.author.name))
        return

    moved_members = 0
    for member in source_channel.members:
        if member.bot:
            continue
        if member.voice.channel.id == target_channel.id:
            continue  # Already in target VC, skip
        try:
            await member.move_to(target_channel)
            moved_members += 1
        except:
            continue

    await ctx.send(embed=create_embed(f"✅ Successfully moved {moved_members} members.", ctx.author.name))
    
