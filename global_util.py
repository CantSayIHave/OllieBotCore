import discord
from discord.ext import commands
import json
import os
import errno
from collections import deque
import twitter
import asyncio
import concurrent.futures
from youtubeapi import YoutubeAPI
import twitch_rss
from worldtime import  *
from response import *
from api_keys import *
from containers import *


class Server:
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'Default')
        self.mods = kwargs.get('mods', [])
        self.commands = kwargs.get('commands', [])
        self.rss = kwargs.get('rss', [])
        self.command_delay = kwargs.get('command_delay', 1)
        self.reee_message = kwargs.get('reee_msg', 'stop hitting yourself')
        self.id = kwargs.get('id', '')
        self.reee = kwargs.get('reee_state', True)
        self.rolemods = kwargs.get('rolemods', [])
        self.spam_timers = kwargs.get('spam_timers', {})  # custom spam timed commands
        self.block_list = kwargs.get('block_list', [])
        self.bot_voice_client = None  # actual voice client - for autoplay
        self.search_results = None
        self.suggest_emotes = []
        self.music = deque(kwargs.get('queue', []))
        self.music_player = None
        self.music_chat = None  # normally set to channel
        self.music_channel = None  # chat channel player is bound to - for autoplay
        self.music_loading = False
        self.music_timer = None  # timer for client disconnect
        self.late = None
        self.current_track = None
        self.vote_skip = None

        # 12/13/17 update
        self.join_message = kwargs.get('join_msg', 'Welcome to the server, @u!')
        self.join_channel = kwargs.get('join_channel', '')

        self.response_lib = ResponseLibrary(self.command_delay)

        responses = kwargs.get('responses', None)
        if responses:
            for r in responses:
                self.response_lib.add(Response(**r))

    def run_command(self, bot, command: str):
        for row in self.commands:
            if command == row[0]:  # add timeout here
                return row[1]
        return None

    def is_mod(self, checkid: str):
        for x in self.mods:
            if x == checkid:
                return True
        return False

    async def add_music_url(self, url: str, requestee: str):
        try:
            vid_id = yt_extract_id(url)
        except Exception as er:
            print('add_music_url error: ' + str(er))
            return
        if vid_id:
            vid = await yt.get_video_info(vid_id)  # type: dict
            if vid:
                self.music.append({'url': url, 'title': vid['snippet']['title'], 'user': requestee})
                return vid
        return False

    def add_music_raw(self, url: str, title: str, requestee: str):
        self.music.append({'url': url, 'title': title, 'user': requestee})

    def get_music_url(self):
        try:
            song = self.music.popleft()
            self.current_track = song
            return song
        except Exception:
            return None

    def get_track_pos(self, url):
        for i, track in enumerate(self.music):
            if track['url'] == url:
                return i + 1

    def music_timeout(self):
        if not self.music_timer:
            self.music_timer = 0
            return False
        else:
            self.music_timer += 10

            if self.music_timer >= TIME_MUSIC_TIMEOUT:
                self.music_timer = None
                return True
            return False

    def vote_skip_register(self, member: discord.Member):
        if not self.vote_skip:
            self.vote_skip = []
        if member.id not in self.vote_skip:
            self.vote_skip.append(member.id)
            return True
        return False

    def vote_skip_check(self, channel: discord.Channel):
        if channel.type != discord.ChannelType.voice and channel.type != 'voice':
            return None
        if not self.vote_skip:
            return None
        if not channel.voice_members:
            return None
        if len(channel.voice_members) < 1:
            return None
        if (len(self.vote_skip) / len(channel.voice_members)) - 1 >= (2/3):
            self.vote_skip = None
            return True
        return False

    def vote_skip_clear(self):
        self.vote_skip = None


# Writes admin list to file
def writeAdmins(admins: list):
    global save_in_progress
    save_in_progress = True

    with open('globals/admins.json', 'w') as f:
        json.dump(admins, f)

    save_in_progress = False


# Check if user is admin
def checkAdmin(name: str):
    global admins
    for x in admins:
        if name == x:
            return True
    return False


# Returns a BotContainer by name
def get_bot(name: str):
    global bots
    for b in bots:
        if b.name == name:
            return b
    return None


