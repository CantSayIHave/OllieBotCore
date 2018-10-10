import io
import json
import os

import discord
from PIL import Image

import storage_manager_v2 as storage
from discordbot import DiscordBot
from server import Server
from util import global_util, command_util


backgrounds = storage.load_backgrounds()


def write():
    storage.write_backgrounds(backgrounds)


def add_background(name, url):
    backgrounds[name] = url


def del_background(name):
    del backgrounds[name]


class PhotoShop:
    def __init__(self, bot: DiscordBot, bg):
        self.bot = bot
        self.backgrounds = bg

        @self.bot.group(aliases=['ps'])
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

        @photoshop.command(pass_context=True, aliases=['colorreplace', 'cr'])
        @self.bot.test_server
        async def replace_color(ctx, in_server: Server,
                                old: str,
                                new: str = '0xffffff',
                                image: str = None,
                                member: discord.Member = None):

            if old == 'help':
                await self.bot.whisper("**Colorreplace usage:**\n"
                                       "`{0}ps <colorreplace/cr> [old color] [new color] [image url/emoji/'capture']`\n"
                                       "`{0}ps <colorreplace/cr> [old color] [new color] <pfp> [optional:@member]`\n"
                                       "`{0}ps <colorreplace/cr> [old color] [new color] (embed image)`\n"
                                       "Replaces one color with another in selected image.\n"
                                       "*Note: transparency is ignored.*\n"
                                       "__Examples:__\n"
                                       "`{0}ps colorreplace ff0000 00ff00 ❤`\n"
                                       "`{0}ps cr #000000 #ffaa00 capture`\n"
                                       "`{0}ps cr ffffff 000000 (embed image)`"
                                       "".format(self.bot.command_prefix))
                return

            if old is None or new is None:
                await self.bot.say('Please supply an `[old]` and `[new]` color. 🖌')
                return

            old = old.replace('#', '').replace('0x', '')
            new = new.replace('#', '').replace('0x', '')

            old = self.force_alpha(old)
            new = self.force_alpha(new)

            if not global_util.is_num(old, 16) or not global_util.is_num(new, 16):
                await self.bot.say('Please supply `[old]` and `[new]` as hexadecimal color codes. #⃣')
                return

            base_image = None

            if image == 'capture':
                if not in_server.capture:
                    await self.bot.say('There is no image currently captured! Use `{0}ps capture` to capture one.'
                                       ''.format(self.bot.command_prefix))
                    return

                base_image = await global_util.get_image(in_server.capture)

            else:
                base_image = await command_util.extract_image(ctx, image, member)

            if not base_image:  # type:Image
                await self.bot.say('Please supply a base image. 📀')
                return

            m = await self.bot.say('Please enter a tolerance for color testing, as a number or percentage. '
                                   '(Default is 5)')
            reply = await self.bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)

            await self.bot.delete_message(message=m)  # erase prompt

            try:
                if '%' in reply.content:
                    tolerance = abs(int((float(reply.content.replace('%', '')) / 100) * 255))
                else:
                    tolerance = int(reply.content)
            except:
                await self.bot.say('Tolerance must be an integer or percentage! Set tolerance to 5.')
                tolerance = 5

            self.replace_color(base_image, int(old, 16), int(new, 16), tolerance)

            image_bytes = io.BytesIO()
            base_image.save(image_bytes, format='PNG')
            await self.bot.send_file(ctx.message.channel,
                                     io.BytesIO(image_bytes.getvalue()),
                                     filename='replaced.png')

        @photoshop.command(pass_context=True)
        async def capture(ctx, arg: str):
            if arg == 'help':
                await self.bot.whisper('**Capture usage:**\n'
                                       '`{0}capture [number]`\n'
                                       'Capture is a photoshop module command that '
                                       'allows the capture of an image for use in any '
                                       'photoshop command. Images able to be captured '
                                       'are any embedded, uploaded or otherwise linked '
                                       'in the last 100 messages for each channel. Once '
                                       'an image is captured, it is globally stored. You '
                                       'may use it with name `capture` in any photoshop '
                                       'command.\n\n'
                                       'The argument `number` is the image number in the '
                                       'channel, counting up from most recent.'
                                       ''.format(self.bot.command_prefix))
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if arg == 'get':
                await self.bot.say('Current capture is {}'.format(in_server.capture))
                return

            arg = global_util.is_num(arg)

            if arg is None:
                return

            if arg < 1:
                arg = 1

            captured = await command_util.find_image(self.bot, ctx.message.channel, image_num=arg)

            if captured:
                filename = global_util.extract_filename(captured)
                await self.bot.say('Captured `{}`'.format(filename))

                in_server.capture = captured
            else:
                await self.bot.say('Nothing found... 🤔')

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

        print('mid tuple is {}'.format(data[36, 36]))

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

                        # return image

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
        if tA[3] < variance:  # ignore alpha
            return False
        return abs(tA[0] - tB[0]) <= variance and \
               abs(tA[1] - tB[1]) <= variance and \
               abs(tA[2] - tB[2]) <= variance

    @staticmethod
    def alpha_compare(tA: tuple, tB: tuple, variance: int):
        return abs(tA[3] - tB[3]) <= variance

    @staticmethod
    def force_alpha(color: str):
        while len(color) < 6:
            color = '0' + color

        while len(color) < 8:
            color = 'f' + color

        return color


def setup(bot):
    return PhotoShop(bot, backgrounds)
