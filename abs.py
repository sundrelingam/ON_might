"""
Add bot to server with this URL:
https://discordapp.com/oauth2/authorize?&client_id=852920228190879816&scope=bot&permissions=2164800
"""

import discord
import random
import requests
import asyncio
import youtube_dl
from discord.ext import commands
from dotenv import load_dotenv
import os
from os.path import join, dirname

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

TENOR_TOKEN = os.environ.get("TENOR_TOKEN")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}
ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def get_gif(searchTerm):
    response = requests.get("https://g.tenor.com/v1/search?q={}&key={}&limit=1".format(searchTerm, TENOR_TOKEN))
    data = response.json()
    return data['results'][0]['media'][0]['gif']['url']


class SymbolOfPeace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()

    @commands.command()
    async def gobeyond(self, ctx, *, url="https://www.youtube.com/watch?v=lsHCzboWK0U"):
        self._times = [0.75, 0.5, 1.0]
        self._weights = [0.45, 0.45, 0.1]
        self._exercises = ['KTE Crunch',
                           'Heaven Raises',
                           'Starfish Crunch',
                           'Figure 8s',
                           'Seated Ab Circles (Left)',
                           'Seated Ab Circles (Right)',
                           'Drunken Mountain Climbers',
                           'Dead Bug',
                           'Alternating Bicycle',
                           'Scissor V-ups',
                           'Russian V-tuck Twist',
                           'Marching Planks',
                           '3-way Seated Ab Tucks',
                           'Twisting Pistons',
                           'Frog Crunch',
                           'Black Widow Plank',
                           'Thread the Needle',
                           'Russian Twists',
                           'Side to Side Kick-through',
                           'V-Tuck',
                           'Super Athletic V-Tuck Extraordinaire']

        # you say run
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        # get hyped with all might vs nomu
        gif_url = get_gif('plus-ultra')
        embed = discord.Embed()
        embed.set_image(url=gif_url)
        await ctx.send(embed=embed)

        # begin abs.exe
        time_remaining = 7

        while time_remaining > 3.5:
            t = random.choices(self._times, self._weights)[0] * 60
            x = random.choice(self._exercises)
            self._exercises.remove(x)

            await ctx.send(f'{x} for {str(t)} seconds')
            await asyncio.sleep(t)

            # countdown until next exercise
            for i in reversed(range(5)):
                await ctx.send(f'{i + 1} ...')
                await asyncio.sleep(1)

            time_remaining -= 5 / 60  # subtract countdown time
            time_remaining -= t / 60

        await ctx.send('30 second rest')
        await asyncio.sleep(25)
        for i in reversed(range(5)):
            await ctx.send(f'{i + 1} ...')
            await asyncio.sleep(1)

        while time_remaining > 0:
            t = random.choices(self._times, self._weights)[0] * 60
            x = random.choice(self._exercises)
            self._exercises.remove(x)

            await ctx.send(f'{x} for {str(t)} seconds')
            await asyncio.sleep(t)

            for i in reversed(range(5)):
                await ctx.send(f'{i + 1} ...')
                await asyncio.sleep(1)

            time_remaining -= 5 / 60
            time_remaining -= t / 60

        await ctx.send('Ok done. Nice.')

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @gobeyond.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


bot = commands.Bot(command_prefix=commands.when_mentioned_or("/"))
bot.add_cog(SymbolOfPeace(bot))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
