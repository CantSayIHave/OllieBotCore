
import time
import random
import json
import sys
import os

from discord.ext import commands
from datetime import datetime
import global_util
from global_util import *
from containers import *

import admin, feeds, fun, music, responses, server_utils, think, sense

# shortened music commands to be replaced
music_commands = {'cq': 'queue clear',
                  'qc': 'queue clear',
                  'p': 'play',
                  'q': 'queue',
                  'd': 'disconnect',
                  'sk': 'skip',
                  'se': 'search',
                  'lq': 'queue listall',
                  'ql': 'queue listall',
                  'ps': 'pause',
                  'sh': 'shuffle',
                  'c': 'current track info'}

random.seed()

"""
DONE:
add server to bot - add 1st mod
add quotes
add server AUTOMAGICALLY
replaced mention w/ id
remove server from bot
rename server
remove quotes
quote timer
reeeeeeee
rss
quote author
custom help
add autoplay
add search
implement help -> inbox
add PM blocks
add shortened commands
add shuffle
add help
wiki
reee response
emote suggest
music bind
repl
block commands
timeout commands
restructure build from file
proxy message sending
restructure
roll
bun

TODO:
musac
 add timeout (maybe)
RemindMe (maybe)
command control (maybe) (kinda did)
add bot shutdown and restart (eh)

"""

async_exit_timer = 0

sync_exit_timer = 0

sync_shutdown = False

startup_extensions = ["admin", "server_utils", "feeds", "fun", "responses", "music"]


