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

def create_embed(text, author_name):
    embed = discord.Embed(
        description=text,
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()  # Keep the timestamp here only
    )
    embed.set_footer(text=f"By {author_name}")
    return embed

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.command()
async def allon(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = True
        embed = create_embed("✅ Bot access has been successfully enabled for **everyone**!\n\n🤖 Developed by **Faiz**.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def alloff(ctx):
    if ctx.author.id == special_user_id:
        global access_enabled
        access_enabled = False
        embed = create_embed("🔒 Bot access has been restricted to **authorized users only**.\n\n🛡️ Authorized person: **Faiz** (Bot Developer)", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    else:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def pull(ctx, member: discord.Member = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        embed = create_embed("❌ Bot access is currently restricted to authorized users only.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        embed = create_embed("🔊 You must be connected to a voice channel first.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if member is None:
        embed = create_embed("❗ Please mention a member to pull. Example: `&pull @John`", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if not member.voice:
        embed = create_embed(f"❗ {member.name} is not connected to any voice channel.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    # Check if the author has permission to join the member's current voice channel
    if member.voice.channel.id != author_voice.channel.id:
        if not author_voice.channel.permissions_for(ctx.author).connect:
            embed = create_embed("❗ You do not have permission to join this channel and move members.", ctx.author.name)
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            return

    try:
        await member.move_to(author_voice.channel)
        embed = create_embed(f"✅ {member.name} has been moved to your voice channel by {ctx.author.name}.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    except discord.Forbidden:
        embed = create_embed("🚫 Bot does not have permission to move members.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    except Exception as e:
        embed = create_embed(f"⚠️ An error occurred: {e}", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def moveall(ctx):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        embed = create_embed("❌ Bot access is currently restricted to authorized users only.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    author_voice = ctx.author.voice
    if not author_voice:
        embed = create_embed("🔊 You must be connected to a voice channel first.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    moved = 0
    for member in ctx.guild.members:
        if member.voice:
            # Check if the author has permission to join the member's current voice channel
            if member.voice.channel.id != author_voice.channel.id:
                if not author_voice.channel.permissions_for(ctx.author).connect:
                    embed = create_embed(f"❗ You do not have permission to join {member.name}'s channel.", ctx.author.name)
                    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
                    continue

            try:
                await member.move_to(author_voice.channel)
                moved += 1
            except discord.Forbidden:
                embed = create_embed(f"🚫 Bot does not have permission to move {member.name}.", ctx.author.name)
                await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            except Exception as e:
                embed = create_embed(f"⚠️ An error occurred: {e}", ctx.author.name)
                await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

    if moved > 0:
        embed = create_embed(f"✅ {moved} members have been successfully moved to your voice channel.", ctx.author.name)
    else:
        embed = create_embed("❗ No members were found in any voice channel or an error occurred.", ctx.author.name)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def move(ctx, member: discord.Member = None, channel_name_or_id: str = None):
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        embed = create_embed("❌ Bot access is currently restricted to authorized users only.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if not member:
        embed = create_embed("❗ Please mention a member to move. Example: `&move @John #VoiceChannelName`", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if not channel_name_or_id:
        embed = create_embed("❗ Please provide the voice channel name or ID to move the member. Example: `&move @John #VoiceChannelName`", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    # Find the channel by name or ID
    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name_or_id)
    if not channel:
        try:
            # Attempt to convert to an ID if the name doesn't work
            channel_id = int(channel_name_or_id)
            channel = discord.utils.get(ctx.guild.voice_channels, id=channel_id)
        except ValueError:
            pass

    if not channel:
        embed = create_embed(f"❗ No voice channel found with the name or ID '{channel_name_or_id}'.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    if not member.voice:
        embed = create_embed(f"❗ {member.name} is not connected to any voice channel.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    # Check if the author has permission to join the target voice channel
    if not channel.permissions_for(ctx.author).connect:
        embed = create_embed(f"❗ You do not have permission to join the target voice channel '{channel.name}'.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    try:
        # Move the member to the specified channel
        await member.move_to(channel)
        embed = create_embed(f"✅ {member.name} has been moved to the voice channel '{channel.name}'.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    except discord.Forbidden:
        embed = create_embed("🚫 Bot does not have permission to move members.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
    except Exception as e:
        embed = create_embed(f"⚠️ An error occurred: {e}", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

keep_alive()
bot.run(os.getenv('TOKEN'))
