import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='&', intents=intents)

# Permissions and allowed users setup
access_enabled = True
special_user_id = 1176678272579424258  # Special user who can always use the bot
allowed_roles = []  # Role IDs of users who are allowed to use the bot (add them here)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def pull(ctx, member: discord.Member = None):
    # Check if the bot is accessible by the special user or allowed roles
    if not access_enabled and ctx.author.id != special_user_id and not any(role.id in allowed_roles for role in ctx.author.roles):
        await ctx.send("Bot ka use abhi sirf ek specific user ya authorized roles ke liye allowed hai.")
        return

    author_voice = ctx.author.voice
    if not author_voice:
        await ctx.send("Tum kisi VC me nahi ho.")
        return

    if member is None:
        await ctx.send("Tumhe ek member ko mention karna hoga. Example: &pull @John")
        return

    if not member.voice:
        await ctx.send(f"{member.name} VC me nahi hai.")
        return

    # Check if the author can move the member based on their VC join permissions
    member_voice_channel = member.voice.channel
    author_permissions = ctx.author.guild_permissions

    # Check if the author has permission to join the member's VC
    if member_voice_channel:
        # Check if author can join the member's VC (author must have 'connect' permission for that VC)
        if author_voice_channel.permissions_for(ctx.author).connect:
            try:
                await member.move_to(author_voice.channel)
                await ctx.send(f"{member.name} ko {ctx.author.name} ne tumhare VC me move kar diya.")
            except discord.Forbidden:
                await ctx.send("Bot ke paas permission nahi hai members ko move karne ki.")
            except Exception as e:
                await ctx.send(f"Kuch error hua: {e}")
        else:
            await ctx.send(f"{ctx.author.name} ko {member.name} ke VC me move karne ki permission nahi hai.")
    else:
        await ctx.send(f"{member.name} kisi VC me nahi hai.")

# Command to enable/disable bot access based on special permissions or roles
@bot.command()
async def permadd(ctx, role: str):
    """Add permission for a role to use the bot."""
    # Add the role ID or name to the allowed roles list
    allowed_roles.append(role)
    await ctx.send(f"Role {role} ko bot use karne ki permission de di gayi hai.")

@bot.command()
async def permremove(ctx, role: str):
    """Remove permission for a role to use the bot."""
    if role in allowed_roles:
        allowed_roles.remove(role)
        await ctx.send(f"Role {role} ko bot use karne ki permission hata di gayi hai.")
    else:
        await ctx.send(f"Role {role} ko bot use karne ki permission nahi thi.")

@bot.command()
async def permlist(ctx):
    """Show the list of roles with permission to use the bot."""
    if allowed_roles:
        await ctx.send("Allowed roles for the bot: " + ", ".join(allowed_roles))
    else:
        await ctx.send("Koi roles bot use karne ke liye authorized nahi hai.")

@bot.command()
async def allon(ctx):
    """Allow anyone to use the bot."""
    global access_enabled
    access_enabled = True
    await ctx.send("Sabhi ko bot use karne ki permission mil gayi hai.")

@bot.command()
async def alloff(ctx):
    """Restrict bot use to only special user and allowed roles."""
    global access_enabled
    access_enabled = False
    await ctx.send("Sirf authorized users aur roles ko hi bot use karne ki permission hai.")

# Running the bot with the token (replace 'your-token-here' with the actual token)
bot.run('your-token-here')
