import os
import json

import discord
from discord.ext import commands

import command_util
import global_util
from discordbot import DiscordBot
import storage_manager as storage

from PIL import Image, ImageDraw, ImageOps


storage.mkdir_safe('photoshop')
storage.mkfile_safe('./photoshop/backgrounds.json', '{}')
with open('./photoshop/backgrounds.json', 'r') as b:
    backgrounds = json.load(b)


def write():
    with open('./photoshop/backgrounds.json', 'w') as b:
        json.dump(backgrounds, b)


def add_background(name, url):
    backgrounds[name] = url


def del_background(name):
    del backgrounds[name]


class PhotoShop:
    def __init__(self, bot: DiscordBot, bg):
        self.bot = bot
        self.backgrounds = bg

        @self.bot.group(name='ps')
        async def photoshop():
            pass

        @photoshop.command(pass_context=True)
        async def mask(ctx, arg: str, url: str = None):
            if arg == 'listall':
                out = "**Available Mask Backgrounds:** "
                for m in self.backgrounds:
                    out += '`{}`, '.format(m)
                await self.bot.say(out[:-2])
                return

            elif arg in self.backgrounds:
                object_arg = None
                if url:
                    object_arg = command_util.find_arg(ctx, url, ['emoji'])
                elif ctx.message.attachments or ctx.message.embeds:
                    try:
                        object_arg = ctx.message.attachments[0]['url']
                    except Exception:
                        try:
                            object_arg = ctx.message.embeds[0]['url']
                        except Exception:
                            pass

                if not object_arg:
                    await self.bot.say('Please pass or embed an image.')
                    return

                if type(object_arg) is discord.Emoji:
                    download_url = object_arg.url
                else:
                    download_url = object_arg

                mask_background = await global_util.get_image(self.backgrounds[arg])

                mask_foreground = await global_util.get_image(download_url)

                if mask_background and mask_foreground:
                    # scale background height to foreground height
                    new_height = mask_foreground.size[1]
                    new_width = new_height * (mask_background.size[0] / mask_background.size[1])
                    mask_background = mask_background.resize((int(new_width), int(new_height)),
                                                             Image.ANTIALIAS)

                    # crop background to foreground
                    if mask_background.size[0] > mask_foreground.size[0]:
                        mask_background = mask_background.crop((0, 0) + mask_foreground.size)
                    else:
                        mask_foreground = mask_foreground.crop((0, 0) + mask_background.size)
                    # await self.bot.send_message(ctx.message.channel, 'about to convert')
                    # convert foreground into a mask
                    self.replace_color(mask_foreground, (255, 255, 255, 0), 0xffffffff, 5, spare=True, alpha=True)
                    self.replace_color(mask_foreground, (0, 0, 0, 0), 0, 5, alpha=True)
                    # await self.bot.send_message(ctx.message.channel, 'converted')

                    mask_foreground = mask_foreground.convert('L')
                    mask_background.putalpha(mask_foreground)
                    mask_background.save('masked.png')

                    await self.bot.send_file(ctx.message.channel, 'masked.png')

                    try:
                        os.remove('masked.png')
                    except Exception as e:
                        print('Photoshop error: {}'.format(e))
                else:
                    await self.bot.say('Mask error. Fore: {}, Back: {}\n'
                                       'Download url: {}'.format(mask_foreground, mask_background, download_url))

        @photoshop.command(pass_context=True)
        async def backgrounds(ctx, arg: str, name: str = None, url: str = None):

            if not ctx.message.server:
                return

            in_server = self.bot.get_server(ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'listall':
                out = "**Backgrounds:** "
                for b in self.backgrounds:
                    out += '`{}`, '.format(b)
                await self.bot.say(out[:-2])
                return

            elif arg == 'add' and name:
                add_url = global_util.extract_image_url(url, ctx.message)
                if add_url:
                    add_background(name, add_url)
                write()
                await self.bot.say('Added background `{}`!'.format(name))

            elif arg == 'remove' and name:
                del_background(name)
                write()
                await self.bot.say('Removed background `{}`!'.format(name))

        @photoshop.command(pass_context=True, name='replace')
        @self.bot.test_high_perm
        async def replace_color(ctx, in_server, old: str, new: str = '0xffffff', image: str = None):
            await self.bot.say("Replace it yourself :P\nServer = {}".format(in_server.name))

    def replace_color(self, image: Image, base_hex, replace_hex, variance: int, spare=False, alpha=False):
        if type(base_hex) is int:
            b_tuple = self.color_tuple(base_hex)
        else:
            b_tuple = base_hex
        if type(replace_hex) is int:
            r_tuple = self.color_tuple(replace_hex)
        else:
            r_tuple = replace_hex

        data = image.load()

        if alpha:
            compare = self.alpha_compare
        else:
            compare = self.color_compare

        if spare:
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    if not compare(data[x, y], b_tuple, variance):
                        data[x, y] = r_tuple
        else:
            for y in range(image.size[1]):
                for x in range(image.size[0]):
                    if compare(data[x, y], b_tuple, variance):
                        data[x, y] = r_tuple

    @staticmethod
    def color_tuple(c_hex: int):
        alpha = (c_hex & 0xff000000) >> 24
        red = (c_hex & 0xff0000) >> 16
        green = (c_hex & 0xff00) >> 8
        blue = c_hex & 0xff
        return red, green, blue, alpha

    # compare colors
    # only checks r, g, b
    @staticmethod
    def color_compare(tA, tB, variance: int):
        return abs(tA[0] - tB[0]) <= variance and \
               abs(tA[1] - tB[1]) <= variance and \
               abs(tA[2] - tB[2]) <= variance

    @staticmethod
    def alpha_compare(tA: tuple, tB: tuple, variance: int):
        return abs(tA[3] - tB[3]) <= variance


def setup(bot):
    return PhotoShop(bot, backgrounds)

