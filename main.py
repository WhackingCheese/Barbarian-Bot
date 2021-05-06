import discord, traceback, sys, database , asyncio
from discord.ext import commands

db = database.Database()

bot_extensions = ['plugins.commands',
                  'plugins.dictionary',
                  'plugins.levels',
                  'plugins.presence',
                  'plugins.utilities',
                  'plugins.welcome',
                  'plugins.help']
bot = commands.Bot(command_prefix='!')

if __name__ == '__main__':
    for extension in bot_extensions:
        try:
            bot.load_extension(extension)
            print(f'Extension {extension} loaded')
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

@bot.command(pass_context=True)
@commands.has_permissions(administrator=True)
async def reload(ctx):
    for extension in bot_extensions:
        try:
            bot.unload_extension(extension)
            bot.load_extension(extension)
            print(f'Extension {extension} has been reloaded')
        except Exception:
            print(f'Failed to reload extension {extension}.', file=sys.stderr)
            traceback.print_exc()

bot.run(db.setting_get('token'), bot=True, reconnect=True)