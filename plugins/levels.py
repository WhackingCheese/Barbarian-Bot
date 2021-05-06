import discord, random, time, database, json, operator, datetime, asyncio
from discord.ext import commands

def get_level_xp(level):
    return 5*(level**2)+50*level+100

def get_level_from_xp(xp):
    remaining_xp, level = xp, 0
    while remaining_xp >= get_level_xp(level):
        remaining_xp -= get_level_xp(level)
        level += 1
    return level

def get_xp_from_level(level):
	xp = 100
	level -= 1
	while level >= 1:
		xp += get_level_xp(level)
		level -= 1
	return xp

m = database.MessageGetter()

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = database.Database()
        self.rewrds = eval(self.db.setting_get('level_rewards'))
        self.embed_clr = int(self.db.setting_get('embed_colour'))
        self.embed_icon = self.db.setting_get('embed_icon_url')
        self.lvlup_msgs = json.loads(self.db.setting_get('level_messages'))
        self.xpmwe = int(self.db.setting_get('level_xp_weekend_mult'))
        self.xpmwd = int(self.db.setting_get('level_xp_def_mult'))
        if datetime.datetime.today().weekday() >= 5:
            self.xpm = self.xpmwe
        else:
            self.xpm = self.xpmwd
        self.xp_rew_min = int(self.db.setting_get('level_xp_rew_min'))
        self.xp_rew_max = int(self.db.setting_get('level_xp_rew_max'))

    def rewards_invalid_syntax_embed(self):
        return discord.Embed(title='Invalid command syntax.', description=m.levels_rewards_syntax, colour=self.embed_clr)

    async def on_message(self, message):
        if message.author.bot:
            return
        if message.author.dm_channel == message.channel:
            return
        player = message.author
        self.db.player_create_if_not_exists(player.id)
        xp = self.db.xp_get(player.id)
        msg_time = int(time.time())
        lvl = get_level_from_xp(xp[0])
        if xp[1] + 60 <= msg_time:
            xp[0] += random.randint(self.xpm * self.xp_rew_min, self.xpm * self.xp_rew_max)
            self.db.xp_update(player.id, xp[0], msg_time)
            nlvl = get_level_from_xp(xp[0])
            if nlvl != lvl:
                if nlvl == 1:
                    msg = m.levels_level_one_message
                else:
                    msg = random.choice(self.lvlup_msgs).replace("{user.name}", player.display_name).replace("{user.mention}", player.mention).replace("{server}", player.guild.name).replace("{level}", str(nlvl))
                embed = discord.Embed(color=self.embed_clr)
                embed.add_field(name=f"{player.display_name} has just achieved level {nlvl}!", value=msg)
                embed.set_thumbnail(url=player.avatar_url)
                player_reward = []
                for key, value in self.rewrds.items():
                    if value == nlvl:
                        player_reward.append(key)
                if len(player_reward) != 0:
                    for item in player_reward:
                        embed.add_field(name='Reward', value=f'<@&{item}>')
                for key in player_reward:
                    role_object = discord.Object(id=key)
                    await player.add_roles(role_object, reason=m.levels_reward_achieved_reason)
                await message.channel.send(embed=embed)

    async def xp_weekends(self):
        while True:
            if self.xpmwe != self.xpmwd:
                dayno = datetime.datetime.today().weekday()
                if dayno >= 5:
                    if self.xpm != self.xpmwe:
                        self.xpm = self.xpmwe
                        await self.bot.guilds[0].channels[0].send(f'**{self.xpmwe}x XP weekend is now active!**')
                else:
                    if self.xpm != self.xpmwd:
                        self.xpm = self.xpmwd
                        await self.bot.guilds[0].channels[0].send(f'**{self.xpmwe}x XP weekend is no longer active.**')
            await asyncio.sleep(60)

    async def on_ready(self):
        self.bot.loop.create_task(self.xp_weekends())

    @commands.command(pass_context=True, help=m.levels_xpreset_help)
    @commands.has_permissions(administrator=True)
    async def xpreset(self, ctx, user, *, password):
        if password != "Yes Yes Confirm.":
            await ctx.send(embed=discord.Embed(title='Invalid Password.', colour=self.embed_clr))
            return
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        if ctx.message.mentions:
            player = ctx.message.mentions[0]
            self.db.xp_update(player.id, 0, 0)
            await ctx.send(embed=discord.Embed(description=f'User {player.mention} has had their xp reset.', colour=self.embed_clr))
            for key in self.rewrds:
                role_object = discord.Object(id=key)
                await player.remove_roles(role_object, reason='Role removed due to xp reset.')
            await ctx.message.delete()
        else:
            await ctx.send(embed=discord.Embed(title='No user mentioned to reset the xp of.', colour=self.embed_clr))
    
    @xpreset.error
    async def xpreset_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=discord.Embed(title='Invalid command syntax.', description=m.levels_xpreset_syntax, colour=self.embed_clr))

    async def on_member_remove(self, member):
        if self.db.player_exists(member.id):
            self.db.player_delete(member.id)

    @commands.command(pass_context=True, help=m.levels_top3_help)
    async def top3(self, ctx):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        player_ids = self.db.get_top_3()
        if player_ids != None:
            embeds = []
            for item in player_ids:
                player = ctx.message.guild.get_member(item)
                player_xp = self.db.xp_get(item)[0]
                player_level = get_level_from_xp(player_xp)
                level_xp = get_level_xp(player_level)
                remaining_xp = player_xp - get_xp_from_level(player_level)
                rank = self.db.get_rank_from_playerid(item)
                embed = discord.Embed(colour=self.embed_clr)
                if player_level == 0:
                    remaining_xp += 100
                embed.add_field(name='Rank',
                                value=f'{rank}/{self.db.players_count()}',
                                inline=True)
                embed.add_field(name='Level',
                                value=player_level,
                                inline=True)
                embed.add_field(name='Experience',
                                value=f'{remaining_xp}/{level_xp}',
                                inline=True)
                embed.add_field(name='Total XP',
                                value=player_xp,
                                inline=True)
                embed.set_author(name=player.name)
                embed.set_thumbnail(url=player.avatar_url)
                embeds.append(embed)
            for item in embeds:
                await ctx.send(embed=item)

    @commands.group(pass_context=True, help = m.levels_rewards_help)
    async def rewards(self, ctx):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        if ctx.invoked_subcommand is None:
            sorted_rewrds = sorted(self.rewrds.items(), key=operator.itemgetter(1))
            if len(sorted_rewrds) == 0:
                embed = discord.Embed(title=f'There currently are no role rewards in {ctx.message.guild.name}.', colour=self.embed_clr)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title=f'The rewards for {ctx.message.guild.name} are:', colour=self.embed_clr)
                for i in range(len(sorted_rewrds)):
                    embed.add_field(name=f'Level {sorted_rewrds[i][1]}', value=f'<@&{sorted_rewrds[i][0]}>')
                await ctx.send(embed=embed)

    @rewards.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, role, level: int):
        if ctx.message.raw_role_mentions != []:
            role = ctx.message.raw_role_mentions[0]
            if role in self.rewrds:
                embed = discord.Embed(title='This role is already a reward.', colour=self.embed_clr)
                await ctx.send(embed=embed)
            else:
                players = self.db.get_playerids_xp_above(get_xp_from_level(level))
                role_object = discord.Object(id=role)
                for item in players:
                    player_object = ctx.message.guild.get_member(item)
                    await player_object.add_roles(role_object, reason=m.levels_rewards_add_added_reason.format(ctx.message.author.display_name))
                self.rewrds[role] = level
                self.db.setting_update('level_rewards', str(self.rewrds))
                embed = discord.Embed(title='Reward created.', description=m.levels_rewards_add_message.format(role, level), colour=self.embed_clr)
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.rewards_invalid_syntax_embed())

    @rewards.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, role):
        if ctx.message.raw_role_mentions != []:
            role = ctx.message.raw_role_mentions[0]
            if role in self.rewrds:
                players = self.db.get_playerids_xp_above(get_xp_from_level(self.rewrds[role]))
                role_object = discord.Object(id=role)
                for item in players:
                    player_object = ctx.message.guild.get_member(item)
                    await player_object.remove_roles(role_object, reason=m.levels_rewards_remove_removed_reason.format(ctx.message.author.display_name))
                del self.rewrds[role]
                self.db.setting_update('level_rewards', str(self.rewrds))
                embed = discord.Embed(title='Reward removed.', description=m.levels_rewards_remove_message.format(role), colour=self.embed_clr)
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(title='This role is not a reward.', colour=self.embed_clr)
                await ctx.send(embed=embed)
        else:
            await ctx.send(embed=self.rewards_invalid_syntax_embed())

    @rewards.command(pass_context=True)
    @commands.has_permissions(administrator=True)
    async def edit(self, ctx, role, level: int):
        if ctx.message.raw_role_mentions != []:
            role = ctx.message.raw_role_mentions[0]
            if role in self.rewrds:
                if level == self.rewrds[role]:
                    embed = discord.Embed(title=m.levels_rewards_edit_level_same, colour=self.embed_clr)
                    await ctx.send(embed=embed)
                    return
                elif level > self.rewrds[role]:
                    players = self.db.get_playerids_xp_minmax(get_xp_from_level(self.rewrds[role]), get_xp_from_level(level)-1)
                    role_object = discord.Object(id=role)
                    for item in players:
                        player_object = ctx.message.guild.get_member(item)
                        await player_object.remove_roles(role_object, reason=m.levels_rewards_edit_reward_removed_reason.format(ctx.message.author.display_name))
                    self.rewrds[role] = level
                    self.db.setting_update('level_rewards', str(self.rewrds))
                elif level < self.rewrds[role]:
                    players = self.db.get_playerids_xp_minmax(get_xp_from_level(level), get_xp_from_level(self.rewrds[role]))
                    role_object = discord.Object(id=role)
                    for item in players:
                        player_object = ctx.message.guild.get_member(item)
                        await player_object.add_roles(role_object, reason=m.levels_rewards_edit_reward_added_reason.format(ctx.message.author.display_name))
                    self.rewrds[role] = level
                    self.db.setting_update('level_rewards', str(self.rewrds))
                embed = discord.Embed(title='The rewards have been updated.', description=m.levels_rewards_edit_message.format(role, level), colour=self.embed_clr)
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=self.rewards_invalid_syntax_embed())
        else:
            await ctx.send(embed=self.rewards_invalid_syntax_embed())

    @rewards.error
    @add.error
    @remove.error
    @edit.error
    async def rewards_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(embed=self.rewards_invalid_syntax_embed())

    @commands.cooldown(1, 120, type=commands.BucketType.user)
    @commands.command(pass_context=True, help = m.levels_punish_help)
    @commands.has_permissions(ban_members=True)
    async def punish(self, ctx, user, xp: int):
        if xp > 5000:
            xp = 5000
        if xp < 0:
            return
        if ctx.message.mentions:
            player = ctx.message.mentions[0]
        else:
            await ctx.send(embed=discord.Embed(title="Invalid command syntax.", description = m.levels_punish_syntax))
            return
        player_xp = self.db.xp_get(player.id)[0]
        if xp > player_xp:
            newxp = 0
        else:
            newxp = player_xp - xp
        self.db.xp_update(player.id, newxp, 0)
        await ctx.send(embed=discord.Embed(title=f"User {player.display_name} has been punished.", description=m.levels_punish_punished.format(xp, newxp), colour=self.embed_clr))

    @punish.error
    async def punish_handler(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            await ctx.send(error)
            await ctx.send(embed=discord.Embed(title="Invalid command syntax.", description = m.levels_punish_syntax, colour=self.embed_clr))

    @commands.command(pass_context=True, help = m.levels_rank_help)
    async def rank(self, ctx):
        if ctx.message.author.bot:
            return
        if ctx.message.author.dm_channel == ctx.message.channel:
            return
        number = ctx.message.content.replace('!rank ', '')
        if number.isdigit():
            player_id = self.db.get_playerid_with_rank(int(number))
            if player_id != None:
                player = ctx.message.guild.get_member(player_id)
            else:
                return
        elif ctx.message.mentions:
            player = ctx.message.mentions[0]
        else:
            player = ctx.message.author
        if player.bot:
            return
        self.db.player_create_if_not_exists(player.id)
        player_xp = self.db.xp_get(player.id)[0]
        player_level = get_level_from_xp(player_xp)
        level_xp = get_level_xp(player_level)
        remaining_xp = player_xp - get_xp_from_level(player_level)
        rank = self.db.get_rank_from_playerid(player.id)
        embed = discord.Embed(colour=self.embed_clr)
        if player_level == 0:
            remaining_xp += 100
        embed.add_field(name='Rank',
                        value=f'{rank}/{self.db.players_count()}',
                        inline=True)
        embed.add_field(name='Level',
                        value=player_level,
                        inline=True)
        embed.add_field(name='Experience',
                        value=f'{remaining_xp}/{level_xp}',
                        inline=True)
        embed.add_field(name='Total XP',
                        value=player_xp,
                        inline=True)
        embed.set_author(name=player.name)
        embed.set_thumbnail(url=player.avatar_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Levels(bot))
