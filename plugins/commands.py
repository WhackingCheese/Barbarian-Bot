import discord, database
from discord.ext import commands

m = database.MessageGetter()

class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.cmds = self.db.commands_get()
        self.embed_clr = int(self.db.setting_get('embed_colour'))
    
    def invalid_syntax_embed(self):
        return discord.Embed(title='Invalid command syntax.', description=m.commands_command_syntax, colour=self.embed_clr)
    
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.dm_channel == message.channel:
            return
        for item in self.cmds:
            if message.content.startswith(item[0]):
                await message.channel.send(item[1])
                return

    @commands.has_permissions(administrator=True)
    @commands.group(pass_context=True, help = m.commands_command_help)
    async def command(self, ctx):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return

    @command.command(pass_context=True)
    async def add(self, ctx, arg, *, args):
        if not arg.isalnum():
            await ctx.send(embed=self.invalid_syntax_embed())
            return
        command = '!' + arg
        for i in range(len(self.cmds)):
            if command == self.cmds[i][0]:
                await ctx.send(embed=discord.Embed(title='A command with this name already exists.', colour=self.embed_clr))
                return
        self.db.command_add(command, args)
        embed = discord.Embed(title='Command has been added successfully.', colour=self.embed_clr)
        embed.add_field(name=command, value=args)
        await ctx.send(embed=embed)
        self.cmds.append([command, args])

    @command.command(pass_context=True)
    async def remove(self, ctx, arg):
        arg = '!' + arg
        for i in range(len(self.cmds)):
            if arg == self.cmds[i][0]:
                self.db.command_remove(arg)
                await ctx.send(embed=discord.Embed(title=f'Command {arg} has been removed.', colour=self.embed_clr))
                del self.cmds[i]
                return
        else:
            await ctx.send(embed=discord.Embed(title=f"Command {arg} isn't a command.", colour=self.embed_clr))

    @command.command(pass_context=True)
    async def edit(self, ctx, arg, *, args):
        arg = '!' + arg
        for i in range(len(self.cmds)):
            if arg == self.cmds[i][0]:
                self.db.command_edit(arg, args)
                await ctx.send(embed=discord.Embed(title=f'Command {arg} has been edited to:', description=args, colour=self.embed_clr))
                self.cmds[i][1] = args
                return
        else:
            await ctx.send(embed=discord.Embed(title=f"Command with name {arg} doesn't exist.", colour=self.embed_clr))

    @command.error
    @add.error
    @remove.error
    @edit.error
    async def commands_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=self.invalid_syntax_embed())

def setup(bot):
    bot.add_cog(Commands(bot))