class BotContainer:
    def __init__(self, **kwargs):

        self.name = kwargs.get('name', 'Default')
        self.servers = kwargs.get('servers', [])
        self.token = kwargs.get('token', '')
        self.desc = kwargs.get('desc', 'No desc')
        self.prefix = kwargs.get('prefix', '.')
        self.playing_message = kwargs.get('playing_msg', 'world domination')
        self.admin_list = kwargs.get('admins', [])

        self.bot = commands.Bot(command_prefix=self.prefix, description=self.desc)

        self.bot.remove_command('help')
        self.music_loading = False  # for use in youtube-dl loading
        self.print_log = ""  # For use with prints

        self.bot.local_servers = self.servers
        self.bot.local_token = self.token
        self.bot.local_desc = self.desc
        self.bot.playing_message = self.playing_message

        self.debug_timer = None

        self.cogs = []

        @self.bot.event  # ---------------------- Main Message Entry ---------------------- #
        async def on_message(message):
            global exit_timer
            """if message.embeds:
                print(message.embeds[0])"""
            exit_timer = 0

            if message.author.id == self.bot.user.id:  # bot should not read own messages
                return

            # last minute fix so .command list works
            # because why work more and do it right
            lstart = message.content.find(' list')
            if lstart != -1:
                if lstart + 5 >= len(message.content):
                    message.content = message.content.replace(' list', ' listall')
                else:
                    if message.content[lstart + 5] == ' ':
                        message.content = message.content.replace(' list', ' listall')

            message.content = message.content.replace('b-ify', 'b_ify')
            message.content = message.content.replace('nick-all', 'nick_all')

            # Avoid server-related content if in direct message
            if not message.server:
                await self.bot.process_commands(message)
                return

            in_server = get_server(message.server.id, self.bot)

            if message.content.find('-t') == 0 and has_high_permissions(message.author, in_server):  # initiate timer!
                message.content = message.content.replace('-t', '', 1)
                self.debug_timer = True

            # skip blocked and spam timed commands
            if len(message.content) > 0:
                if message.content[0] == self.prefix:
                    if not has_high_permissions(message.author, in_server):
                        root_cmd = message.content.split(' ')[0]
                        root_cmd = root_cmd.replace(self.bot.command_prefix, '')

                        if len(in_server.block_list) > 0:
                            for com in in_server.block_list:  # com is type BlockItem
                                if com.name == root_cmd:
                                    if com.channel == 'all':
                                        return
                                    elif com.channel == message.channel.id:
                                        return

                        if root_cmd in in_server.spam_timers:
                            if in_server.spam_timers[root_cmd] > 0:
                                return
                            else:
                                in_server.spam_timers[root_cmd] = in_server.command_delay * 60

            # finds a reee not at start
            reee_start = message.content.lower().find('reee')
            if reee_start > -1 and (in_server.reee is True) and (
                        message.author.id != self.bot.user.id):  # this covers both None (-1) and message start (0)

                if self.is_rear_terminated(message.content.lower(), reee_start):
                    if reee_start + 4 < len(message.content):
                        terminated = False
                        whitespace = False
                        for letter in message.content.lower()[reee_start + 4:]:
                            if letter != 'e':
                                terminated = True
                                if letter == ' ':
                                    whitespace = True
                                break
                        # if reee terminates against end or against whitespace
                        if (not terminated) or (terminated and whitespace):
                            await self.bot.send_message(message.channel,
                                                        message.author.mention + ' ' + in_server.reee_message)
                    else:
                        await self.bot.send_message(message.channel,
                                                    message.author.mention + ' ' + in_server.reee_message)

            if not get_server_by_name(message.server.name, self.bot):  # server auto-add
                real_server = get_server(message.server.id, self.bot)
                if real_server:
                    real_server.name = message.server.name  # handle server name changes
                    writeBot(self.bot)
                else:
                    self.servers.append(
                        Server(name=message.server.name,
                               mods=[message.server.owner.id],
                               command_delay=1,
                               id=message.server.id))
                    writeBot(self.bot)

            await responses.execute_responses(message, self.bot, in_server)

            # shortened music commands
            if message.content.find('{0}music'.format(self.bot.command_prefix)) == 0:

                if in_server.music_chat:
                    if type(in_server.music_chat) is discord.Channel:
                        if (message.channel.id != in_server.music_chat.id) and not has_high_permissions(message.author, in_server):
                            return

                command_list = message.content.split(' ')
                if len(command_list) > 1:
                    if command_list[1] in music_commands:
                        command_list[1] = music_commands[command_list[1]]
                        message.content = ' '.join(command_list)

            if message.content.lower() == 'f':
                await self.bot.add_reaction(message, '🇫')

            if message.content.lower() == '<:owo:392462319617179659>':
                owo = discord.Emoji(name='owo', id='392462319617179659', server=message.server, require_colons=True)
                await self.bot.add_reaction(message, owo)

            if '🅱' in message.content.lower() and len(message.content) < 2:
                await self.bot.add_reaction(message, '🐝')

            if '🐝' in message.content.lower() and len(message.content) < 2:
                await self.bot.add_reaction(message, '🅱')

            await sense.sense(self.bot, message)

            if self.debug_timer:
                self.debug_timer = self.get_micros()

            await self.bot.process_commands(message)

            if self.debug_timer:
                self.debug_timer = self.get_micros() - self.debug_timer
                await self.bot.send_message(message.channel,
                                            'processing took {} microseconds'.format(self.debug_timer))
                self.debug_timer = None

        @self.bot.event
        async def on_ready():
            print('Logged in as')
            print(self.bot.user.name)
            print(self.bot.user.id)
            print('---------------')
            await self.bot.change_presence(game=discord.Game(name=self.playing_message, type=0))
            self.id = self.bot.user.id

        @self.bot.event
        async def on_member_join(member):
            in_server = get_server(member.server.id, self.bot)

            out_msg = in_server.join_message.replace('@u', member.mention)

            print('Join event on {}'.format(in_server.name))

            if in_server.join_channel:
                await self.bot.send_message(discord.Object(id=in_server.join_channel), out_msg)
            else:
                await self.bot.send_message(discord.Server(id=in_server.id), out_msg)

        @self.bot.command(pass_context=True)
        async def bot(ctx, arg: str = None, arg2: str = None, token_in: str = None, prefix_in: str = None):
            if not checkAdmin(ctx.message.author.id):
                return

            global bots
            if arg == 'list':
                await self.bot.say('Current bot list:')
                for b in bots:
                    await self.bot.say(b.name)

            elif arg == 'new':
                for b in bots:
                    if b.name == arg2:
                        await self.bot.say('Sorry, bot name taken.')  # Search for bot name before adding
                        return

                if arg2 and token_in:
                    if prefix_in:
                        newbot = BotContainer(name=arg2, token=token_in, prefix=prefix_in)
                    else:
                        newbot = BotContainer(name=arg2, token=token_in)
                    bots.append(newbot)
                    writeBot(newbot.bot)
                    newbot.run()
                    await self.bot.say('Bot ' + newbot.name + ' added!')

            elif arg and arg2:
                for b in bots:
                    if b.name == arg:
                        if arg2 == 'listservers':
                            await self.bot.say('Current server list for ' + b.name + ':')
                            for s in b.servers:
                                await self.bot.say('`' + s.name + '`')
                        elif arg2 == 'renameserver':
                            if token_in and prefix_in:
                                old_name = token_in
                                new_name = prefix_in
                                for s in b.servers:
                                    if s.name == old_name:
                                        s.name = new_name
                                        await self.bot.say(b.name + ' server ' + old_name + ' changed to ' + new_name)
                                        writeBot(b.bot)
                                        return
                            else:
                                await self.bot.say('Please provide current and new server names as arguments')

            if arg == 'help':
                await self.bot.send_message(ctx.message.author,
                                            '**Bot usage**:\n'
                                            '`{0}bot <list>`\n'
                                            '`{0}bot <new> [name] [token] [prefix]`\n'
                                            '`{0}bot [bot name] <listservers>`\n'
                                            '`{0}bot [bot name] <renameserver> [current name] [new name]`\n'
                                            'Bot command used for bot addition, removal, and management'.format(
                                                self.bot.command_prefix))

    def run(self):
        self.bot.run(self.token)

    @staticmethod
    def is_rear_terminated(content: str, start: int):
        if start == 0:
            return True
        if start > 0 and content[start - 1] == ' ':
            return True
        return False

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


