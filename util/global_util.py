import concurrent.futures
import io
import json
import re
import shlex
from collections import deque

import twitter
from PIL import Image

from api_keys import *
from apis import twitch_rss
from apis.olliebot_web import OllieBotAPI
from apis.worldtime import *
from apis.youtubeapi import YoutubeAPI
from response import *
from util.containers import *


# Returns a BotContainer by name
def get_bot(name: str):
    global bots
    for b in bots:
        if b.name == name:
            return b
    return None


def proxy_message(bot, channel_id: str, content: str, embed: discord.Embed = None):
    global out_messages
    out_messages.append(ProxyMessage(bot=bot,
                                     channel=discord.Object(id=channel_id),
                                     content=content,
                                     embed=embed))


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


def bc_from_bot(bot):
    global bots
    for b in bots:
        if b.id == bot.user.id:
            return b


def extract_url(arg: str, start: int) -> str:
    out = ''
    for c in arg[start:start + 100]:
        if c == '"':
            break
        out += c
    return out


def extract_mention_id(id: str):
    out = ''
    for c in id:
        if c.isdigit():
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


def is_num(text: str, base: int = 10):
    try:
        num = int(text, base)
        return num
    except (ValueError, TypeError):
        return None


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


def strip_args(args: str) -> list:
    arg_list = shlex.split(args, ' ')
    out_list = []
    for a in arg_list:
        if a:
            pieces = a.split('=')
            out_list.append((pieces[0], pieces[1]))
    return out_list


def flush_delete_queue():
    global delete_queue
    for d in delete_queue:  # type: DeleteMessage
        d.timer = 0


def replace_color(img: Image.Image, base_color: int, with_color: int, variance: int):
    red = (base_color & 0xff0000) >> 16
    green = (base_color & 0xff00) >> 8
    blue = base_color & 0xff

    with_red = (with_color & 0xff0000) >> 16
    with_green = (with_color & 0xff00) >> 8
    with_blue = with_color & 0xff

    pixels = img.load()

    for y in range(img.size[1]):
        for x in range(img.size[0]):
            at = pixels[x, y]

            # at[0:4] -> [red, green, blue, alpha]

            if abs(red - at[0]) <= variance and abs(green - at[1]) <= variance and abs(blue - at[2]) <= variance:
                pixels[x, y] = (with_red, with_green, with_blue, at[3])  # keep original alpha | alpha-blind


async def get_json(page: str) -> dict:
    with aiohttp.ClientSession() as session:
        async with session.get(page) as resp:
            if resp.status == 200:
                d = await resp.json()
                return d

async def get_image(url: str):
    try:
        with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    image_bytes = await resp.read()

                    image = Image.open(io.BytesIO(image_bytes))
                    image = image.convert('RGBA')
                    return image
    except Exception:
        return None


def extract_image_url(arg, msg: discord.Message):
    if type(arg) is str and arg.startswith('http'):
        return arg
    if msg.attachments:
        return msg.attachments[0]['url']
    if msg.embeds:
        return msg.embeds[0]['url']


def extract_filename(path):
    if '.' in path[-5:]:
        matches = re.findall(r'\b[a-zA-Z]+\.[a-zA-Z]{3}\b', path)
        if matches:
            return matches[-1]

    matches = re.findall(r'\b([a-zA-Z]+)', path)

    if matches:
        return matches[-1]

    return path


# i forgot what non-builtin attributes are called so it's "new"
def get_new_attr(thing):
    return (x for x in thing.__dict__ if not x.startswith('__'))


# time in seconds
def schedule_delete(bot, msg, time: int):
    delete_queue.append(DeleteMessage(message=msg, bot=bot, timer=time))


def schedule_future(coro, time: int):
    coro_queue.append(TimedFuture(coro=coro, timer=time))


# helper function purely for formatting
def help_form(text: str):
    return text


# global save protection
save_in_progress = False


# save_in_progress decorator
def global_save(func):

    def decorator(*args, **kwargs):
        global save_in_progress
        save_in_progress = True
        func(*args, **kwargs)
        save_in_progress = False
    return decorator


exit_timer = 0

out_messages = deque([])  # for proxy message delivery system

delete_queue = []

coro_queue = []

mute_queue = []

bypass_perm = []

alive_timer = 0

# temp storage for temp admin key
adminKey = ''

# global timer for rss feeds
rss_timer = 60

# global bad timer
bad_timer = 0

internal_shutdown = False

sync_shutdown = False

# default executor
def_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)

# -----------
#  CONSTANTS
# -----------
CHAR_ZWS = chr(0x200B)

TITLE_BAR = '───────────────────────'

TIME_RESPONSE_EXIT = 300  # in seconds

TIME_RSS_LOOP = 70  # in seconds

TIME_ASYNC_EXIT = 60  # in seconds

TIME_MUSIC_TIMEOUT = 120  # in seconds

OWNER_ID = '305407800778162178'

MUSIC_QUEUE_LIMIT = 50

with open('resources/emoji_alphabet.json', 'r', encoding='utf8') as f:
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

olliebot_api = OllieBotAPI(OLLIEBOT_TOKEN)

rss_feeds = ['twitter', 'twitch', 'youtube']

rss_colors = {'twitter': 0x00aced,
              'twitch': 0x6441a5,
              'youtube': 0xbb0000}

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


hug_library = []
pat_library = []


num2word = {'0': 'zero',
            '1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine'}