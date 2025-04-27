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
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text=f"Requested By {author_name} | ")
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

    if member.voice.channel.id == author_voice.channel.id:
        embed = create_embed("🤪 Are you mad? Check kar, yeh pehle se hi VC mein hai.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    try:
        # Check if author has permission to connect to his own VC
        if not author_voice.channel.permissions_for(ctx.author).connect:
            embed = create_embed("🚫 You do not have permission to connect to your own voice channel.", ctx.author.name)
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            return

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
        if member.voice and member.voice.channel.id != author_voice.channel.id:
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
        embed = create_embed("❗ No members were moved. Either they were already in your VC or an error occurred.", ctx.author.name)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permlist(ctx):
    if not allowed_roles:
        embed = create_embed("📜 No roles have permission to use the bot.", ctx.author.name)
    else:
        roles_list = "\n".join([f"🔹 {role.name} (ID: {role.id})" for role_id in allowed_roles for role in ctx.guild.roles if role.id == role_id])
        embed = create_embed(f"📜 Roles allowed to use the bot:\n{roles_list}", ctx.author.name)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permadd(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return
    
    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id not in allowed_roles:
            allowed_roles.append(role.id)
            embed = create_embed(f"✅ Role **{role.name}** has been granted permission to use the bot.", ctx.author.name)
        else:
            embed = create_embed(f"ℹ️ Role **{role.name}** already has permission.", ctx.author.name)
    else:
        embed = create_embed(f"❗ Role '{role_name_or_id}' not found.", ctx.author.name)
    await ctx.send(embed=embed, reference=ctx.message, mention_author=False)

@bot.command()
async def permdl(ctx, role_name_or_id: str):
    if ctx.author.id != special_user_id:
        embed = create_embed("❌ You do not have permission to execute this command.", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    role = discord.utils.get(ctx.guild.roles, name=role_name_or_id) or discord.utils.get(ctx.guild.roles, id=int(role_name_or_id))
    if role:
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            embed = create_embed(f"✅ Role **{role.name}** has been removed from allowed list.", ctx.author.name)
        else:
            embed = create_embed(f"ℹ️ Role **{role.name}** did not have permission.", ctx.author.name)
    else:
        embed = create_embed(f"❗ Role '{role_name_or_id}' not found.", ctx.author.name)
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
        embed = create_embed("❗ Please provide the voice channel name or ID to move the member. Example: `&move @John VoiceChannelName`", ctx.author.name)
        await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
        return

    # Find the channel by name or ID
    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name_or_id)
    if not channel:
        try:
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

    try:
        # Check if author has permission to join target VC
        if not channel.permissions_for(ctx.author).connect:
            embed = create_embed("🚫 You do not have permission to connect to that voice channel.", ctx.author.name)
            await ctx.send(embed=embed, reference=ctx.message, mention_author=False)
            return

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
                