# Writes a bot to file
def writeBot(b):
    global bots, save_in_progress
    bc = bc_from_bot(b)
    save_in_progress = True

    try:
        os.makedirs('bots/' + bc.name)  # Make name directory in bots folder
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    with open('bots/' + bc.name + '/' + bc.name + '.json', 'w') as f:

        bot_dict = {'token': b.local_token,
                    'desc': b.local_desc,
                    'prefix': b.command_prefix,
                    'playing_msg': b.playing_message}

        s_names = []
        for s in b.local_servers:
            s_names.append(s.name)  # Write server names into bot data file

        bot_dict['server_names'] = s_names

        json.dump(bot_dict, f)

    for s in b.local_servers:  # type: Server
        try:
            os.makedirs('bots/' + bc.name + '/' + s.name)  # Make server name directory in bots folder
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        with open('bots/' + bc.name + '/' + s.name + '/' + s.name + '.json', 'w') as fi:

            server_dict = {'id': s.id,
                           'cmd_delay': s.command_delay,
                           'reee': s.reee_message,
                           'rolemods': s.rolemods,
                           'block_list': [x.__dict__ for x in s.block_list],
                           'spam_list': s.spam_timers,
                           'join_msg': s.join_message,
                           'join_channel': s.join_channel}

            json.dump(server_dict, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'mods.json', 'w') as fi:
            s_mods = {'server_mods': s.mods}

            json.dump(s_mods, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'quotes.json', 'w') as fi:
            s_quotes = {'quotes': s.commands}

            json.dump(s_quotes, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'rss.json', 'w') as fi:
            s_rss = {'rss': [x.__dict__ for x in s.rss]}

            json.dump(s_rss, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'responses.json', 'w') as fi:
            s_responses = [x.__dict__ for x in s.response_lib.responses]

            json.dump(s_responses, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'music.json', 'w') as fi:
            s_music = {'queue': list(s.music)}

            json.dump(s_music, fi)

    with open('globals/bots.json', 'w') as f:  # IMPORTANT: writes bot names into bots.json* in globals
        bot_list = []
        for bo in bots:
            bot_list.append(bo.name)

        bots_dict = {'bots': bot_list}

        json.dump(bots_dict, f)

    save_in_progress = False


def writeRss(b, s):
    global save_in_progress
    b = bc_from_bot(b)
    if b and s:
        save_in_progress = True

        with open('bots/' + b.name + '/' + s.name + '/' + 'rss.json', 'w') as fi:
            s_rss = {'rss': s.rss}

            json.dump(s_rss, fi)

        save_in_progress = False


def writeServerData(b, s: Server):
    global save_in_progress
    bc = bc_from_bot(b)
    if bc and s:
        save_in_progress = True

        with open('bots/' + bc.name + '/' + s.name + '/' + s.name + '.json', 'w') as fi:
            server_dict = {'id': s.id,
                           'cmd_delay': s.command_delay,
                           'reee': s.reee_message,
                           'rolemods': s.rolemods,
                           'block_list': [x.__dict__ for x in s.block_list],
                           'spam_list': s.spam_timers,
                           'join_msg': s.join_message,
                           'join_channel': s.join_channel}

            json.dump(server_dict, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'mods.json', 'w') as fi:
            s_mods = {'server_mods': s.mods}

            json.dump(s_mods, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'quotes.json', 'w') as fi:
            s_quotes = {'quotes': s.commands}

            json.dump(s_quotes, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'rss.json', 'w') as fi:
            s_rss = {'rss': s.rss}

            json.dump(s_rss, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'responses.json', 'w') as fi:
            s_responses = [x.__dict__ for x in s.response_lib.responses]

            json.dump(s_responses, fi)

        with open('bots/' + bc.name + '/' + s.name + '/' + 'music.json', 'w') as fi:
            s_music = {'queue': list(s.music)}

            json.dump(s_music, fi)

        save_in_progress = False


def writeResponses(b: discord.ext.commands.Bot, s: Server):
    global save_in_progress
    bc = bc_from_bot(b)
    save_in_progress = True

    with open('bots/' + bc.name + '/' + s.name + '/' + 'responses.json', 'w') as fi:
        s_responses = [x.__dict__ for x in s.response_lib.responses]

        json.dump(s_responses, fi)

    save_in_progress = False


def proxy_message(bot, channel_id: str, content: str, embed: discord.Embed = None):
    global out_messages
    out_messages.append(ProxyMessage(bot=bot,
                                     channel=discord.Object(id=channel_id),
                                     content=content,
                                     embed=embed))


def writeBotData(b):
    global save_in_progress
    bc = bc_from_bot(b)
    save_in_progress = True

    with open('bots/' + bc.name + '/' + bc.name + '.json', 'w') as f:
        bot_dict = {'token': b.local_token,
                    'desc': b.local_desc,
                    'prefix': b.command_prefix,
                    'playing_msg': b.playing_message}

        s_names = []
        for s in b.local_servers:
            s_names.append(s.name)  # Write server names into bot data file

        bot_dict['server_names'] = s_names

        json.dump(bot_dict, f)

    save_in_progress = False


def writeMusic(b, s):
    global save_in_progress
    bc = bc_from_bot(b)
    save_in_progress = True

    try:
        os.makedirs('bots/' + bc.name + '/music')  # Make name directory in bots folder
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open('bots/' + bc.name + '/' + s.name + '/' + 'music.json', 'w') as fi:
        s_music = {'queue': list(s.music)}

        json.dump(s_music, fi)

        save_in_progress = False


