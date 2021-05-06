import discord, database
from discord.ext import commands
from datetime import datetime

def presence(presence_type, presence_name):
    if presence_type == 'playing':
        return discord.Game(name = presence_name, start = datetime.utcnow())
    elif presence_type == 'listening':
        return discord.Activity(name = presence_name, type = discord.ActivityType.listening, start = datetime.utcnow())
    elif presence_type == 'watching':
        return discord.Activity(name = presence_name, type = discord.ActivityType.watching, start = datetime.utcnow())
    elif presence_type == 'streaming':
        return discord.Streaming(name = presence_name, url = "https://www.twitch.tv/whackingcheese")
    else:
        return None

m = database.MessageGetter()

class Presence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.embed_clr = int(self.db.setting_get('embed_colour'))
    
    def invalid_syntax_embed(self):
        return discord.Embed(title='Invalid command syntax.', description=m.presence_presence_syntax, colour=self.embed_clr)

    @commands.command(pass_context=True, help=m.presence_presence_help)
    @commands.has_permissions(administrator=True)
    async def presence(self, ctx, arg1, *, arg2):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        game = presence(arg1, arg2)
        if game == None:
            await ctx.send(embed=self.invalid_syntax_embed())
            return
        await self.bot.change_presence(activity=game)
        self.db.setting_update('presence_type', arg1)
        self.db.setting_update('presence_name', arg2)
        if arg1 == 'listening':
            arg1 += ' to'
        embed = discord.Embed(title='Bot presence has been changed to:', color=self.embed_clr)
        embed.add_field(name=arg1.capitalize(), value=arg2)
        await ctx.send(embed=embed)

    async def on_ready(self):
        game = presence(self.db.setting_get('presence_type'), self.db.setting_get('presence_name'))
        if game != None:
            await self.bot.change_presence(activity=game)
    
    @presence.error
    async def presence_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=self.invalid_syntax_embed())

def setup(bot):
    bot.add_cog(Presence(bot))