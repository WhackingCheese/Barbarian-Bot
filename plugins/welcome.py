import discord, database, random, json, asyncio
from discord.ext import commands

m = database.MessageGetter()

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.embed_clr = int(self.db.setting_get('embed_colour'))
        self.wlcm_msgs_j = self.db.setting_get('welcome_join')
        self.wlcm_msgs_l = json.loads(self.db.setting_get('welcome_leave'))

    async def on_ready(self):
        await asyncio.sleep(1)
        self.wlcm_chnl = self.bot.get_channel(int(self.db.setting_get('welcome_channel')))

    def invalid_syntax_embed(self):
        return discord.Embed(title='Invalid command syntax.', description=m.welcome_welcome_syntax, colour=self.embed_clr)

    @commands.group(pass_context=True, help = m.welcome_welcome_help)
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return

    @welcome.command(pass_context=True)
    async def channel(self, ctx, arg):
        mention = ctx.message.raw_channel_mentions
        if mention != []:
            if f'<#{mention[0]}>' == arg:
                self.db.setting_update('welcome_channel', mention[0])
                self.wlcm_chnl = self.bot.get_channel(mention[0])
                embed = discord.Embed(title='Welcome \\ Goodbye message channel has been updated to:', description=f'<#{mention[0]}>', colour=self.embed_clr)
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=self.invalid_syntax_embed())
        else:
            await ctx.send(embed=self.invalid_syntax_embed())
    
    @welcome.command(pass_context=True)
    async def message(self, ctx, *, arg):
        self.db.setting_update('welcome_join', arg)
        self.wlcm_msgs_j = arg
        embed = discord.Embed(title='The Welcome message has been updated to:', description=arg, colour=self.embed_clr)
        await ctx.send(embed=embed)

    @welcome.error
    @channel.error
    @message.error
    async def welcome_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=self.invalid_syntax_embed())

    async def on_member_join(self, member):
        await asyncio.sleep(1)
        message = self.wlcm_msgs_j.replace("{user.name}", member.display_name).replace("{user.mention}", member.mention).replace("{server}", member.guild.name)
        await self.wlcm_chnl.send(message)

    async def on_member_remove(self, member):
        message = random.choice(self.wlcm_msgs_l)
        message = message.replace("{user.name}", member.display_name).replace("{user.mention}", member.mention).replace("{server}", member.guild.name)
        await self.wlcm_chnl.send(message)

def setup(bot):
    bot.add_cog(Welcome(bot))