import sqlite3

class Database:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(Database, cls).__new__(cls, *args, **kwargs)
            cls.__instance.conn = sqlite3.connect('database.db')
            cls.__instance.c = cls.__instance.conn.cursor()
        return cls.__instance

    def setting_get(self, setting):
        '''Returns setting value from Settings table where setting name is setting.'''
        self.c.execute('SELECT value FROM Settings WHERE setting = (?)', (setting,))
        return self.c.fetchall()[0][0]

    def setting_delete(self, setting):
        '''Deletes entry for setting in Settings table.'''
        self.c.execute('DELETE FROM Settings WHERE setting = (?)', (setting,))
        self.conn.commit()

    def setting_exists(self, setting):
        '''Checks if setting exists in Settings table.'''
        self.c.execute('SELECT EXISTS (SELECT 1 FROM Settings WHERE setting = (?))', (setting,))
        if (self.c.fetchall()[0][0]) == 1:
            return True
        else:
            return False

    def setting_add(self, setting, value):
        '''Creates entry for setting in Settings table.'''
        self.c.execute('INSERT INTO Settings(setting, value) VALUES (?, ?)', (setting, value))
        self.conn.commit()

    def setting_get_all(self):
        '''Returns a list of all available settings.'''
        self.c.execute('SELECT setting from Settings')
        data, items = self.c.fetchall(), []
        for i in range(len(data)):
            items.append(data[i][0])
        return items

    def setting_update(self, setting, value):
        '''Updates setting value with value where setting name is setting.'''
        self.c.execute('UPDATE Settings SET value = (?) WHERE setting = (?)', (value, setting))
        self.conn.commit()

    def player_create_if_not_exists(self, player_id):
        '''Creates player entry in Players table if player entry for that player isnt already present.'''
        self.c.execute('SELECT EXISTS (SELECT 1 FROM Players WHERE player_id = (?))', (player_id,))
        if (self.c.fetchall()[0][0]) == 1:
            return
        else:
            self.c.execute('INSERT INTO Players(player_id, xp_value, xp_time) VALUES (?, ?, ?)', (player_id, 0, 0))
            self.conn.commit()

    def player_exists(self, player_id):
        '''Checks if player entry for player with id palyer_id exists in Players table'''
        self.c.execute('SELECT EXISTS (SELECT 1 FROM Players WHERE player_id = (?))', (player_id,))
        if (self.c.fetchall()[0][0]) == 1:
            return True
        else:
            return False

    def get_playerids_xp_above(self, xp_value):
        '''Returns a list containing player_ids where xp_value is above xp_value.'''
        self.c.execute('SELECT player_id FROM Players WHERE xp_value >= (?)', (xp_value,))
        data, items = self.c.fetchall(), []
        for i in range(len(data)):
            items.append(data[i][0])
        return items

    def get_playerids_xp_minmax(self, min_xp, max_xp):
        '''Returns a list containing player_ids where xp value is above or equal to min_xp and below or equal to max_xp.'''
        self.c.execute('SELECT player_id FROM Players WHERE xp_value >= (?) AND xp_value <= (?)', (min_xp, max_xp))
        data, items = self.c.fetchall(), []
        for i in range(len(data)):
            items.append(data[i][0])
        return items

    def player_delete(self, player_id):
        '''Deletes player entry in Players table for player with ID player_id.'''
        self.c.execute('DELETE FROM Players WHERE player_id = (?)', (player_id,))
        self.conn.commit()

    def xp_get(self, player_id):
        '''Returns a list containing xp value and xp time for player iwth ID player_id.'''
        self.c.execute('SELECT xp_value, xp_time FROM Players WHERE player_id = (?)', (player_id,))
        return list(self.c.fetchall()[0])

    def xp_update(self, player_id, new_xp_value, new_xp_time):
        '''Updates xp value and xp time for player with ID player_id to new_xp_value and new_xp_time.'''
        self.c.execute('UPDATE Players SET xp_value = (?), xp_time = (?) WHERE player_id = (?)', (new_xp_value, new_xp_time, player_id))
        self.conn.commit()

    def get_playerid_with_rank(self, rank):
        '''Returns a player_id with the rank largest xp_value.'''
        self.c.execute('SELECT player_id FROM (SELECT player_id, xp_value FROM Players ORDER BY xp_value DESC, player_id desc) LIMIT 1 OFFSET (?)', (rank-1,))
        try:
            result = self.c.fetchall()[0][0]
            return result
        except IndexError:
            return None

    def get_rank_from_playerid(self, player_id):
        '''Returns the rank of the player with the given id'''
        self.c.execute('SELECT player_id FROM (SELECT player_id, xp_value FROM Players ORDER BY xp_value DESC, player_id desc)')
        try:
            result, results = self.c.fetchall(), []
            for item in result:
                results.append(item[0])
            return results.index(player_id)+1
        except IndexError:
            return None

    def get_top_3(self):
        '''Returns the ids of 3 players with the most xp.'''
        self.c.execute('SELECT player_id FROM (SELECT player_id, xp_value FROM Players ORDER BY xp_value DESC, player_id desc) LIMIT 3')
        try:
            result, results = self.c.fetchall(), []
            for item in result:
                results.append(item[0])
            return results
        except IndexError:
            return None

    def players_count(self):
        '''Counts total number of player_ids in Players table.'''
        self.c.execute('SELECT COUNT(*) FROM Players')
        return self.c.fetchall()[0][0]

    def cleanup(self):
        '''Cleans the database, shrinking it's size.'''
        self.conn.execute('VACUUM')

    def command_add(self, command, value):
        '''Adds a command to the Commands table.'''
        self.c.execute('INSERT INTO Commands(command, return) VALUES (?, ?)', (command, value))
        self.conn.commit()

    def commands_get(self):
        '''Returns a list containing all commands from the Commands table.'''
        self.c.execute('SELECT command, return FROM Commands')
        result, results = self.c.fetchall(), []
        for item in result:
            results.append(list(item))
        return results

    def command_remove(self, command):
        '''Removes a command from the Commands table.'''
        self.c.execute('DELETE FROM Commands WHERE command = (?)', (command,))
        self.conn.commit()

    def command_edit(self, command, value):
        '''Edits a command in the Commands table.'''
        self.c.execute('UPDATE Commands SET return = (?) WHERE command = (?)', (value, command))
        self.conn.commit()

