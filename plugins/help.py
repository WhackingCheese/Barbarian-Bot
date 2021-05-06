import discord, database
from discord.ext import commands

m = database.MessageGetter()

async def _can_run(cmd, ctx):
    try:
        return await cmd.can_run(ctx)
    except:
        return False

async def get_runnable_commands(bot, ctx):
    cmds = bot.commands
    cmds2 = []
    cgs = bot.cogs
    for cog in cgs:
        for command in cmds:
            if command.cog_name == cog:
                if (await _can_run(command, ctx)):
                    cmds2.append(command)
    return cmds2

def get_help_message(cmds):
    message = ''
    last_cog = None
    for command in cmds:
        if last_cog == None:
            last_cog = command.cog_name
            message += "**" + command.cog_name + '**\n'
            message += '  !' + command.name + '\n'
        elif last_cog == command.cog_name:
            message += '  !' + command.name + '\n'
        elif last_cog != command.cog_name:
            last_cog = command.cog_name
            message += "**" + command.cog_name + '**\n'
            message += '  !' + command.name + '\n'
    return message

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.embed_clr = int(self.db.setting_get('embed_colour'))
        self.embed_icon = self.db.setting_get('embed_icon_url')

    @commands.command(pass_context=True, help=m.help_help_help)
    async def help(self, ctx, *args):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        cmd = None
        if args == ():
            custom_commands = self.db.commands_get()
            msg = ''
            if len(custom_commands) != 0:
                msg += '**Custom Commands**\n'
                for i in range(len(custom_commands)):
                    msg += '  ' + custom_commands[i][0] + '\n'
            msg += get_help_message(await get_runnable_commands(self.bot, ctx))
            if ctx.message.author.dm_channel == None:
                await ctx.message.author.create_dm()
            embed = discord.Embed(description=msg, colour=self.embed_clr)
            embed.set_footer(text=ctx.message.guild.name, icon_url=self.embed_icon)
            await ctx.message.author.dm_channel.send('**These are the commands that are available to you:**', embed=embed)
        else:
            cmds = (await get_runnable_commands(self.bot, ctx))
            for item in cmds:
                if item.name == args[0]:
                    cmd = item
                    break
            if cmd != None:
                if ctx.message.author.dm_channel == None:
                    await ctx.message.author.create_dm()
                embed = discord.Embed(title=f'Help for command {args[0]}:', description=cmd.help, colour=self.embed_clr)
                await ctx.message.author.dm_channel.send(embed=embed)

def setup(bot):
    bot.remove_command("help")
    bot.add_cog(Help(bot))