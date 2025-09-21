import discord
from discord import app_commands
from discord.ext import commands, tasks
import youtube_dl
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
GUILD = discord.Object(id=GUILD_ID)

voice_client = None
playlist = []  # liste des URLs YouTube
current_song = 0

ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extractaudio': True,
    'audioformat': "mp3",
    'outtmpl': "song.%(ext)s",
    'noplaylist': True,
}

def get_audio_source(url):
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['url']

# ================== Commandes ==================
@bot.tree.command(name="joinvc", description="Faire rejoindre le bot à un salon vocal", guild=GUILD)
@app_commands.describe(channel_id="ID du salon vocal")
async def joinvc(interaction: discord.Interaction, channel_id: str):
    global voice_client
    channel = bot.get_channel(int(channel_id))
    if not channel or not isinstance(channel, discord.VoiceChannel):
        await interaction.response.send_message("Salon vocal invalide.", ephemeral=True)
        return

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()
    await interaction.response.send_message(f"Connecté à {channel.name} ✅", ephemeral=True)
    play_music.start()

@bot.tree.command(name="addsong", description="Ajouter une URL YouTube à la playlist", guild=GUILD)
@app_commands.describe(url="URL de la vidéo YouTube")
async def addsong(interaction: discord.Interaction, url: str):
    playlist.append(url)
    await interaction.response.send_message(f"🎵 Ajouté à la playlist : {url}", ephemeral=True)

@bot.tree.command(name="leavevc", description="Faire quitter le bot du salon vocal", guild=GUILD)
async def leavevc(interaction: discord.Interaction):
    global voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        play_music.stop()
        voice_client = None
        await interaction.response.send_message("Déconnecté du salon vocal ✅", ephemeral=True)
    else:
        await interaction.response.send_message("Le bot n'est pas connecté à un salon.", ephemeral=True)

# ================== Lecture en boucle ==================
from discord import FFmpegPCMAudio
from discord.utils import get

@tasks.loop(seconds=1.0)
async def play_music():
    global current_song, voice_client
    if not voice_client or not voice_client.is_connected() or len(playlist) == 0:
        return
    if not voice_client.is_playing():
        url = playlist[current_song]
        source = FFmpegPCMAudio(get_audio_source(url))
        voice_client.play(source, after=lambda e: print(f"Erreur: {e}" if e else ""))
        current_song = (current_song + 1) % len(playlist)

# ================== Synchronisation ==================
@bot.event
async def on_ready():
    await bot.tree.sync(guild=GUILD)
    print(f"Connecté comme {bot.user} ✅")

bot.run(TOKEN)