class MessageGetter:
    __instance = None
    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super(MessageGetter, cls).__new__(cls, *args, **kwargs)
            cls.__instance.db = Database()
            #Strings
            cls.__instance.help_syntax = cls.__instance.db.setting_get('help_syntax')
            #Commands plugin
            cls.__instance.commands_command_help = cls.__instance.db.setting_get('commands_command_help')
            cls.__instance.commands_command_syntax = cls.__instance.help_syntax + cls.__instance.commands_command_help
            #Dictionary plugin
            cls.__instance.dictionary_define_help = cls.__instance.db.setting_get('dictionary_define_help')
            #Help plugin
            cls.__instance.help_help_help = cls.__instance.db.setting_get('help_help_help')
            #Levels plugin
            cls.__instance.levels_rewards_help = cls.__instance.db.setting_get('levels_rewards_help')
            cls.__instance.levels_rewards_syntax = cls.__instance.help_syntax + cls.__instance.levels_rewards_help
            cls.__instance.levels_xpreset_help = cls.__instance.db.setting_get('levels_xpreset_help')
            cls.__instance.levels_xpreset_syntax = cls.__instance.help_syntax + cls.__instance.levels_xpreset_help
            cls.__instance.levels_punish_help = cls.__instance.db.setting_get('levels_punish_help')
            cls.__instance.levels_punish_syntax = cls.__instance.help_syntax + cls.__instance.levels_punish_help
            cls.__instance.levels_rank_help = cls.__instance.db.setting_get('levels_rank_help')
            cls.__instance.levels_top3_help = cls.__instance.db.setting_get('levels_top3_help')
            cls.__instance.levels_reward_achieved_reason = cls.__instance.db.setting_get('levels_reward_achieved_reason')
            cls.__instance.levels_rewards_add_added_reason = cls.__instance.db.setting_get('levels_rewards_add_added_reason')
            cls.__instance.levels_rewards_add_message = cls.__instance.db.setting_get('levels_rewards_add_message')
            cls.__instance.levels_rewards_remove_removed_reason = cls.__instance.db.setting_get('levels_rewards_remove_removed_reason')
            cls.__instance.levels_rewards_remove_message = cls.__instance.db.setting_get('levels_rewards_remove_message')
            cls.__instance.levels_rewards_edit_message = cls.__instance.db.setting_get('levels_rewards_edit_message')
            cls.__instance.levels_punish_punished = cls.__instance.db.setting_get('levels_punish_punished')
            cls.__instance.levels_level_one_message = cls.__instance.db.setting_get('levels_level_one_message')
            cls.__instance.levels_rewards_edit_reward_added_reason = cls.__instance.db.setting_get('levels_rewards_edit_reward_added_reason')
            cls.__instance.levels_rewards_edit_reward_removed_reason = cls.__instance.db.setting_get('levels_rewards_edit_reward_removed_reason')
            cls.__instance.levels_rewards_edit_level_same = cls.__instance.db.setting_get('levels_rewards_edit_level_same')
            #Presence plugin
            cls.__instance.presence_presence_help = cls.__instance.db.setting_get('presence_presence_help')
            cls.__instance.presence_presence_syntax = cls.__instance.help_syntax + cls.__instance.presence_presence_help
            #Utilities plugin
            cls.__instance.utilities_settings_help = cls.__instance.db.setting_get('utilities_settings_help')
            cls.__instance.utilities_settings_syntax = cls.__instance.help_syntax + cls.__instance.utilities_settings_help
            cls.__instance.utilities_clear_help = cls.__instance.db.setting_get('utilities_clear_help')
            cls.__instance.utilities_clear_syntax = cls.__instance.help_syntax + cls.__instance.utilities_clear_help
            #Welcome plugin
            cls.__instance.welcome_welcome_help = cls.__instance.db.setting_get('welcome_welcome_help')
            cls.__instance.welcome_welcome_syntax = cls.__instance.help_syntax + cls.__instance.welcome_welcome_help
        return cls.__instance