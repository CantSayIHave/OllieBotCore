from discord.ext import commands
import discord
from enum import Enum
import re


class ArgumentType(Enum):
    MEMBER = USER =  0
    CHANNEL =        1
    COLOUR = COLOR = 2
    ROLE =           3
    GAME =           4
    INVITE =         5
    EMOJI =          6


def get_type(arg):
    if type(arg) is int:
        try:
            return ArgumentType(arg)
        except ValueError:
            return None
    elif type(arg) is str:
        try:
            return ArgumentType[arg.upper()]
        except (ValueError, KeyError):
            return None


def get_converter(type_):
    c_type = get_type(type_)
    if not c_type:
        return None
    if c_type == ArgumentType.MEMBER or c_type == ArgumentType.USER:
        return commands.MemberConverter
    elif c_type == ArgumentType.CHANNEL:
        return commands.ChannelConverter
    elif c_type == ArgumentType.COLOUR:
        return commands.ColourConverter
    elif c_type == ArgumentType.ROLE:
        return commands.RoleConverter
    elif c_type == ArgumentType.GAME:
        return commands.GameConverter
    elif c_type == ArgumentType.INVITE:
        return commands.InviteConverter
    elif c_type == ArgumentType.EMOJI:
        return EmojiConverter


def find_arg(ctx, arg: str, types: iter):
    for t in types:
        converter = get_converter(t)
        if converter:
            try:
                found = converter(ctx, arg).convert()
                if found:
                    return found
            except commands.BadArgument:
                pass
    return arg


async def find_member(ctx, arg: str, percent):
    if percent > 1:
        percent = percent / 100

    arg = arg.lower()

    for m in ctx.message.server.members:
        if arg in m.name.lower():
            if (len(arg) / len(m.name)) >= percent:
                return m
        elif arg in m.display_name.lower():
            if (len(arg) / len(m.display_name)) >= percent:
                return m


class EmojiConverter:
    def __init__(self, ctx, arg):
        self.ctx = ctx
        self.arg = arg

    def convert(self):
        match = re.match(r'<:([a-zA-Z0-9_]+)+:([0-9]+)>$', self.arg)
        if match:
            return discord.Emoji(name=match.group(1), id=match.group(2), server='00000000', require_colons=True)
        elif not re.match(r'https?:', self.arg):
            emote_uni = hex(ord(self.arg))[2:]
            return 'https://abs.twimg.com/emoji/v2/72x72/{}.png'.format(emote_uni)
