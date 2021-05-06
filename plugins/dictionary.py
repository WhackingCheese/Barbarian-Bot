from vocabulary.vocabulary import Vocabulary
from html.parser import HTMLParser
from discord.ext import commands
from bbcode import Parser
import discord, re, json, database

m = database.MessageGetter()

class Dictionary(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.embed_clr = int(self.db.setting_get('embed_colour'))

    @commands.cooldown(1, 15, type=commands.BucketType.user)
    @commands.command(pass_context=True, help=m.dictionary_define_help)
    async def define(self, ctx, *, arg):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        def_list = Vocabulary.meaning(arg)
        if def_list == False or def_list == '[]':
            return
        definitions, msg_grammar, msg_unparsed = [], [], ''
        for i in json.loads(def_list):
            definitions.append(i["text"])
        results = definitions[:3]
        for i in range(len(results)):
            if results[i][-1:] != '.':
                results[i] += '.'
            msg_grammar.append(results[i].capitalize())
            msg_unparsed += "**" + str(i+1) + ".** "
            if i == 0:
                msg_unparsed += " "
            msg_unparsed += str(msg_grammar[i]) + "\n"
        msg_parsed = Parser().strip(HTMLParser().unescape((re.compile(r'<.*?>')).sub('', msg_unparsed)))
        await ctx.send(embed=discord.Embed(title=f'Definitions for {arg}.', description=msg_parsed, color=self.embed_clr))

def setup(bot):
    bot.add_cog(Dictionary(bot))