def has_high_permissions(user: discord.User, s: Server = None, b=None):  # check for mod OR admin
    if checkAdmin(user.id):
        return True

    if b:
        for s in b.local_servers:
            if s.is_mod(user.id):
                return True

            if type(user) is discord.Member:
                for r in s.rolemods:
                    for sr in user.roles:  # is actually member
                        if sr.id == r:
                            return True

    if s:
        if s.is_mod(user.id):
            return True

        if type(user) is discord.Member:
            for r in s.rolemods:
                for sr in user.roles:  # is actually member
                    if sr.id == r:
                        return True
    return False


def get_server(id: str, bot) -> Server:
    for s in bot.local_servers:
        if s.id == id:
            return s
    return None


def get_server_by_name(name: str, bot) -> Server:
    for s in bot.local_servers:
        if s.name == name:
            return s
    return None


def get_quote(in_server, in_name, do_spam=False):
    for c in in_server.commands:
        if do_spam:
            if c['name'] == in_name:
                return c
        else:
            if c['name'] == in_name and int(c['timer']) < 1:
                c['timer'] = str(in_server.command_delay * 60)
                return c
    return None


def get_rss(in_server, in_channel_id, in_user):
    for c in in_server.rss:
        if c['uid'] == in_user and c['channel'] == in_channel_id:
            return c
    return None


def bc_from_bot(bot):
    global bots
    for b in bots:
        if b.id == bot.user.id:
            return b


def save_backup():
    global save_in_progress
    save_in_progress = True

    os.system('cp -r bots backups')
    os.system('cp -r globals backups')

    save_in_progress = False


def extract_url(arg: str, start: int) -> str:
    out = ''
    for c in arg[start:start + 100]:
        if c == '"':
            break
        out += c
    return out


def yt_shortened_to_long(link: str):
    if 'https://youtu.be' in link:
        link_parts = link.rsplit('/', maxsplit=1)
        try:
            return 'https://www.youtube.com/watch?v={}'.format(link_parts[1])
        except IndexError:
            return None
    return None


def yt_extract_id(url: str):
    if 'youtube' in url and 'v=' in url:
        v_tag = url.rsplit('v=', 1)
        return v_tag[1].split('&')[0]
    elif 'youtu.be' in url:
        return url.rsplit('/', 1)[1]
    return None


def is_num(text: str):
    try:
        num = int(text)
        return num
    except ValueError:
        return None


def flush_delete_queue():
    global delete_queue
    for d in delete_queue:  # type: DeleteMessage
        d.timer = 0


# time in seconds
def schedule_delete(bot, msg, time: int):
    delete_queue.append(DeleteMessage(message=msg, bot=bot, timer=time))


# helper function purely for formatting
def help_form(text: str):
    return text


# Load admins
# | File Format: json, 1 list
with open('globals/admins.json', 'r') as f:
    admins = json.load(f)

exit_timer = 0

out_messages = deque([])  # for proxy message delivery system

delete_queue = []

mute_queue = []

alive_timer = 0

# temp storage for temp admin key
adminKey = ''

# global timer for rss feeds
rss_timer = 60

# global bad timer
bad_timer = 0

internal_shutdown = False

# global save protection
save_in_progress = False

sync_shutdown = False

# default executor
def_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# -----------
#  CONSTANTS
# -----------
CHAR_ZWS = chr(0x200B)

TIME_RESPONSE_EXIT = 900  # in seconds

TIME_RSS_LOOP = 70  # in seconds

TIME_ASYNC_EXIT = 60  # in seconds

TIME_MUSIC_TIMEOUT = 30  # in seconds

OWNER_ID = '305407800778162178'

bots = []

with open('emoji_alphabet.json', 'r', encoding='utf8') as f:
    emoji_alphabet = json.load(f)

twitter_api = twitter.Api(consumer_key=TWITTER_CONSUMER_KEY,
                          consumer_secret=TWITTER_CONSUMER_SECRET,
                          access_token_key=TWITTER_TOKEN_KEY,
                          access_token_secret=TWITTER_TOKEN_SECRET)

yt = YoutubeAPI(key=YOUTUBE_TOKEN)

twitch = twitch_rss.TwitchRss(client_id=TWITCH_CLIENT_ID,
                              client_secret=TWITCH_CLIENT_SECRET,
                              oauth=TWITCH_TOKEN)

worldtime = WorldTime(key=GEO_TIME_TOKEN)

rss_feeds = ['twitter', 'twitch', 'youtube']

rss_colors = {'twitter': 0x00aced,
              'twitch': 0x6441a5,
              'youtube': 0xbb0000}