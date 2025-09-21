import discord
from discord import app_commands
from discord.ext import commands, tasks
import youtube_dl
from dotenv import load_dotenv
import os
from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.message_content = True  # Pour certaines commandes, utile si tu veux le contenu des messages
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
GUILD = discord.Object(id=GUILD_ID)

voice_client = None
playlist = []  # liste des URLs YouTube
current_song = 0

# ================== YoutubeDL ==================
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extractaudio': True,
    'audioformat': "mp3",
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

    try:
        if voice_client and voice_client.is_connected():
            await voice_client.move_to(channel)
        else:
            voice_client = await channel.connect()
        await interaction.response.send_message(f"Connecté à {channel.name} ✅", ephemeral=True)
        if not play_music.is_running():
            play_music.start()
    except Exception as e:
        await interaction.response.send_message(f"Erreur de connexion au salon : {e}", ephemeral=True)
        print("Erreur joinvc:", e)

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

@bot.tree.command(name="skip", description="Passer la chanson actuelle", guild=GUILD)
async def skip(interaction: discord.Interaction):
    if voice_client and voice_client.is_playing():
        voice_client.stop()
        await interaction.response.send_message("⏭ Chanson suivante", ephemeral=True)
    else:
        await interaction.response.send_message("Aucune musique en cours", ephemeral=True)

@bot.tree.command(name="pause", description="Mettre en pause la musique", guild=GUILD)
async def pause(interaction: discord.Interaction):
    if voice_client and voice_client.is_playing():
        voice_client.pause()
        await interaction.response.send_message("⏸ Musique en pause", ephemeral=True)
    else:
        await interaction.response.send_message("Aucune musique en cours", ephemeral=True)

@bot.tree.command(name="resume", description="Reprendre la musique", guild=GUILD)
async def resume(interaction: discord.Interaction):
    if voice_client and voice_client.is_paused():
        voice_client.resume()
        await interaction.response.send_message("▶ Musique reprise", ephemeral=True)
    else:
        await interaction.response.send_message("Aucune musique en pause", ephemeral=True)

# ================== Lecture en boucle ==================
from discord import FFmpegPCMAudio

@tasks.loop(seconds=1.0)
async def play_music():
    global current_song, voice_client
    if not voice_client or not voice_client.is_connected() or len(playlist) == 0:
        return
    if not voice_client.is_playing():
        try:
            url = playlist[current_song]
            source = FFmpegPCMAudio(get_audio_source(url))
            voice_client.play(source, after=lambda e: print(f"Erreur playback: {e}" if e else ""))
            current_song = (current_song + 1) % len(playlist)
        except Exception as e:
            print("Erreur lecture musique:", e)
            current_song = (current_song + 1) % len(playlist)

# ================== Synchronisation ==================
@bot.event
async def on_ready():
    await bot.tree.sync(guild=GUILD)
    print(f"Connecté comme {bot.user} ✅")

# ================== Keep alive ==================
keep_alive()
bot.run(TOKEN)
