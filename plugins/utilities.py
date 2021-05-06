import discord, asyncio, database
from discord.ext import commands

m = database.MessageGetter()

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.embed_clr = int(self.db.setting_get('embed_colour'))

    @commands.group(pass_context=True, help=m.utilities_settings_help)
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(embed=discord.Embed(title="Available settings in the databse are:", description=str(self.db.setting_get_all()), colour=self.embed_clr))

    @settings.command(pass_context=True)
    async def dump(self, ctx, setting):
        if setting == 'token':
            return
        if self.db.setting_exists(setting):
            msg = self.db.setting_get(setting)
            await ctx.send(embed=discord.Embed(title=f'The value for {setting} is:', description=msg, colour=self.embed_clr))
        else:
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} doesn't exist.", colour=self.embed_clr))

    @settings.command(pass_context=True)
    async def edit(self, ctx, setting, *, value):
        if setting == 'token':
            return
        if self.db.setting_exists(setting):
            self.db.setting_update(setting, value)
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} has been updated to:", description=value, colour=self.embed_clr))
        else:
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} doesn't exist.", colour=self.embed_clr))

    @settings.command(pass_context=True)
    async def add(self, ctx, setting, *, value):
        if setting == 'token':
            return
        if self.db.setting_exists(setting):
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} already exists.", colour=self.embed_clr))
        else:
            self.db.setting_add(setting, value)
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} has been added to settings table with value:", description=value, colour=self.embed_clr))

    @settings.command(pass_context=True)
    async def remove(self, ctx, setting):
        if setting == 'token':
            return
        if self.db.setting_exists(setting):
            self.db.setting_delete(setting)
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} has been removed."))
        else:
            await ctx.send(embed=discord.Embed(title=f"Setting {setting} doesn't exist.", colour=self.embed_clr))

    @dump.error
    @edit.error
    @add.error
    @remove.error
    async def rewards_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=discord.Embed(title='Invalid command syntax.', description=m.utilities_settings_syntax, colour=self.embed_clr))

    @commands.command(pass_context=True, help=m.utilities_clear_help)
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, num: int):
        channel = ctx.message.channel
        limit = 100
        if num > limit:
            num = limit
        if ctx.message.mentions:
            player = ctx.message.mentions[0]
            def is_mention(m):
                return m.author == player
            await channel.purge(limit=num, check=is_mention, bulk=True)
            await ctx.send(embed=discord.Embed(title=f"Deleted all messages by {player.display_name} in the last {num} messages.", colour=self.embed_clr))
        else:
            await channel.purge(limit=num, bulk=True)
            await ctx.send(embed=discord.Embed(title=f"Deleted {num} messages.", colour=self.embed_clr))

    @clear.error
    async def clear_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=discord.Embed(title='Invalid syntax', description=m.utilities_clear_syntax, colour=self.embed_clr))

    async def database_cleanup(self):
        while True:
            self.db.cleanup()
            await asyncio.sleep(86400)

    async def on_ready(self):
        print('----------------------')
        print('  ', self.bot.user.name, "Online")
        print(' ', self.bot.user.id)
        print('----------------------')
        self.bot.loop.create_task(self.database_cleanup())

def setup(bot):
    bot.add_cog(Utilities(bot))