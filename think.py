from discord.ext import commands
import aiohttp
import discord
import os
import io
import cv2
from PIL import Image, ImageDraw, ImageOps
from global_util import *
from discordbot import DiscordBot
import command_util
import face


stickers = {'think_human': face.StickerProfile(name='think',
                                               data_type='human',
                                               fp='resources/think_hand.png',
                                               scale=0.6,
                                               sticker_x=lambda o, f: int(f.x_pos + (f.width / 2) - (2 * o.size[0] / 3)),
                                               sticker_y=lambda o, f: int((f.y_pos + f.height) - (o.size[1] / 2))),
            'think_anime': face.StickerProfile(name='think',
                                               data_type='anime',
                                               fp='resources/think_hand.png',
                                               scale=0.5,
                                               sticker_x=lambda o, f: int(f.x_pos + (f.width / 2) - (2 * o.size[0] / 3)),
                                               sticker_y=lambda o, f: int((f.y_pos + f.height) - (4 * o.size[1] / 5)))
            }


class Think:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def thinkpfp(ctx, user: discord.User = None):

            if not user:
                user = ctx.message.author

            with aiohttp.ClientSession() as session:
                async with session.get(user.avatar_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        im = Image.open(io.BytesIO(image_bytes))
                        bigsize = (im.size[0] * 3, im.size[1] * 3)
                        mask = Image.new('L', bigsize, 0)
                        draw = ImageDraw.Draw(mask)
                        draw.ellipse((0, 0) + bigsize, fill=255)
                        mask = mask.resize(im.size, Image.ANTIALIAS)
                        im.putalpha(mask)

                        output = ImageOps.fit(im, mask.size, centering=(0.5, 0.5))
                        output.putalpha(mask)
                        output.save('base_image.png')
                        await think.callback(ctx, local_base=True)

        @self.bot.command(pass_context=True)
        async def thinke(ctx, arg: str):

            if arg == 'help':
                await self.bot.send_message(ctx.message.author, "**Thinke help:**\n"
                                                                "`{}thinke [emote]`\n"
                                                                "Really makes you think about emotes :thinking:"
                                                                "".format(self.bot.command_prefix))
                return

            if arg[0] == '<':
                arg = arg.replace('<:', '')
                arg = arg.replace('>', '')
                emote = arg.split(':')
                ctx.message.attachments = [{'url': 'https://cdn.discordapp.com/emojis/{}.png'.format(emote[1])}]
                await think.callback(ctx, arg)
            else:
                emote_uni = hex(ord(arg[0]))[2:]
                ctx.message.attachments = [{'url': 'https://abs.twimg.com/emoji/v2/72x72/{}.png'.format(emote_uni)}]
                await think.callback(ctx, arg=arg)

        @self.bot.command(pass_context=True)
        async def think(ctx, arg: str = None, local_base=False):

            if arg == 'help':
                await self.bot.send_message(ctx.message.author, "**Think help:**\n"
                                                                "`{}think (embed image)`\n"
                                                                "Really makes you think :thinking:"
                                                                "".format(self.bot.command_prefix))
                return

            if (ctx.message.attachments or ctx.message.embeds) or (local_base is True):

                base_image = None

                if not local_base:
                    link = None
                    try:
                        link = ctx.message.attachments[0]['url']
                    except Exception:
                        try:
                            link = ctx.message.embeds[0]['url']
                        except Exception:
                            pass

                    if not link:
                        await self.bot.send_message(ctx.message.channel, 'Please embed an image.')
                        return

                    with aiohttp.ClientSession() as session:
                        async with session.get(link) as resp:
                            if resp.status == 200:
                                image_bytes = await resp.read()
                                base_image = Image.open(io.BytesIO(image_bytes))
                                base_image = base_image.convert("RGBA")
                                base_image.save('base_image.png')
                else:
                    base_image = Image.open('base_image.png')

                scale_const = 0.6  # hand-to-face ratio | 0.5362
                sc_anime = 0.5

                def find_faces():
                    faceCascade = cv2.CascadeClassifier('resources/haarcascade_frontalface_default.xml')
                    cv_image = cv2.imread('base_image.png')
                    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

                    faces = faceCascade.detectMultiScale(
                        gray,
                        scaleFactor=1.2,
                        minNeighbors=1,
                        minSize=(100, 100),
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )

                    if len(faces) > 0:
                        return faces
                    else:
                        return None

                def find_anime_faces():
                    faceCascade = cv2.CascadeClassifier('resources/lbpcascade_animeface.xml')
                    cv_image = cv2.imread('base_image.png')
                    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
                    gray = cv2.equalizeHist(gray)

                    faces = faceCascade.detectMultiScale(
                        gray,
                        scaleFactor=1.2,
                        minNeighbors=1,
                        minSize=(100, 100)
                        # flags=cv2.CASCADE_SCALE_IMAGE
                    )

                    if len(faces) > 0:
                        return faces
                    else:
                        return None

                found_human_faces = None
                found_anime_faces = None
                found_faces = None

                try:
                    found_human_faces = await self.bot.loop.run_in_executor(def_executor, find_faces)
                    found_anime_faces = await self.bot.loop.run_in_executor(def_executor, find_anime_faces)
                except Exception as e:
                    print('Face detection failed at: ' + str(e))

                if (found_human_faces is not None) and (found_anime_faces is None):
                    found_faces = found_human_faces
                elif (found_anime_faces is not None) and (found_human_faces is None):
                    found_faces = found_anime_faces
                elif (found_human_faces is not None) and (found_anime_faces is not None):
                    if len(found_human_faces) > len(found_anime_faces):
                        found_faces = found_human_faces
                    else:
                        found_faces = found_anime_faces  # assume anime because internet

                if found_faces is found_anime_faces:
                    scale_const = sc_anime

                if found_faces is not None:
                    for f in found_faces:
                        overlay_image = Image.open('resources/think_hand.png')

                        if overlay_image.size[0] > f[2]:
                            new_width = f[2]
                            new_height = new_width * (overlay_image.size[1] / overlay_image.size[0])
                            overlay_image = overlay_image.resize((int(new_width), int(new_height)),
                                                                 Image.ANTIALIAS)

                        if overlay_image.size[1] > f[3]:
                            new_height = f[3]
                            new_width = new_height * (overlay_image.size[0] / overlay_image.size[1])
                            overlay_image = overlay_image.resize((int(new_width), int(new_height)),
                                                                 Image.ANTIALIAS)

                        overlay_image = overlay_image.resize((int(overlay_image.size[0] * scale_const),
                                                              int(overlay_image.size[1] * scale_const)),
                                                             Image.ANTIALIAS)

                        newX = int(f[0] + (f[2] / 2) - (2 * overlay_image.size[0] / 3))

                        if found_faces is found_human_faces:
                            newY = int((f[1] + f[3]) - (overlay_image.size[1] / 2))
                        else:
                            newY = int((f[1] + f[3]) - (4 * overlay_image.size[1] / 5))

                        overlay_image = overlay_image.convert("RGBA")

                        base_image.paste(overlay_image, (newX, newY), overlay_image)
                else:
                    overlay_image = Image.open('resources/think_blank.png')
                    if overlay_image.size[0] > base_image.size[0]:
                        new_width = base_image.size[0]
                        new_height = new_width * (overlay_image.size[1] / overlay_image.size[0])
                        overlay_image = overlay_image.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

                    if overlay_image.size[1] > base_image.size[1]:
                        new_height = base_image.size[1]
                        new_width = new_height * (overlay_image.size[0] / overlay_image.size[1])
                        overlay_image = overlay_image.resize((int(new_width), int(new_height)), Image.ANTIALIAS)

                    base_image = base_image.convert("RGBA")
                    overlay_image = overlay_image.convert("RGBA")

                    base_image.paste(overlay_image, (0, 0), overlay_image)

                base_image.save('think.png', format='PNG')

                def llen(np_list):
                    if np_list is None:
                        return 0
                    return len(np_list)

                await self.bot.send_file(ctx.message.channel, 'think.png')
                # await self.bot.say('Found {} real faces and {} drawn faces'.format(llen(found_human_faces),
                # llen(found_anime_faces)))
                os.remove('think.png')
                os.remove('base_image.png')
            else:
                await self.bot.say('Please embed an image')

        @self.bot.command(pass_context=True)
        async def think(ctx, arg: str = None, user: discord.User = None):
            base_image = None

            if arg:
                converted_arg = command_util.find_arg(ctx, arg, ['emote'])

                if type(converted_arg) is discord.Emoji:
                    base_image = await get_image(converted_arg.url)
                elif type(converted_arg) is str:
                    if converted_arg.startswith('http'):
                        base_image = await get_image(converted_arg)
                    elif converted_arg in ['pfp', 'avatar']:
                        if user:
                            av_url = user.avatar_url
                        else:
                            av_url = ctx.message.author.avatar_url
                        base_image = await get_image(av_url)
                        base_image = style_pfp(base_image)
            else:
                if ctx.message.attachments:
                    base_image = await get_image(ctx.message.attachments[0]['url'])
                elif ctx.message.embeds:
                    base_image = await get_image(ctx.message.embeds[0]['url'])

            if not base_image:
                await self.bot.say('Error finding base image :thinking:', delete_after=5)
                return

            result_name = face.apply_sticker(base_image,
                                             human_profile=stickers['think_human'],
                                             anime_profile=stickers['think_anime'],
                                             loop=self.bot.loop,
                                             executor=def_executor)

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


def setup(bot):
    return Think(bot)