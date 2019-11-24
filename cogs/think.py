import json

import discord
from PIL import Image, ImageDraw, ImageOps
from discord.ext import commands

import face
from discordbot import DiscordBot
from util import global_util, command_util
import storage_manager_v2 as storage

stickers = {}

serialized = storage.load_stickers()
for s in serialized:
    options = {}
    for o in serialized[s]:
        if o in ['sticker_x', 'sticker_y']:
            options[o] = eval(serialized[s][o])
        else:
            options[o] = serialized[s][o]
    stickers[s] = face.StickerProfile(**options)


class Think:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def think(ctx, arg: str = None, member: str = None):

            if arg == 'help':
                await self.bot.whisper('**Think usage:**\n'
                                       '`{0}think [url]`\n'
                                       '`{0}think (embed image)`\n'
                                       '`{0}think [emoji]`\n'
                                       '`{0}think ["pfp"/"avatar"] [optional:@user]`\n'
                                       'Makes an image think.\n'
                                       'Examples:\n'
                                       '`{0}think` (with embedded image)\n'
                                       '`{0}think 🍎`\n'
                                       '`{0}think pfp`'.format(self.bot.command_prefix))
                return

            base_image = await extract_image(ctx, arg, member)

            if not base_image:
                await self.bot.say('Error finding base image :thinking:', delete_after=5)
                return

            result_name = await face.apply_sticker(base_image,
                                                   human_profile=stickers['think_human'],
                                                   anime_profile=stickers['think_anime'],
                                                   default_profile=stickers['think_default'],
                                                   loop=self.bot.loop,
                                                   executor=global_util.def_executor)


            if result_name:
                await self.bot.send_file(ctx.message.channel, result_name)
            else:
                await self.bot.send_message(ctx.message.channel, 'Error processing image :thinking:')

        @self.bot.command(pass_context=True)
        async def boop(ctx, arg: str = None, member: str = None):

            if arg == 'help':
                await self.bot.whisper('**Boop usage:**\n'
                                       '`{0}boop [url]`\n'
                                       '`{0}boop (embed image)`\n'
                                       '`{0}boop [emoji]`\n'
                                       '`{0}boop ["pfp"/"avatar"] [optional:@user]`\n'
                                       'Boops an image.\n'
                                       'Examples:\n'
                                       '`{0}boop` (with embedded image)\n'
                                       '`{0}boop 😳`\n'
                                       '`{0}boop avatar`'.format(self.bot.command_prefix))
                return

            base_image = await extract_image(ctx, arg, member)

            if not base_image:
                await self.bot.say('Error finding base image :thinking:', delete_after=5)
                return

            result_name = await face.apply_sticker(base_image,
                                                   human_profile=stickers['boop_human'],
                                                   anime_profile=stickers['boop_anime'],
                                                   default_profile=stickers['boop_default'],
                                                   loop=self.bot.loop,
                                                   executor=global_util.def_executor)

            if result_name:
                await self.bot.send_file(ctx.message.channel, result_name)
            else:
                await self.bot.send_message(ctx.message.channel, 'Error processing image :thinking:')


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
        converted_arg = command_util.find_arg(ctx, arg, ['emoji', 'member'])

        if isinstance(converted_arg, discord.Emoji):
            base_image = await global_util.get_image(converted_arg.url)
        elif isinstance(converted_arg, str):
            if converted_arg.startswith('http'):
                base_image = await global_util.get_image(converted_arg)
            elif converted_arg in ['pfp', 'avatar']:
                if member:
                    member = command_util.find_arg(ctx, member, ['member'])
                    if type(member) is not discord.Member:
                        member = await command_util.find_member(ctx, member, percent=50)

                if not member:
                    member = ctx.message.author

                base_image = await global_util.get_image(member.avatar_url)
                base_image = style_pfp(base_image)
        elif isinstance(converted_arg, discord.Member):
            base_image = await global_util.get_image(converted_arg.avatar_url)
            base_image = style_pfp(base_image)
    else:
        if ctx.message.attachments:
            base_image = await global_util.get_image(ctx.message.attachments[0]['url'])
        elif ctx.message.embeds:
            base_image = await global_util.get_image(ctx.message.embeds[0]['url'])
        else:
            base_image = await global_util.get_image(ctx.message.author.avatar_url)
            base_image = style_pfp(base_image)

    return base_image


def setup(bot):
    return Think(bot)