async def delete_messages():
    while True:
        await asyncio.sleep(1)
        for d in global_util.delete_queue:  # type: DeleteMessage
            d.timer -= 1
            if d.timer <= 0:
                try:
                    await d.bot.delete_message(d.message)
                except Exception:
                    print('Failed to delete a message.')
                global_util.delete_queue.remove(d)


async def background_async():
    global bots, out_messages, rss_timer, alive_timer, exit_timer, async_exit_timer, sync_exit_timer, loop
    while True:
        await asyncio.sleep(10)
        try:
            while len(out_messages) > 0:
                try:
                    msg_out = out_messages.popleft()  # type: ProxyMessage
                    if msg_out.embed is None:
                        await msg_out.bot.send_message(msg_out.channel, msg_out.content)
                    else:
                        await msg_out.bot.send_message(msg_out.channel, em=msg_out.embed)
                except Exception as e:
                    print('Proxy sender failed at {}'.format(e))

            for b in bots:
                for s in b.servers:  # type: Server

                    for c in s.commands:
                        delay = int(c['timer'])
                        if delay > 0:
                            delay -= 10
                            c['timer'] = delay

                    for c in s.spam_timers:
                        if s.spam_timers[c] > 0:
                            s.spam_timers[c] -= 10

                    s.response_lib.dec_spam_timers(10)

                    try:
                        await music.music_autoplay(s, b.bot)
                    except Exception as e:
                        print('Music autoplay failed at: ' + str(e))

            print('Alive ' + str(alive_timer))

            alive_timer += 1
            if alive_timer > 6:
                alive_timer = 0

            rss_timer += 10

            if rss_timer >= TIME_RSS_LOOP:
                rss_timer = 0
                print('rss event')
                for b in bots:  # type: BotContainer
                    for s in b.servers:  # type: Server
                        for r in s.rss:  # type: dict
                            r_type = r['type']
                            if r_type == 'twitter':
                                try:
                                    await b.bot.loop.run_in_executor(def_executor, feeds.scrape_twitter(b, s, r))
                                except Exception as e:
                                    print('Twitter scrape failed with error: {}'.format(e))

                            elif r_type == 'twitch':
                                try:
                                    await feeds.scrape_twitch(b, s, r)
                                except Exception as e:
                                    print('Twitch scrape failed with error: {}'.format(e))

                            elif r_type == 'youtube':
                                try:
                                    await feeds.scrape_youtube(b, s, r)
                                except Exception as e:
                                    print('Youtube scrape failed with error: {}'.format(e))

            exit_timer += 10
            if exit_timer >= TIME_RESPONSE_EXIT and not global_util.save_in_progress:  # kill at 15 min
                exit(1)

            if global_util.internal_shutdown and (not global_util.save_in_progress):
                print('async shutting down...')
                flush_delete_queue()
                asyncio.sleep(2)
                for bc in bots:
                    bc.bot.logout()
                break

        except Exception as e:
            print('Async task loop error: {}'.format(e))
    # loop.stop()


