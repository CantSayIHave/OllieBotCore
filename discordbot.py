import asyncio
import importlib
import random
import re
import time

import discord
from discord.ext import commands

import server
import storage_manager as storage
from cogs import responses, sense, help
from util import global_util

"""
Breaking Changes:
 nvm
"""

"""
ToDo
----
fix all self references
"""

replace_chars = [('“', '"'), ('”', '"'), ('‘', "'"), ('’', "'")]  # need to put this in utils

command_mappings = {'b-ify': 'b_ify',
                    'nick-all': 'nick_all',
                    '8ball': 'eight_ball',
                    'eightball': 'eight_ball',
                    'ps': 'photoshop'}


class DiscordBot(commands.Bot):
    def __init__(self, formatter=None, pm_help=False, **options):
        self.name = options.get('name', 'Default')
        self.local_servers = options.get('servers', [])
        self.token = options.get('token', '')
        self.desc = options.get('desc', 'No desc')
        self.prefix = options.get('prefix', '.')
        self.playing_message = options.get('playing_msg', 'world domination')
        self.admins = options.get('admins', [])
        self.bot_list = options.get('bot_list', [])

        super().__init__(self.prefix, formatter, self.desc, pm_help, **options)

        self.remove_command('help')
        self.music_loading = False  # for use in youtube-dl loading
        self.print_log = ""  # For use with prints

        self.debug_timer = None

        self._cogs = []  # hold cog instances

        self.help_all, self.help_mod = help.build_menus(self)

        @self.event  # ---------------------- Main Message Entry ---------------------- #
        async def on_message(message):
            global_util.exit_timer = 0

            # bot should not read own or other bot messages
            if message.author == self.user or message.author.bot:
                return

            # cant have be a command without content ¯\_(ツ)_/¯
            if not message.content:
                return

            if message.author.id == '340747290849312768':  # eggy
                if message.content.find('{}fren'.format(self.command_prefix)) == 0:
                    await self.send_message(message.channel, '{} is always my fren'.format(message.author.mention))
                    return

            if message.author.id == '238038532369678336':  # cake
                if message.content.find('{}fren'.format(self.command_prefix)) == 0:
                    cake_choice = ['{} is ***always*** by fren',
                                   '{} might ***always*** be my fren',
                                   '{} is never not my fren']
                    await self.send_message(message.channel,
                                            random.choice(cake_choice).format(message.author.mention))
                    return

            # last minute fix so .command list works
            # because why work more and do it right
            if message.content.find(self.command_prefix) == 0:
                message.content = re.sub(r'( list)\b', ' listall', message.content)  # type:str

            # Avoid server-related content if in direct message
            if not message.server:

                message.content = self.map_commands(self.char_swaps(message.content))

                await help.intercept_help(message, self)

                # treat all commands as lowercase
                message.content = self.command_lowercase(message.content)

                await self.process_commands(message)

                if message.author.id in global_util.bypass_perm:
                    global_util.bypass_perm.remove(message.author.id)

                return

            in_server = self.get_server(message.server)

            high_perm = self.has_high_permissions(message.author, in_server)

            await self.handle_tag_prefixes(message, perms=high_perm)

            if await self.handle_blocked(message, in_server, perms=high_perm):
                return

            message.content = self.map_commands(self.char_swaps(message.content))

            await help.intercept_help(message, self)  # intercept help

            content_lower = message.content.lower()  # type: str

            await self.find_reee(content_lower, message, in_server)

            if not self.get_server(name=message.server.name):  # server auto-add and name change update
                real_server = self.get_server(message.server)
                if real_server:
                    real_server.name = message.server.name  # handle server name changes
                    storage.write_bot(self)
                else:
                    new_server = server.Server(name=message.server.name,
                                        mods=[message.server.owner.id],
                                        command_delay=1,
                                        id=message.server.id)
                    self.local_servers.append(new_server)
                    storage.write_bot(self)

            await responses.execute_responses(message, self, in_server, content_lower=content_lower)

            # shortened music commands
            if content_lower.find('{0}music'.format(self.command_prefix)) == 0:

                if in_server.music_chat:
                    if (message.channel.id != in_server.music_chat) and not high_perm:
                        return

                command_list = message.content.split(' ')
                if len(command_list) > 1:
                    if command_list[1] in global_util.music_commands:
                        command_list[1] = global_util.music_commands[command_list[1]]
                        message.content = ' '.join(command_list)

            await self.handle_default_reactions(content_lower, message)

            await sense.sense(self, message)

            if self.debug_timer:
                self.debug_timer = self.get_micros()

            # treat all commands as lowercase
            message.content = self.command_lowercase(message.content)

            await self.process_commands(message)

            if self.debug_timer:
                self.debug_timer = self.get_micros() - self.debug_timer
                await self.send_message(message.channel,
                                        'processing took {} microseconds'.format(self.debug_timer))
                self.debug_timer = None

            if message.author.id in global_util.bypass_perm:
                global_util.bypass_perm.remove(message.author.id)

        @self.event
        async def on_ready():
            print('Logged in as')
            print(self.user.name)
            print(self.user.id)
            print('---------------')
            await self.change_presence(game=discord.Game(name=self.playing_message, type=0))
            self.id = self.user.id

        @self.event
        async def on_member_join(member):
            in_server = self.get_server(member.server)

            out_msg = in_server.join_message.replace('@u', member.mention)

            print('Join event on {}'.format(in_server.name))

            if in_server.join_channel:
                await self.send_message(discord.Object(id=in_server.join_channel), out_msg)
            else:
                await self.send_message(discord.Server(id=in_server.id), out_msg)

        @self.event
        async def on_member_remove(member):
            in_server = self.get_server(member.server)

            if not in_server.leave_channel:
                return

            out_msg = '**{}** has left the server. Goodbye! <:pinguwave:415782912278003713>'.format(member.name)

            await self.send_message(discord.Object(id=in_server.leave_channel), out_msg)

        @self.command(pass_context=True)
        async def bot(ctx, arg: str = None, arg2: str = None, token_in: str = None, prefix_in: str = None):
            if not self.check_admin(ctx.message.author):
                return

            global bots
            if arg == 'list':
                await self.say('Current bot list:')
                for b in bots:
                    await self.say(b.name)

            elif arg == 'new':
                for b in bots:
                    if b.name == arg2:
                        await self.say('Sorry, bot name taken.')  # Search for bot name before adding
                        return

                if arg2 and token_in:
                    if prefix_in:
                        newbot = DiscordBot(name=arg2, token=token_in, prefix=prefix_in)
                    else:
                        newbot = DiscordBot(name=arg2, token=token_in)
                    bots.append(newbot)
                    storage.write_bot(newbot.bot)
                    newbot.run()
                    await self.say('Bot ' + newbot.name + ' added!')

            elif arg and arg2:
                for b in bots:
                    if b.name == arg:
                        if arg2 == 'listservers':
                            await self.say('Current server list for ' + b.name + ':')
                            for s in b.servers:
                                await self.say('`' + s.name + '`')
                        elif arg2 == 'renameserver':
                            if token_in and prefix_in:
                                old_name = token_in
                                new_name = prefix_in
                                for s in b.servers:
                                    if s.name == old_name:
                                        s.name = new_name
                                        await self.say(b.name + ' server ' + old_name + ' changed to ' + new_name)
                                        storage.write_bot(b.bot)
                                        return
                            else:
                                await self.say('Please provide current and new server names as arguments')

            if arg == 'help':
                await self.send_message(ctx.message.author,
                                        '**Bot usage**:\n'
                                        '`{0}bot <list>`\n'
                                        '`{0}bot <new> [name] [token] [prefix]`\n'
                                        '`{0}bot [bot name] <listservers>`\n'
                                        '`{0}bot [bot name] <renameserver> [current name] [new name]`\n'
                                        'Bot command used for bot addition, removal, and management'.format(
                                            self.command_prefix))

    def get_server(self, server: discord.Server = None, name: str = None, id: str = None) -> server.Server:
        test_id = None
        if server:
            test_id = server.id
        elif id:
            test_id = id
        if test_id:
            for s in self.local_servers:
                if s.id == test_id:
                    return s
        if name:
            for s in self.local_servers:
                if s.name == name:
                    return s

    async def handle_blocked(self, message, in_server, perms):
        # skip blocked and spam timed commands
        if len(message.content) > 0:
            if message.content[0] == self.prefix:
                if not perms:
                    root_cmd = message.content.split(' ')[0]
                    root_cmd = root_cmd.replace(self.command_prefix, '')

                    if len(in_server.block_list) > 0:
                        for com in in_server.block_list:  # type: BlockItem
                            if com.name == root_cmd:
                                if com.channel == 'all':
                                    m = await self.send_message(message.channel,
                                                                '`{}` is blocked in all channels'.format(root_cmd))
                                    global_util.schedule_delete(self, m, 3)
                                    return True
                                elif com.channel == message.channel.id:
                                    m = await self.send_message(message.channel,
                                                                '`{}` is blocked in this channel'.format(root_cmd))
                                    global_util.schedule_delete(self, m, 3)
                                    return True

                    if root_cmd in in_server.spam_timers:
                        if in_server.spam_timers[root_cmd] > 0:
                            return True
                        else:
                            in_server.spam_timers[root_cmd] = in_server.command_delay * 60
        return False

    async def find_reee(self, content, message, in_server):
        if not in_server.reee:
            return

        match = re.match(r'(reee+)\b', content, flags=re.IGNORECASE)
        if match:
            await self.send_message(message.channel, '{} {}'.format(message.author.mention, in_server.reee_message))

    async def handle_tag_prefixes(self, message, perms):
        if message.content.find('-p') == 0:
            if perms:
                message.content = message.content.replace('-p', '', 1)
                global_util.bypass_perm.append(message.author.id)

        if message.content.find('-d') == 0:
            await asyncio.sleep(0.2)
            await self.delete_message(message)
            message.content = message.content.replace('-d', '', 1)

        if message.content.find('-t') == 0 and perms:  # initiate timer!
            message.content = message.content.replace('-t', '', 1)
            self.debug_timer = True

    def check_admin(self, user: discord.User):
        return user.id in self.admins

    def has_high_permissions(self, user: discord.User, server: server.Server = None):  # check for mod OR admin
        if user.id in global_util.bypass_perm:
            return False

        if self.check_admin(user):
            return True

        if type(user) is discord.Member:
            server_perm = user.server_permissions  # type:discord.Permissions
            if server_perm.administrator:
                return True

        check_servers = []

        if server:
            check_servers.append(server)
        else:
            check_servers.extend(self.local_servers)

        for s in check_servers:
            if s.is_mod(user):
                return True

            if type(user) is discord.Member:
                for r in s.rolemods:
                    for sr in user.roles:  # is actually member
                        if sr.id == r:
                            return True
        return False

    async def handle_default_reactions(self, content, message):
        if content == 'f':
            await self.add_reaction(message, '🇫')

        if content == '<:owo:392462319617179659>':
            owo = discord.Emoji(name='owo', id='392462319617179659', server=message.server, require_colons=True)
            await self.add_reaction(message, owo)

        if '🅱' in content and len(message.content) < 2:
            await self.add_reaction(message, '🐝')

        if '🐝' in content and len(message.content) < 2:
            await self.add_reaction(message, '💛')
            await self.add_reaction(message, '🖤')
            await self.add_reaction(message, '🐝')

    def load_cogs(self, extensions):
        for ext in extensions:
            m = importlib.import_module(ext)
            self._cogs.append(m.setup(self))

    def test_high_perm(self, func):
        """Decorator for generic server-based high permission test

        Passes found :class:`Server` object as second arg

        """

        async def decorator(ctx, *args):
            if not ctx.message.server:
                await self.bot.send_message(ctx.message.channel,
                                            'Sorry, but this command is only accessible from a server')
                return

            in_server = self.get_server(server=ctx.message.server)
            if not self.has_high_permissions(ctx.message.author, in_server):
                return
            await func(ctx, in_server, *args)
        return decorator

    def test_server(self, func):
        """Decorator for testing for server

        Passes found :class:`Server` object as second arg

        """

        async def decorator(ctx, *args):
            if not ctx.message.server:
                await self.bot.send_message(ctx.message.channel,
                                            'Sorry, but this command is only accessible from a server')
                return

            in_server = self.get_server(server=ctx.message.server)
            await func(ctx, in_server, *args)
        return decorator

    @staticmethod
    def extract_id(text: str):
        if not (text[0] == '<' and text[len(text) - 1] == '>'):
            return None
        begin = text.find('@') + 1
        if text[begin] == '!':
            begin += 1
        end = len(text) - 1
        try:
            num = text[begin:end]
            int(num)
            return num
        except ValueError:
            return None

    @staticmethod
    def get_micros():
        return int(round(time.time() * 1000000))

    @staticmethod
    def char_swaps(content: str) -> str:
        for swap in replace_chars:
            if swap[0] in content:
                content = content.replace(swap[0], swap[1])
        return content

    def map_commands(self, content: str) -> str:
        if content.find(self.command_prefix) == 0:
            command = content[len(self.command_prefix):content.find(' ')]
            if command in command_mappings:
                return self.command_prefix + command_mappings[command] + content[content.find(' '):]
        return content

    def command_lowercase(self, content: str) -> str:
        if content[0] == self.command_prefix:
            command = content[:content.find(' ')]
            if not command.islower():
                return command.lower() + content[content.find(' '):]
        return content
