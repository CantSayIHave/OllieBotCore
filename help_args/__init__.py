"""
Help args

Help documentation for each command
"""

from .fun import *
from .utilities import *
from .admin import *
from . import music

help_taglines = {'audioconvert': {'d': 'convert audio to different format', 'm': False},
                 'clear': {'d': 'clear bot messages', 'm': True},
                 'cat': {'d': 'summon a cat', 'm': False},
                 'b-ify': {'d': 'add some 🅱️ to text', 'm': False},
                 'bigtext': {'d': 'transform text into regional indicators', 'm': False},
                 'block': {'d': 'block any command from non-mods', 'm': True},
                 'bun': {'d': 'summon a bun', 'm': False},
                 'emotes': {'d': 'suggest server emotes to the mods', 'm': False},
                 'good': {'d': 'easy way to check if bot is online', 'm': True},
                 'getraw': {'d': 'get raw text from a message', 'm': True},
                 'imageconvert': {'d': 'convert image to different format', 'm': False},
                 'info': {'d': 'get bot info', 'm': False},
                 'music': {'d': 'manage/play music from youtube', 'm': False},
                 'perm': {'d': 'set user permissions', 'm': True},
                 'purge': {'d': 'mass-clear messages', 'm': True},
                 'playing': {'d': "set bot's 'playing' message", 'm': True},
                 'prefix': {'d': "set bot's command prefix", 'm': True},
                 'quote': {'d': 'manage/call quotes', 'm': True},
                 'react': {'d': 'react to a message with bigtext', 'm': False},
                 'reee': {'d': 'manage autistic screaming response', 'm': True},
                 'response': {'d': 'manage custom responses', 'm': True},
                 'roles': {'d': 'automate mass roll assignments', 'm': True},
                 'roll': {'d': 'dice roller', 'm': False},
                 'rss': {'d': 'manage rss feeds for each channel', 'm': True},
                 'spamtimer': {'d': 'set spam timer for quotes', 'm': True},
                 'think': {'d': 'really makes you think', 'm': False},
                 'unblock': {'d': 'unblock commands', 'm': True},
                 'usrjoin': {'d': 'manage message to new users', 'm': True},
                 'ytdl': {'d': 'youtube to mp3 converter', 'm': True},
                 'wiki': {'d': 'search Wikipedia for something', 'm': False},
                 'woof': {'d': 'summon a woof', 'm': False}}
