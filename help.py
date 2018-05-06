import discord
from discord.ext import commands
from global_util import *
from containers import *
import paginator


help_args = {'audioconvert': {'d': 'convert audio to different format', 'm': False},
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


class Help:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def help(ctx):
            global help_args

            def list_help(args, high_perm):
                for arg in args:  # type: str
                    if help_args[arg]['m'] and high_perm:
                        yield EmbedField(name=arg,
                                         value=help_args[arg]['d'].capitalize(),
                                         inline=False)
                    elif not help_args[arg]['m']:
                        yield EmbedField(name=arg,
                                         value=help_args[arg]['d'].capitalize(),
                                         inline=False)

            info = 'Commands follow the format\n\n`'
            info += '{0}command <required arguments> [optional arguments]`\n\n' \
                    'Note that `optional arguments` means an argument must be provided, ' \
                    'but it can be anything. For example, in:\n\n' \
                    '`{0}music <play/queue> [link/query/search number]`\n\n' \
                    'the arguments provided in <play/queue> **must** be either `play` ' \
                    'or `queue`, but the next argument may be either a youtube link, ' \
                    'a query, or a search result number like so:\n\n`' + \
                    '{0}music play https://www.youtube.com/watch?v=tVj0ZTS4WF4`\n\n' \
                    'To learn more about the syntax of each command, call `' + \
                    '{0}[command] help`'

            info_option = paginator.Option(button='ℹ',
                                           content=EmbedField(name="__Command Syntax__:",
                                                              value=info.format(self.bot.command_prefix)))

            await paginator.paginate(list_help(args=sorted(help_args),
                                               high_perm=self.bot.has_high_permissions(ctx.message.author)),
                                     title='Command Help',
                                     bot=self.bot,
                                     destination=ctx.message.author,
                                     timeout=120,
                                     extra_options=[info_option],
                                     icon='https://abs.twimg.com/emoji/v2/72x72/2753.png',
                                     color=0xff0000)


def setup(bot):
    return Help(bot)