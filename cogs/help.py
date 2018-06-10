import discord
from discord.ext import commands

from util.containers import *
from util import paginator
from util import global_util
from discordbot import DiscordBot
import help_args


help_icon = 'https://abs.twimg.com/emoji/v2/72x72/2753.png'

all_profile = {'mod': False,
               'pages': (('fun', 'images'),
                         ('fun', 'text'),
                         ('fun', 'util'),
                         ('fun', 'info'),
                         ('utilities', 'tools'),
                         ('music', None)),
               'icon': help_icon,
               'color': 0xff0000}

mod_profile = {'mod': True,
               'pages': (('fun', 'images'),
                         ('fun', 'text'),
                         ('fun', 'util'),
                         ('fun', 'info'),
                         ('utilities', 'bot'),
                         ('utilities', 'server'),
                         ('utilities', 'tools'),
                         ('music', None)),
               'icon': help_icon,
               'color': 0xff0000}


def build_page(bot: DiscordBot, section: str, subsec: str = None, mod=True, page_on=1, page_total=1):
    em = discord.Embed(title=global_util.TITLE_BAR, color=0xff0000)
    if subsec:
        em.set_author(name='Command Help (Page {}/{}): {} - {}'.format(page_on,
                                                                       page_total,
                                                                       section.capitalize(),
                                                                       subsec.capitalize()),
                      icon_url=help_icon)
    else:
        em.set_author(name='Command Help (Page {}/{}): {}'.format(page_on,
                                                                  page_total,
                                                                  section.capitalize()),
                      icon_url=help_icon)

    if subsec:
        parent_mod = getattr(help_args, section)
        mod = getattr(parent_mod, subsec)
    else:
        mod = getattr(help_args, section)

    for command in global_util.get_new_attr(mod, check=lambda x: type(x) is HelpForm):
        form = getattr(mod, command)  # type:HelpForm
        if form.high_perm:
            if mod:
                em.add_field(name='{}{}'.format(bot.command_prefix, command),
                             value=form.tagline,
                             inline=False)
        else:
            em.add_field(name='{}{}'.format(bot.command_prefix, command),
                         value=form.tagline,
                         inline=False)

    return em


def build_menu(bot: DiscordBot, profile: dict):
    mod = profile['mod']
    pages = profile['pages']
    total = len(pages)
    menu = paginator.Pages([], profile['icon'], profile['color'])

    for i, p in enumerate(pages):
        menu += build_page(bot, p[0], p[1], mod, i+1, total)

    return menu


def build_menus(bot: DiscordBot):
    all_help = build_menu(bot, all_profile)
    mod_help = build_menu(bot, mod_profile)

    return all_help, mod_help


class Help:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def help(ctx, command: str = None, detail: str = None):
            if command:
                await send_help(self.bot, ctx.message.author, command, detail)
                return

            def list_help(args, high_perm):
                for arg in args:  # type: str
                    if help_args.help_taglines[arg]['m'] and high_perm:
                        yield EmbedField(name=arg,
                                         value=help_args.help_taglines[arg]['d'].capitalize(),
                                         inline=False)
                    elif not help_args.help_taglines[arg]['m']:
                        yield EmbedField(name=arg,
                                         value=help_args.help_taglines[arg]['d'].capitalize(),
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

            await paginator.paginate(items=list_help(args=sorted(help_args),
                                               high_perm=self.bot.has_high_permissions(ctx.message.author)),
                                     title='Command Help',
                                     bot=self.bot,
                                     destination=ctx.message.author,
                                     author=ctx.message.author,
                                     timeout=120,
                                     extra_options=[info_option],
                                     icon='https://abs.twimg.com/emoji/v2/72x72/2753.png',
                                     color=0xff0000)

async def intercept_help(message: discord.Message, bot):
    if not message.content:
        return False

    if message.content.find(bot.command_prefix) != 0:
        return False

    pieces = message.content.split(' ')

    if len(pieces) >= 2:
        if pieces[1] == 'help':
            query = pieces[0].replace(bot.command_prefix, '')

            detail = None
            if len(pieces) >= 3:
                detail = pieces[2]

            await send_help(bot, message.author, query, detail)
            return True

    return False


async def send_help(bot: DiscordBot, author: discord.User, command: str, detail=None):
    form = getattr(help_args, command, default=None)  # type:HelpForm

    if form:
        if detail:
            if form.detail(detail):
                help_message = form.detail(detail).format(bot.command_prefix, bot.user.mention)
            else:
                help_message = 'Command `{}` doesn\'t have a detail named `{}`'.format(command, detail)
        else:
            help_message = form.format(bot.command_prefix, bot.user.mention)
    else:
        help_message = 'Command `{}` has no help documentation or does not exist.'.format(command)

    await bot.send_message(author, help_message)


def setup(bot):
    return Help(bot)