import sys
import logging
import datetime
import traceback

import aiohttp
import discord
from discord.ext import commands

import config
from cogs.utils import context


logging.getLogger('discord').setLevel(logging.INFO)
log = logging.getLogger()
fmt = logging.Formatter('|{asctime}|{levelname}|{name}: {message}', '%Y-%m-%d %I:%M:%S %p', style='{')
sneakyhandler = logging.FileHandler(filename='logs/sneakyninja.log', encoding='utf-8')
sneakyhandler.addFilter(lambda rec: not rec.name.split('.')[0] == 'discord')
sneakyhandler.setFormatter(fmt)

discordhandler = logging.FileHandler(filename='logs/discord.log', mode='w', encoding='utf-8')
discordhandler.addFilter(lambda rec: rec.name.split('.')[0] == 'discord')
discordhandler.setFormatter(fmt)

log.addHandler(sneakyhandler)
log.addHandler(discordhandler)


initial_extensions = (
    'cogs.info',
    'cogs.admin',
    'cogs.mod',
    'cogs.manage',
    'cogs.fun'
)

class SneakyNinja(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('>>'), owner_id=config.owner_id,
            description="Greetings, I can provide various info and of course, help you run server",
            activity=discord.Activity(name='>>help', type=discord.ActivityType.listening),
            intents=discord.Intents(
                guilds=True, members=True, messages=True,
                voice_states=True, emojis=True, invites=True
            )
        )
        
        # utils
        self.session = None

        # preferences
        self.colour = discord.Colour(0x04f2a6)
        self.time_format = "%d %B, %Y; %I:%M %p"

        # a global cooldown mapping, to avoid command spams 
        self._global_cooldown = commands.CooldownMapping.from_cooldown(5, 6.0, commands.BucketType.member)
        self.add_check(self.global_cooldown_check)

        self.load_extension('cogs.core')  # cogs.core's exception shouldn't be ignored
        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as error:
                print(f'Failed to load {extension}')
                traceback.print_exception(type(error), error, error.__traceback__)


    async def on_ready(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        print(f"Logged in:\n{self.user.name} - {self.user.id}")

    async def get_context(self, message, *, cls=context.Context):
        return await super().get_context(message, cls=cls)

    async def close(self):
        await super().close()
        await self.session.close()

    async def global_cooldown_check(self, ctx):
        """Global Command Cooldown"""

        # this is the global cooldown implementaion
        # but cogs and commands may have their own local cooldown
        bucket = self._global_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise commands.CommandOnCooldown(bucket, retry_after)
        return True

    def timenow(self):
        return datetime.datetime.utcnow()

    async def send_owner(self, msg, **kwargs):
        owner = self.get_user(self.owner_id)
        await owner.send(msg, **kwargs)


bot = SneakyNinja()
bot.run(config.token)