# Load bots
# | File Format: json, 1 dict
with open('globals/bots.json', 'r') as f:
    bot_names = json.load(f)
    for b_name in bot_names['bots']:

        with open('bots/' + b_name + '/' + b_name + '.json', 'r') as ff:
            bot_data = json.load(ff)
            server_list = []

            for s_name in bot_data['server_names']:
                with open('bots/' + b_name + '/' + s_name + '/' + s_name + '.json', 'r') as fi:
                    server_data = json.load(fi)
                    s_id = server_data['id']
                    s_cmd_delay = server_data['cmd_delay']
                    s_reee = server_data['reee']
                    s_rolemods = server_data['rolemods']
                    s_block_list = []
                    s_spam_list = server_data['spam_list']
                    s_join_msg = server_data['join_msg']
                    s_join_channel = server_data['join_channel']

                    for com in server_data['block_list']:
                        s_block_list.append(BlockItem(**com))

                with open('bots/' + b_name + '/' + s_name + '/' + 'mods.json', 'r') as fi:
                    server_mods = json.load(fi)
                    s_mods = server_mods['server_mods']

                with open('bots/' + b_name + '/' + s_name + '/' + 'quotes.json', 'r') as fi:
                    server_quotes = json.load(fi)
                    s_commands = server_quotes['quotes']  # should be a list of dicts

                with open('bots/' + b_name + '/' + s_name + '/' + 'rss.json', 'r') as fi:
                    server_rss = json.load(fi)
                    s_rss = server_rss['rss']  # should be a list of dicts

                with open('bots/' + b_name + '/' + s_name + '/' + 'music.json', 'r') as fi:
                    s_queue = []
                    try:
                        server_queue = json.load(fi)
                        s_queue = server_queue['queue']  # should be a list of dicts
                    except Exception:
                        pass

                    if not s_queue:
                        s_queue = []

                with open('bots/' + b_name + '/' + s_name + '/' + 'responses.json', 'r') as fi:
                    s_responses = json.load(fi)

                server_list.append(Server(name=s_name,
                                          mods=s_mods,
                                          commands=s_commands,
                                          rss=s_rss,
                                          command_delay=s_cmd_delay,
                                          id=s_id,
                                          rolemods=s_rolemods,
                                          block_list=s_block_list,
                                          spam_timers=s_spam_list,
                                          reee_msg=s_reee,
                                          join_msg=s_join_msg,
                                          join_channel=s_join_channel,
                                          responses=s_responses,
                                          queue=s_queue))  # Server Build

            bots.append(BotContainer(name=b_name,
                                     token=bot_data['token'],
                                     desc=bot_data['desc'],
                                     prefix=bot_data['prefix'],
                                     playing_msg=bot_data['playing_msg'],
                                     servers=server_list,
                                     admin_list=admins))
            print('Loaded bot {}'.format(b_name))

"""
for bt in bots:
    for extension in startup_extensions:
        try:
            bt.bot.load_extension(extension)
            print('Loaded {}'.format(extension))
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))"""


for bt in bots:
    bt.cogs.append(admin.setup(bt.bot))
    bt.cogs.append(feeds.setup(bt.bot))
    bt.cogs.append(fun.setup(bt.bot))
    bt.cogs.append(music.setup(bt.bot))
    bt.cogs.append(responses.setup(bt.bot))
    bt.cogs.append(server_utils.setup(bt.bot))
    bt.cogs.append(think.setup(bt.bot))
    bt.cogs.append(sense.setup(bt.bot))


# Full bot loop
# | Create loop, assign tasks, start, restart upon exception

loop = asyncio.get_event_loop()

for bt in bots:
    loop.create_task(bt.bot.start(bt.token))

loop.create_task(twitch.initialize())
loop.create_task(delete_messages())

try:
    loop.run_until_complete(background_async())
finally:
    try:
        loop.close()
    except Exception:
        exit(5)

if global_util.internal_shutdown:
    exit(5)
exit(1)

# bot.run('MzM4NTA2OTA1NjgzMjMwNzIw.DFWayQ.BVYncs5BtVdoPsYEhJvTHqBpy9o')
# bot.self_bot=False
