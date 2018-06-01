import re
from enum import Enum

import discord
from PIL import Image, ImageDraw, ImageOps
from discord.ext import commands

from util import global_util


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
        # not re.match(r'https?:', self.arg)
        elif len(self.arg) == 1:
            emote_uni = hex(ord(self.arg))[2:]
            return 'https://abs.twimg.com/emoji/v2/72x72/{}.png'.format(emote_uni)


async def find_message(bot, channel, message_num: int):
    m_on = 0
    async for m in bot.logs_from(channel, limit=int(message_num + 1)):
        if m_on == message_num:
            return m
        m_on += 1


async def find_image(bot, channel, image_num: int):
    im_on = 1
    async for m in bot.logs_from(channel, limit=100):  # type: discord.Message
        if m.embeds:
            if im_on == image_num:
                return m.embeds[0]['url']
            im_on += 1
        if m.attachments:
            if im_on == image_num:
                return m.attachments[0]['url']
            im_on += 1


def style_pfp(im: Image):
    bigsize = (im.size[0] * 3, im.size[1] * 3)
    mask = Image.new('L', bigsize, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + bigsize, fill=255)
    mask = mask.resize(im.size, Image.ANTIALIAS)
    im.putalpha(mask)

    output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)

    return output


async def extract_image(ctx: commands.Context, arg: str = None, member: str = None):
    base_image = None

    if arg:
        converted_arg = find_arg(ctx, arg, ['emoji'])

        if type(converted_arg) is discord.Emoji:
            base_image = await global_util.get_image(converted_arg.url)
        elif type(converted_arg) is str:
            if converted_arg.startswith('http'):
                base_image = await global_util.get_image(converted_arg)
            elif converted_arg in ['pfp', 'avatar']:
                if member:
                    member = find_arg(ctx, member, ['member'])
                    if type(member) is not discord.Member:
                        member = await find_member(ctx, member, percent=50)

                if not member:
                    member = ctx.message.author

                base_image = await global_util.get_image(member.avatar_url)
                base_image = style_pfp(base_image)
    else:
        if ctx.message.attachments:
            base_image = await global_util.get_image(ctx.message.attachments[0]['url'])
        elif ctx.message.embeds:
            base_image = await global_util.get_image(ctx.message.embeds[0]['url'])

    return base_image