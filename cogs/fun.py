import copy
import functools
import os

import wikipedia
import youtube_dl
from PIL import ImageDraw, ImageFont
from pydub import AudioSegment
from wikipedia import DisambiguationError
from wikipedia import PageError
import pyfiglet
import timestring
import insultgen
from googletrans import Translator

import storage_manager_v2 as storage
from apis.strawpoll import *
from discordbot import DiscordBot
from util import global_util, command_util
from util.global_util import *

num2regional = {0: '0⃣',
                1: '1⃣',
                2: '2⃣',
                3: '3⃣',
                4: '4⃣',
                5: '5⃣',
                6: '6⃣',
                7: '7⃣',
                8: '8⃣',
                9: '9⃣',}

regional2num = {v: k for k, v in num2regional.items()}

fig_fonts = pyfiglet.FigletFont.getFonts()
translator = Translator()


class Fun:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def reee(server, ctx, arg: str = None, *, msg: str = None):

            if arg is None:
                await self.bot.say('reee response is set to **{}**'.format(bool(server.reee_message)))
                return

            if arg.lower() == 'true':
                server.reee_message = True
                await self.bot.say('reee response set to true')
                return
            elif arg.lower() == 'false':
                server.reee_message = False
                await self.bot.say('reee response set to false')
                return

            if arg == 'message' and msg is None:
                await self.bot.say('reee message is set to `{0}`'.format(server.reee_message))
                return

            if arg == 'message' and msg is not None:
                server.reee_message = msg
                storage.write_server_data(server)
                await self.bot.say('reee message now set to `{0}`'.format(server.reee_message))

        @self.bot.command(pass_context=True)
        async def good(ctx, noun: str = None):
            if noun == 'bot':
                await self.bot.say('good human')
            elif noun == 'human':
                await self.bot.say('GOOD FELLOW HUMAN')
            elif noun == 'help':
                await self.bot.say('I try 😊')
            else:
                await self.bot.say('good what?')

        @self.bot.command(pass_context=True)
        async def bad(ctx, arg: str = None):

            if ctx.message.author.id == '238038532369678336':
                await self.bot.say(random.choice(['good cake', 'great cake', 'i love cake']))
                return

            if arg is None:
                await self.bot.say('no u')
            elif arg == 'bot':
                await self.bot.say('{0} bad human'.format(ctx.message.author.mention))
            elif arg == 'human':
                await self.bot.say('{0} BAD FELLOW HUMAN AS WELL'.format(ctx.message.author.mention))
            elif arg == 'help':
                await self.bot.say("Well I'm more help than you 😤")
            else:
                insult = insultgen.generate()
                if random.choice((True, False)):
                    insult = insult.upper()
                await self.bot.say(insult)

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def playing(server, ctx, *, message: str):
            self.bot.playing_message = message
            storage.write_bot_data(self.bot)

            await self.bot.change_presence(game=discord.Game(name=message, type=0))
            await self.bot.say('Changed `playing` status to `{0}`'.format(message))

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def presence(server, ctx, type: str, *, message: str):
            if not self.bot.has_high_permissions(ctx.message.author):
                return

            presence_types = {'playing': 0, 'game': 0, 'streaming': 1, 'listening': 2}
            type = type.lower()

            url = None

            if 'url=' in message:
                pieces = message.split(' ')
                if 'url=' in pieces[-1]:
                    url = pieces[-1].replace('url=','')
                    message = ' '.join(pieces[:-1])

            if type in presence_types:
                await self.bot.change_presence(game=discord.Game(name=message, type=presence_types[type], url=url))
                await self.bot.say('Changed `{}` presence to `{}`'.format(type, message))
            else:
                await self.bot.say('`{}` is not a valid presence type'.format(type))

        @self.bot.command(pass_context=True, aliases=['b-ify', 'bify'])
        async def b_ify(ctx, *, arg: str):

            if arg == 'help':
                await self.bot.send_message(ctx.message.author,
                                            '**B-ify help:**\n'
                                            '`{0}b-ify [text]`\n'
                                            'Adds some 🅱 to text.'
                                            ''.format(self.bot.command_prefix))
                return

            keys = arg.split(' ')
            out_str = ''
            for key in keys:
                start = copy.copy(key)
                key = key.replace('b', '🅱')
                if key != start:
                    out_str += key + ' '
                    continue
                key = key.replace('gg', '🅱🅱')
                if key != start:
                    out_str += key + ' '
                    continue
                key = key.replace(random.choice(key), '🅱')
                out_str += key + ' '
            await self.bot.say(out_str)

        @self.bot.command(pass_context=True)
        async def bigtext(ctx, *, arg: str):

            if arg == 'help':
                await self.bot.send_message(ctx.message.author,
                                            "**Bigtext help:**\n"
                                            "`{0}bigtext ['-r'] [text]`\n"
                                            "Converts `text` into regional indicators.\n"
                                            "If optional `-r` is passed before `text`, the *raw* form of the \n"
                                            "output will be returned so that you may copy and paste it yourself.\n"
                                            "__Examples:__\n"
                                            "`{0}bigtext i am not a bot`\n"
                                            "`{0}bigtext -r i am totally human`"
                                            "".format(self.bot.command_prefix))
                return

            is_raw = False
            if arg[:2] == '-r':
                is_raw = True
                arg = arg[2:]
            arg = arg.lower()
            out_str = ''
            for c in arg:
                if c == 'b':
                    out_str += '🅱'
                elif c.isalpha():
                    out_str += ':regional_indicator_{}:'.format(c)
                elif c.isnumeric():
                    out_str += ':{}:'.format(global_util.num2word[c])
                elif c == '\n':
                    out_str += '\n'
                elif c.isspace():
                    out_str += '  '
                else:
                    out_str += c
                if is_raw:
                    out_str += ' '
            if is_raw:
                await self.bot.say('```\n{}\n```'.format(out_str))
            else:
                await self.bot.say(out_str)

        @self.bot.command(pass_context=True)
        async def imageconvert(ctx, new_format: str, dummy_link: str = None):

            if new_format == 'help':
                await self.bot.send_message(ctx.message.author, '**Image Convert help:**\n'
                                                                '`{}imgconvert [new filetype] (embed image)`\n'
                                                                'Converts an image to requested filetype.'
                                                                ''.format(self.bot.command_prefix))
                return

            if ctx.message.attachments or ctx.message.embeds:
                link = None
                try:
                    link = ctx.message.attachments[0]['url']
                except Exception:
                    try:
                        link = ctx.message.embeds[0]['url']
                    except Exception:
                        pass

                if not link:
                    await self.bot.say('Please embed an image.')
                    return

                path = 'converted.{}'.format(new_format)

                try:
                    with aiohttp.ClientSession() as session:
                        async with session.get(link) as resp:
                            if resp.status == 200:
                                image_bytes = await resp.read()
                                base_image = Image.open(io.BytesIO(image_bytes))
                                base_image = base_image.convert("RGBA")

                                base_image.save(path)

                                await self.bot.send_file(ctx.message.channel, path)
                                os.remove(path)
                except Exception as e:
                    print('Image conversion failed at: ' + str(e))
                    await self.bot.say('Error in conversion.')
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            else:
                await self.bot.say('Please embed an image')

        @self.bot.command(pass_context=True)
        async def audioconvert(ctx, new_format: str, link: str = None):

            if new_format == 'help':
                await self.bot.send_message(ctx.message.author, '**Audio Convert help:**\n'
                                                                '`{}audioconvert [new filetype] [link]`\n'
                                                                'Converts an audio file to requested filetype.'
                                                                ''.format(self.bot.command_prefix))
                return

            if ctx.message.attachments or link:
                download_link = None
                if link and link.find('http') == 0:
                    download_link = link
                else:
                    try:
                        download_link = ctx.message.attachments[0]
                    except Exception:
                        pass

                if not download_link:
                    await self.bot.say('Please attach an audio file.')
                    return

                save_path = None

                try:
                    with aiohttp.ClientSession() as session:
                        async with session.get(link) as resp:
                            if resp.status == 200:
                                file_bytes = await resp.read()
                                old_ext = '.mp3'
                                try:
                                    file_name = resp.headers['Content-Disposition'].split('filename=')[1]
                                    file_pieces = file_name.rsplit('.', 1)
                                    file_name = file_pieces[0]
                                    old_ext = file_pieces[1]
                                except Exception:
                                    file_name = 'converted'

                                save_path = '{}.{}'.format(file_name, old_ext)

                                with open(save_path, 'wb') as audio:
                                    audio.write(file_bytes)
                                    audio.close()

                                try:
                                    song = AudioSegment.from_file(save_path, old_ext)
                                except Exception:
                                    await self.bot.say('Invalid file type.')
                                    raise

                                save_path = '{}.{}'.format(file_name, new_format)

                                song.export(save_path, format=new_format)

                                await self.bot.send_file(ctx.message.channel, save_path)
                                os.remove(save_path)
                except Exception as e:
                    print('Image conversion failed at: ' + str(e))
                    await self.bot.say('Error in conversion.')
                    try:
                        os.remove(save_path)
                    except Exception:
                        pass

        @self.bot.command(pass_context=True)
        async def wiki(ctx, *, title: str):
            sent = await self.bot.say(':mag_right: :regional_indicator_w: Searching Wikipedia for `{0}`'.format(title))
            thing = functools.partial(self.get_wiki_page, title)
            wiki_page = await self.bot.loop.run_in_executor(def_executor, thing)

            if wiki_page is None:
                await self.bot.say('No pages exist for `{0}`!'.format(title))
                return

            if wiki_page is False:
                await self.bot.say('Please be more specific :thinking:')
                return

            await self.bot.delete_message(sent)

            marked_title = wiki_page['title']
            embed = discord.Embed(title=marked_title,
                                  url=wiki_page['url'],
                                  description=wiki_page['summary'],
                                  color=0xffffff)
            if wiki_page['image'] is not None:
                img_url = wiki_page['image']
                embed.set_image(url=img_url)
            embed.set_author(name='Wikipedia',
                             url='https://www.wikipedia.org/',
                             icon_url='https://upload.wikimedia.org/wikipedia/en/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png')
            await self.bot.send_message(ctx.message.channel, embed=embed)

        @self.bot.command(pass_context=True)
        async def joined(ctx, *, member: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            if member:
                if len(member) > 1:
                    if member[0] == '"':
                        member = member[1:]
                    if member[-1] == '"':
                        member = member[:-1]  # remove attempted quotes from around arg

                member = command_util.find_arg(ctx, member, ['member'])
                if type(member) is not discord.Member:
                    member = await command_util.find_member(ctx, member, percent=50, return_name=False)

            if not member:
                member = ctx.message.author

            e = discord.Embed(description="{0} joined {1} on {2}".format(member.display_name,
                                                                         ctx.message.server.name,
                                                                         member.joined_at.strftime("%B %-d, %Y at "
                                                                                                   "%H:%M:%S UTC")),
                              color=0x00d114)
            e.set_author(name=member.name, icon_url=member.avatar_url)

            await self.bot.say(embed=e)

        @self.bot.command(pass_context=True, aliases=['usrinfo'])
        async def userinfo(ctx, member: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            if member:
                member = command_util.find_arg(ctx, member, ['member'])
                if type(member) is not discord.Member:
                    member = await command_util.find_member(ctx, member, percent=50, return_name=False)

            if not member:
                member = ctx.message.author

            e = discord.Embed(title='════╣User Info╠════\n{}'.format(CHAR_ZWS), color=member.colour)
            e.set_author(name=member.name, icon_url=member.avatar_url)
            e.set_thumbnail(url=member.avatar_url)

            if member == ctx.message.server.owner:
                e.add_field(name='Owns this server.', value=CHAR_ZWS, inline=False)

            if member.bot:
                e.add_field(name='This user is a bot. (unlike me)', value=CHAR_ZWS, inline=False)

            e.add_field(name='Joined __{}__'.format(ctx.message.server.name),
                        value=member.joined_at.strftime('%B %-d, %Y at %H:%M:%S UTC'),
                        inline=False)

            e.add_field(name='ID', value=member.id, inline=False)

            if member.roles:
                sorted_roles = [r.name for r in sorted(member.roles, reverse=True)]
                role_list = ', '.join(sorted_roles)
                e.add_field(name='Roles', value=role_list.replace('@', ''), inline=False)
            else:
                e.add_field(name='Roles', value='everyone', inline=False)

            e.add_field(name='Status', value=str(member.status).replace('dnd', 'do not disturb'), inline=False)

            if member.game:
                e.add_field(name='Playing', value=member.game.name, inline=False)
            else:
                e.add_field(name='Playing', value='N/A', inline=False)

            if member.nick:
                e.add_field(name='Nickname', value=member.nick, inline=False)
            else:
                e.add_field(name='Nickname', value='N/A', inline=False)

            e.add_field(name='Created', value=member.created_at.strftime('%B %-d, %Y at %H:%M:%S UTC'), inline=False)

            await self.bot.say(embed=e)

        @self.bot.command(pass_context=True)
        async def ytdl(ctx, link: str):
            if not self.bot.has_high_permissions(ctx.message.author):
                return

            if link == 'help':
                await self.bot.send_message(ctx.message.author, '**Ytdl help:**\n'
                                                                '`{}ytdl [link]`\n'
                                                                'Youtube-to-MP3 function. Give it a link '
                                                                'and receive the file.\n'
                                                                '*Note: If the final file is over 10MB, the file '
                                                                'will not be returned*'
                                                                ''.format(self.bot.command_prefix))
                return

            def dl_proc():
                try:
                    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(link)
                        return ydl.prepare_filename(info)

                except Exception as e:
                    print('it failed.' + str(e))

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]}

            await self.bot.say('Starting download... :arrow_down:')

            try:
                file_name = await self.bot.loop.run_in_executor(def_executor, dl_proc)
                await self.bot.say('Conversion finished! :white_check_mark:\n'
                                   'Downloaded `{}`'.format(file_name.replace('.webm', '')))
                try:
                    await self.bot.send_file(ctx.message.channel, file_name.replace('.webm', '.mp3'))
                except Exception:
                    await self.bot.say('File could not be uploaded. Too large!')
                os.remove(file_name.replace('.webm', '.mp3'))
            except Exception as e:
                print('YTDL failed at: ' + str(e))
                self.bot.say('Download failed. ¯\_(ツ)_/¯ Try a different link?')

        @self.bot.command(pass_context=True)
        async def roll(ctx, *, roll_in: str):
            if roll_in == 'help':
                await self.bot.send_message(ctx.message.author, '**Roll help:**\n'
                                                                '`{0}roll <[N]dN> [+/- N] [adv/dis]`\n'
                                                                'Examples:\n'
                                                                '`{0}roll d6`\n'
                                                                '`{0}roll 10d10 +5`\n'
                                                                '`{0}roll d20 -3 dis`'
                                                                ''.format(self.bot.command_prefix))
                return

            roll_in = roll_in.replace(' ','')
            token_d = roll_in.find('d')
            token_mods = -1
            mods = None
            roll_out = []
            if token_d != -1:
                print('d token found at {}'.format(token_d))
                for n, c in enumerate(roll_in[token_d+1:]):
                    if c == '+' or c == '-' or c == 'a' or c == 'd':
                        token_mods = n + token_d + 1
                        mods = roll_in[token_mods:]
                        print('mods token found at {}'.format(token_mods))
                        break
                if token_mods == -1:
                    token_mods = len(roll_in)
                    print('mods token not found')
                print('mods token is {}'.format(mods))

                favor = None
                extra = None
                if mods:
                    if 'adv' in mods and 'dis' not in mods:
                        favor = 'adv'
                        mods = mods.replace('adv','')
                    elif 'dis' in mods:
                        favor = 'dis'
                        mods = mods.replace('dis','')
                    mods = mods.replace('adv', '')

                    if '+' in mods:
                        extra = mods[mods.find('+'):]
                    elif '-' in mods:
                        extra = mods[mods.find('-'):]

                dice = roll_in[0:token_mods].split('d')
                iterations = self.is_num(dice[0])
                sides = self.is_num(dice[1])

                if not iterations or type(iterations) is not int:
                    iterations = 1

                if iterations < 1:
                    iterations = 1

                if favor:
                    iterations = 2

                if not sides or type(sides) is not int:
                    sides = 1

                if sides < 1:
                    sides = 1

                if sides > 0xffffffff:
                    sides = 0xffffffff

                if ((len(str(sides)) + 3) * iterations) > 1024:
                    iterations = int(1024 / (len(str(sides)) + 3)) - 2

                for i in range(0, iterations):
                    roll_out.append(random.randint(1,sides))

                em = discord.Embed(title='───────────────────────────', color=0xcb42f4)
                em.set_author(name='Roll', icon_url='http://moziru.com/images/dungeons-dragons-clipart-d20-12.jpg')

                result = 1

                if favor:
                    first = None
                    if favor == 'adv':
                        first = False
                        result = roll_out[1]
                        if roll_out[0] >= roll_out[1]:
                            first = True
                            result = roll_out[0]

                    elif favor == 'dis':
                        first = False
                        result = roll_out[1]
                        if roll_out[0] <= roll_out[1]:
                            first = True
                            result = roll_out[0]

                    if first:
                        value_out = '**{}** | {}'.format(roll_out[0], roll_out[1])
                    else:
                        value_out = '{} | **{}**'.format(roll_out[0], roll_out[1])

                    if favor == 'adv':
                        em.add_field(name='__d{} with Advantage__'.format(sides), value=value_out, inline=False)
                    elif favor == 'dis':
                        em.add_field(name='__d{} with Disadvantage__'.format(sides), value=value_out, inline=False)

                else:
                    value_out = str(roll_out[0])
                    for r in roll_out[1:]:
                        value_out += ' + {}'.format(r)

                    result = sum(roll_out)

                    if len(roll_out) == 1:
                        value_out = '**{}**'.format(roll_out[0])
                    else:
                        value_out += ' = **{}**'.format(result)
                    em.add_field(name='__{}d{}__'.format(iterations, sides), value=value_out, inline=False)

                if extra:
                    extra_n = self.is_num(extra[1:])
                    if not extra_n:
                        extra_n = 1

                    em.add_field(name='__Modifier__', value=extra[0] + str(extra_n), inline=False)

                    if extra[0] == '+':
                        result += extra_n
                    elif extra[0] == '-':
                        result -= extra_n

                if result < 1:
                    result = 1

                em.add_field(name='__Result__', value=str(result), inline=False)

                await self.bot.say(embed=em)

        @self.bot.command(pass_context=True)
        async def bun(ctx, num: int = None):
            async def get_page() -> str:
                with aiohttp.ClientSession() as session:
                    async with session.get('http://www.rabbit.org/fun/net-bunnies.html') as resp:
                        if resp.status == 200:
                            p = await resp.text()
                            return p

            if not num:
                num = 1

            if num < 1:
                num = 1

            if num > 5:
                num = 5

            if num < 2:
                page = await get_page()

                if not page:
                    page = await get_page()

                if not page:
                    await self.bot.say('Could not connect to server :(')
                    return

                first_key = page.find('Show me another photo')

                if first_key == -1:
                    page = await get_page()
                    first_key = page.find('Show me another photo')

                image_src_s = page.find('http', first_key)

                image_src = extract_url(page, image_src_s)

                em = discord.Embed(title='Bun', color=0x4542f4)  # blue

                em.set_image(url=image_src)

                await self.bot.say(embed=em)
            else:
                for b in range(0, num):
                    page = await get_page()

                    first_key = page.find('Show me another photo')

                    image_src_s = page.find('http', first_key)

                    image_src = extract_url(page, image_src_s)

                    em = discord.Embed(title='Bun ' + str(b + 1), color=0x4542f4)  # blue

                    em.set_image(url=image_src)

                    await self.bot.say(embed=em)

        @self.bot.command(pass_context=True)
        async def cat(ctx, num: int = None):
            async def get_page() -> dict:
                with aiohttp.ClientSession() as session:
                    async with session.get('http://aws.random.cat/meow') as resp:
                        if resp.status == 200:
                            d = await resp.json()
                            return d

            if not num:
                num = 1

            if num < 1:
                num = 1

            if num > 5:
                num = 5

            if num < 2:
                cat_img = await get_page()

                if not cat_img:
                    cat_img = await get_page()

                if not cat_img:
                    await self.bot.say('Cannot connect to server :(')
                    return

                em = discord.Embed(title='Cat', color=0x03d600)  # green

                em.set_image(url=cat_img['file'])

                await self.bot.say(embed=em)
            else:
                for c in range(1, num + 1):
                    cat_img = await get_page()

                    em = discord.Embed(title='Cat ' + str(c), color=0x03d600)

                    em.set_image(url=cat_img['file'])

                    await self.bot.say(embed=em)

        @self.bot.command(pass_context=True)
        async def woof(ctx, num: str = None):
            async def get_page() -> dict:
                with aiohttp.ClientSession() as session:
                    async with session.get('https://random.dog/woof.json') as resp:
                        if resp.status == 200:
                            d = await resp.json()
                            return d

            if not num:
                num = 1
            elif self.is_num(num):
                num = int(num)
                if num > 1000:
                    await self.bot.say('https://corgiorgy.com/')
                    return
            elif num == '∞':
                await self.bot.say('https://corgiorgy.com/')
                return

            if num < 1:
                num = 1

            if num > 5:
                num = 5

            if num < 2:
                dog_img = await get_page()

                if not dog_img:
                    dog_img = await get_page()

                if not dog_img:
                    await self.bot.say('Cannot connect to server :(')
                    return

                while dog_img['url'][-4:] == '.mp4':
                    dog_img = await get_page()

                em = discord.Embed(title='Woof', color=0xff4242)  # green

                em.set_image(url=dog_img['url'])

                await self.bot.say(embed=em)
            else:
                for d in range(1, num + 1):
                    dog_img = await get_page()

                    while dog_img['url'][-4:] == '.mp4':
                        dog_img = await get_page()

                    em = discord.Embed(title='Woof ' + str(d), color=0xff4242)

                    em.set_image(url=dog_img['url'])

                    await self.bot.say(embed=em)

        @self.bot.command(pass_context=True)
        async def dropbear(ctx):
            async def get_koala() -> str:
                with aiohttp.ClientSession() as session:
                    async with session.get('https://www.gettyimages.com/photos/koala?mediatype=photography&'
                                           'phrase=koala&sort=mostpopular') as resp:
                        if resp.status == 200:
                            t = await resp.text()
                            return t

            def get_link(text: str, start: int):
                out_link = ''
                for c in text[start:start+300]:
                    if c == '"':
                        break
                    out_link += c
                return out_link

            koala_resp = await get_koala()

            if not koala_resp:
                koala_resp = await get_koala()

            if not koala_resp:
                await self.bot.say('Cannot connect to server :(')
                return

            iters = random.randint(1,55)
            asset_start = 0
            for i in range(0, iters):
                asset_start = koala_resp.find('class="srp-asset-image', asset_start + 1)

            koala_start = koala_resp.find('https://media.gettyimages.com/photos', asset_start)
            koala = get_link(koala_resp, koala_start)
            koala = koala.replace('&amp;', '&')

            em = discord.Embed(title='Drop Bear', color=0x00ffff)  # cyan
            em.set_image(url=koala)

            await self.bot.say(embed=em)

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def late(server, ctx, arg: str = None, to_set: int = None):

            if server.name != 'Shoe0nHead':
                return

            is_admin = self.bot.check_admin(ctx.message.author)

            if not arg:
                if not server.late:
                    choice = random.randint(0, 4)
                    if choice == 0:
                        minutes = random.randint(0, 10)
                    elif choice == 1:
                        minutes = random.randint(0, 1000)
                    elif choice == 2:
                        minutes = random.randint(0, 100000)
                    else:
                        minutes = random.randint(0, 1000000)
                    if minutes == 0:
                        await self.bot.say('Shoe is on time (for once)')
                    else:
                        await self.bot.say('Shoe is now {} minutes late'.format(minutes))
                else:
                    minutes = int((time.time() - server.late) / 60)
                    await self.bot.say('Shoe is now {} minutes late'.format(minutes))
            elif arg == 'start' and is_admin:
                server.late = time.time()
                await self.bot.say('Late timer started.')
            elif arg == 'stop' and is_admin:
                server.late = None
                await self.bot.say('Late timer stopped.')
            elif arg == 'set' and to_set and is_admin:
                server.late = time.time() - (to_set * 60)
                await self.bot.say('Late timer set to {}.'.format(to_set))

        @self.bot.command(pass_context=True)
        async def react(ctx, type: str, arg1: str = '', arg2: str = '', *, text: str = ''):
            if type == 'help':
                await self.bot.send_message(ctx.message.author, '**React help:**\n'
                                                                '`{0}react <id> [message ID] [text]`\n'
                                                                '`{0}react <user> [@mention] [message #] [text]`\n'
                                                                '`{0}react <recent> [message #] [text]`\n'
                                                                'Make bigtext reactions to messages. Alternate \n'
                                                                'emoji for most characters exist, but try to limit\n'
                                                                'multiple occurrences of each character.'
                                                                ''.format(self.bot.command_prefix))
                return

            target_message = None

            if type == 'id':
                target_message = await self.bot.get_message(ctx.message.channel, arg1)
                text = arg2 + ' ' + text
            elif type == 'user':
                if ctx.message.mentions:
                    usr_messages = []
                    async for m in self.bot.logs_from(ctx.message.channel, limit=20):
                        if m.author == ctx.message.mentions[0]:
                            usr_messages.append(m)
                    m_index = 0
                    if self.is_num(arg2):
                        m_index = int(arg2) - 1
                        if m_index < 0:
                            m_index = 0
                    target_message = usr_messages[m_index]
            elif type == 'recent' or (is_num(type) is not None):
                if self.is_num(type) is not None:
                    message_num = int(type)
                    text = '{} {} {}'.format(arg1, arg2, text)

                elif self.is_num(arg1):
                    message_num = int(arg1)
                    text = arg2 + ' ' + text
                else:
                    return
                if message_num < 1:
                    message_num = 1
                m_on = 0
                async for m in self.bot.logs_from(ctx.message.channel, limit=int(message_num + 1)):
                    if m_on == message_num:
                        target_message = m
                        break
                    m_on += 1

            if not target_message:
                logs = self.bot.logs_from(ctx.message.channel, limit=2)
                target_message = logs[1]

            used_emotes = []
            failures = []  # for troubleshooting

            # literally get key by value, how clever i know
            def get_key(emoji: str):
                for k, v in emoji_alphabet.items():
                    if emoji in v:
                        return k

            # begin by loading current reactions into used_emotes
            if target_message.reactions:
                for r in target_message.reactions:  # type:discord.Reaction
                    if isinstance(r.emoji, str):
                        used_emotes.append(r.emoji)
                        char = get_key(r.emoji)
                        if char in text:
                            text = text[text.find(char)+1:]

            lower = text.lower()
            skip = False  # for skipping loops when pairs are present

            for i, c in enumerate(lower):
                if skip:
                    skip = False
                    continue

                pair = lower[i:i+2]  # check for letter pairs first

                if len(pair) == 2:
                    if pair in emoji_alphabet:
                        e = emoji_alphabet[pair][0]
                        if e not in used_emotes:
                            try:
                                await self.bot.add_reaction(target_message, e)
                            except Exception as e:
                                failures.append(e)
                            used_emotes.append(e)
                            skip = True
                            continue

                if c in emoji_alphabet:
                    for e in emoji_alphabet[c]:
                        if e not in used_emotes:
                            try:
                                await self.bot.add_reaction(target_message, e)
                            except discord.Forbidden:
                                failures.append(e)
                            except discord.HTTPException:
                                failures.append(e)
                            used_emotes.append(e)
                            break

            out = await self.bot.say('✅')

            schedule_delete(self.bot, out, 5)

        @self.bot.command(pass_context=True)
        async def timein(ctx, *, arg: str):
            if arg == 'help':
                await self.bot.say("**Timein help:**\n"
                                   "`{0}timein [location]`\n"
                                   "Get the current time in a location. Format `location` as an "
                                   "address, city, state, etc. Example:\n"
                                   "`{0}timein London`"
                                   "".format(self.bot.command_prefix))
                return

            if arg in ['only time', 'time zone', 'time']:
                arg = 'Montana'

            location = await worldtime.get_location(query=arg)

            if location:
                time_there = await worldtime.get_time(location=location)
                if time_there:
                    em = discord.Embed(title='───────────────────────', color=0x00b6ff)  # sky blue
                    em.set_author(name='World Time', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f30e.png')
                    em.add_field(name='__Location__', value=location.address, inline=False)
                    em.add_field(name='__Time Zone__', value='{} - {}'.format(time_there.timezone_id,
                                                                              time_there.timezone_name))
                    tm = time_there.time.strftime('%I:%M:%S %p')
                    if tm[0] == '0':
                        tm = tm[1:]
                    em.add_field(name='__Time__', value=tm, inline=False)
                    em.add_field(name='__Date__', value=time_there.time.strftime('%A, %B %d, %Y'), inline=False)

                    await self.bot.say(embed=em)
                else:
                    m = await self.bot.say('An error occurred while searching.')
                    schedule_delete(self.bot, m, 5)
            elif location is None:
                m = await self.bot.say('No location found for `{}`. Please be more specific.'.format(arg))
                schedule_delete(self.bot, m, 5)
            elif location is False:
                m = await self.bot.say('An error occurred while searching.')
                schedule_delete(self.bot, m, 5)

        @self.bot.command(pass_context=True)
        async def poll(ctx, *, args: str):
            in_args = self.strip_args(args)
            options = []
            name = 'Poll'
            for a, o in in_args:
                if a == 'option':
                    options.append(o)
                elif a == 'name':
                    name += ' - {}'.format(o)

            while len(options) > 9:
                options.pop()

            if len(options) < 1:
                await self.bot.say('Please add at least 1 option.')
                return

            scores = {}
            for i, o in enumerate(options):
                scores[i+1] = 0

            def get_poll(scores: dict, options: list):
                em = discord.Embed(title='───────────────────────', color=random.randint(0, 0xffffff))
                em.set_author(name=name, icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4ca.png')

                poll_bar = '🔲🔲🔲🔲🔲🔲🔲🔲🔲🔲🔲🔲🔲🔲🔲'

                total = 0
                for v in scores.values():
                    total += v
                if total == 0:
                    for o in options:
                        em.add_field(name=o, value='0%', inline=False)
                    return em
                else:
                    for i, o in enumerate(options):
                        percent = round(scores[i+1]/total, 1)
                        em.add_field(name=o,
                                     value='{} {}%'.format(poll_bar[:int(len(poll_bar) * percent)], round(percent * 100)),
                                     inline=False)
                    return em

            em = get_poll(scores, options)

            base_message = await self.bot.send_message(ctx.message.channel, embed=em)
            reactions = []
            has_voted = []
            for i, o in enumerate(options):
                await self.bot.add_reaction(base_message, num2regional[i+1])
                reactions.append(num2regional[i+1])
            await self.bot.wait_for_reaction(num2regional[len(options)])
            while True:
                reaction, user = await self.bot.wait_for_reaction(reactions,
                                                                  message=base_message,
                                                                  timeout=180)
                if not reaction:
                    break

                current_voted = len(has_voted)

                if user.id not in has_voted:
                    choice = str(reaction.emoji)
                    if choice in reactions:
                        has_voted.append(user.id)
                        scores[regional2num[choice]] += 1

                if len(has_voted) > current_voted:
                    em = get_poll(scores, options)
                    await self.bot.edit_message(base_message, embed=em)

        @self.bot.command(pass_context=True)
        async def strawpoll(ctx, *, args: str):

            straw_poll = None

            if 'option=' not in args:
                in_args = shlex.split(args, ' ')
                if len(in_args) > 2:
                    straw_poll = StrawPoll(title=in_args[0], options=in_args[1:])
            else:
                in_args = self.strip_args(args)
                input_options = {'title': 'no title', 'options': []}
                for k, v in in_args:
                    if k == 'option':
                        input_options['options'].append(v)
                    else:
                        input_options[k] = v

                if len(input_options['options']) < 2:
                    input_options['options'].append('no')

                if len(input_options['options']) < 2:
                    input_options['options'].append('u')

                straw_poll = StrawPoll(**input_options)

            if not straw_poll:
                await self.bot.send_message(ctx.message.channel, 'Error in data input')
                return

            success = await straw_poll.create()

            if success:
                await self.bot.send_message(ctx.message.channel, 'http://www.strawpoll.me/{}'.format(success['id']))
            else:
                await self.bot.send_message(ctx.message.channel, 'Straw Poll could not be created ¯\_(ツ)_/¯')

        @self.bot.command(pass_context=True)
        async def straya(ctx, *, text: str):
            out = ""

            def yeahnah():
                return random.choice(['yeah', 'nah'])

            for w in text.split(' '):
                if w == 'yes':
                    out += " nah yeah"
                elif w == 'no':
                    out += " yeah nah"
                elif w == 'yeah':
                    out += 'yeah yeah'
                elif w == 'nah':
                    out += 'nah nah'
                else:
                    if random.choice([True, False]):
                        out += " {}".format(yeahnah())
                    else:
                        out += " {} {}".format(yeahnah(), yeahnah())

            await self.bot.send_message(ctx.message.channel, out)

        @self.bot.group(pass_context=True)
        async def ishihara(ctx):
            pass

        @ishihara.command(pass_context=True)
        async def solve(ctx, link: str = None):

            in_server = None
            if ctx.message.server:
                in_server = self.bot.get_server(server=ctx.message.server)

            base_image = await command_util.extract_image(ctx, link, in_server)

            colors = self.get_colors(base_image, 40)
            replace_colors = []
            for c in colors:
                if not self.color_compare(c, (0, 0, 0, 0), 20) and not self.color_compare(c, (255, 255, 255, 255), 20):
                    present = False
                    for pc in replace_colors:
                        if self.color_compare(pc, c, 50):
                            present = True
                    if not present:
                        replace_colors.append(c)

            def replace_method(base_image, tol=30):
                for color in replace_colors:
                    replace_color(base_image, self.color_int(color), 0x000000, tol)

            if base_image:
                await self.bot.say('Tolerance? Default is 30.')
                m = await self.bot.wait_for_message(timeout=30, author=ctx.message.author, channel=ctx.message.channel)
                if is_num(m.content):
                    tol = int(m.content)
                else:
                    tol = 30
                try:
                    await self.bot.loop.run_in_executor(def_executor, lambda: replace_method(base_image, tol))

                    base_image.save('solved.png', format='PNG')

                    await self.bot.send_file(ctx.message.channel, 'solved.png')
                except Exception:
                    await self.bot.send_message(ctx.message.channel, 'Solve failed.')
                    return
            else:
                await self.bot.send_message(ctx.message.channel, 'Image invalid.')
                return

            try:
                os.remove('solved.png')
            except Exception:
                pass

        @self.bot.command(pass_context=True)
        async def hug(ctx, *, arg: str = None):
            member_name = None

            if arg:
                member = command_util.find_arg(ctx, arg, ['member'])

                if type(member) is str:
                    member_name = await command_util.find_member(ctx, member, percent=50, return_name=True)
                    if not member_name:
                        member_name = arg
                else:
                    member_name = member.display_name

            image = random.choice(global_util.hug_library)

            single_options = ['**{}** gets a hug',
                              'Here, **{}**, have a hug',
                              '*Hugs* for **{}**']

            duo_options = ['**{0}** gets a hug from **{1}**',
                           '**{1}** hugs **{0}**',
                           '**{1}** gives **{0}** a hug']

            if member_name:
                desc = random.choice(duo_options).format(member_name, ctx.message.author.name)
            else:
                desc = random.choice(single_options).format(ctx.message.author.name)

            em = discord.Embed(title=CHAR_ZWS, description=desc, color=random.randint(0, 0xffffff))
            em.set_image(url=image)

            await self.bot.send_message(ctx.message.channel, embed=em)

        @self.bot.command(pass_context=True)
        async def pat(ctx, *, arg: str = None):
            member_name = None

            if arg:
                member = command_util.find_arg(ctx, arg, ['member'])

                if type(member) is str:
                    member_name = await command_util.find_member(ctx, member, percent=50, return_name=True)
                    if not member_name:
                        member_name = arg
                else:
                    member_name = member.display_name

            image = random.choice(global_util.pat_library)

            single_options = ['**{}** gets a pat',
                              'Here, **{}**, have a pat',
                              '*Headpats* for **{}**']

            duo_options = ['**{0}** gets a pat from **{1}**',
                           '**{1}** pats **{0}**',
                           '**{1}** gives **{0}** headpats']

            if member_name:
                desc = random.choice(duo_options).format(member_name, ctx.message.author.name)
            else:
                desc = random.choice(single_options).format(ctx.message.author.name)

            em = discord.Embed(title=CHAR_ZWS, description=desc, color=random.randint(0, 0xffffff))
            em.set_image(url=image)

            await self.bot.send_message(ctx.message.channel, embed=em)

        @self.bot.command(pass_context=True)
        async def edithugs(ctx, arg: str, *, link: str):
            if ctx.message.author.id != OWNER_ID:
                return

            if arg == 'add':
                if ' @r ' in link:
                    for url in link.split(' @r '):
                        if url not in global_util.hug_library:
                            global_util.hug_library.append(url)
                elif '\n' in link:
                    for url in link.split('\n'):
                        if url not in global_util.hug_library:
                            global_util.hug_library.append(url)
                else:
                    global_util.hug_library.append(link)
            elif arg.startswith('rem'):
                global_util.hug_library.remove(link)
            storage.write_hugs()

            out = await self.bot.say('✅')
            schedule_delete(self.bot, out, 5)

        @self.bot.command(pass_context=True)
        async def editpats(ctx, arg: str, *, link: str):
            if ctx.message.author.id != OWNER_ID:
                return

            if arg == 'add':
                if ' @r ' in link:
                    for url in link.split(' @r '):
                        if url not in global_util.pat_library:
                            global_util.pat_library.append(url)
                elif '\n' in link:
                    for url in link.split('\n'):
                        if url not in global_util.pat_library:
                            global_util.pat_library.append(url)
                else:
                    global_util.pat_library.append(link)
            elif arg.startswith('rem'):
                global_util.pat_library.remove(link)
            storage.write_pats()

            out = await self.bot.say('✅')
            schedule_delete(self.bot, out, 5)

        @self.bot.command(pass_context=True)
        async def pick(ctx, *, arg: str):
            choices = arg.split(' ')
            if len(choices) == 1:
                choices = arg.split(',')
            if len(choices) > 10:
                choices = choices[:10]

            chosen = random.choice(choices)

            await self.bot.say('I pick **{}**'.format(chosen))

        @self.bot.command(pass_context=True, aliases=['eight-ball', '8ball', 'eb'])
        async def eight_ball(ctx, *, arg: str):
            choice_im = await olliebot_api.get_eight_ball()

            em = discord.Embed(title=CHAR_ZWS, color=0x0000ff)
            em.add_field(name='__{} asked:__'.format(ctx.message.author.display_name), value=arg, inline=False)
            em.set_thumbnail(url=choice_im)

            await self.bot.send_message(ctx.message.channel, embed=em)

        @self.bot.command(pass_context=True, aliases=['colour'])
        async def color(ctx, arg: str, green: int = None, blue: int = None):

            if arg == 'help':
                await self.bot.whisper('**Color usage:**\n'
                                       '`{0}color [hex]`\n'
                                       '`{0}color [red] [green] [blue]`\n'
                                       'Displays a sample of the requested color.\n'
                                       '`[hex]` may be formatted as a 1-6 digit hexadecimal\n'
                                       'number beginning with prefixes `0x` or `#`.\n'
                                       '`red`, `[green]` and `[blue]` should each be an\n'
                                       'integer from 0-255.\n'
                                       '*Examples:*\n'
                                       '`{0}color #ffaa00`\n'
                                       '`{0}color 255 170 0`'
                                       ''.format(self.bot.command_prefix))
                return

            image = None

            if green is not None and blue is not None:
                # convert arg (red) to int
                if is_num(arg) is not None:
                    arg = int(arg)
                else:
                    await self.bot.say('Please format RGB arguments as integers.', delete_after=5)
                    print('arg is {}'.format(arg))
                    return

                # check ranges
                if 0 <= arg <= 255 and 0 <= green <= 255 and 0 <= blue <= 255:
                    # print('rgb found as {} {} {}'.format(arg, green, blue))
                    image = self.build_color_sample(rgb=(arg, green, blue))
                else:
                    await self.bot.say('Please format `[red] [green] [blue]` as integers ranging from 0-255.',
                                       delete_after=5)
                    return
            else:
                # check for hex formatting
                if 2 < len(arg) <= 8:

                    absolute = arg.replace('0x', '').replace('#', '')
                    if len(absolute) > 6:
                        await self.bot.say('Please pass a 0-6 digit hex code.', delete_after=5)
                        return

                    val = arg.replace('#', '0x')
                    arg = arg.replace('0x', '#')

                    # convert to int
                    try:
                        val = int(val, 16)
                    except:
                        await self.bot.say('Please format `[hex]` as a hexadecimal color tag with digits 0-9,a-f.',
                                           delete_after=5)
                        return

                    if '#' not in arg:
                        arg = '#' + arg

                    image = self.build_color_sample(hex_code=(arg, val))

            if image:
                image_bytes = io.BytesIO()
                image.save(image_bytes, format='PNG')
                await self.bot.send_file(ctx.message.channel,
                                         io.BytesIO(image_bytes.getvalue()),
                                         filename='color.png')

        @self.bot.command(pass_context=True)
        async def textart(ctx, *, arg: str):

            font = 'standard'
            for word in global_util.split_iter(arg, '=:'):
                if word.startswith(('font=', 'font:')):
                    arg = arg.replace(word, '')
                    font = word.replace('font=', '').replace('font:', '')

                    if font not in fig_fonts:
                        await self.bot.say('No font `{}` exists!'.format(font), delete_after=5)
                        font = 'standard'

                    break

            if len(arg) > 40:
                arg = arg[:40]

            formatted = pyfiglet.figlet_format(arg, font=font)[:1990]

            await self.bot.say('```\n{}\n```'.format(formatted))

        @self.bot.group(pass_context=True)
        async def birthday(ctx):
            pass

        @birthday.command(pass_context=True)
        @self.bot.test_high_perm
        async def add(in_server, ctx, user: discord.User, *, date: str):
            bd = in_server.get_birthday(user=user)
            if bd:
                await self.bot.say('User **{}** already has a birthday registered'.format(user.name))
                return

            try:
                dt = timestring.Date(date).date
            except:
                await self.bot.say('Please be more clear about which date you would like to add.')
                return
            bd = in_server.add_birthday(user=user, dt=dt)

            storage.write_birthdays(in_server)

            await self.bot.say('Added birthday for **{}** as {}'.format(user.name, bd.dt.strftime('%B %-d')))

        @birthday.command(pass_context=True)
        @self.bot.test_high_perm
        async def edit(in_server, ctx, user: discord.User, *, date: str):
            bd = in_server.get_birthday(user=user)
            if not bd:
                await self.bot.say('User **{}** does not have a birthday registered'.format(user.name))
                return

            try:
                dt = timestring.Date(date).date
            except:
                await self.bot.say('Please be more clear about which date you would like to add.')
                return

            bd.dt = dt

            storage.write_birthdays(in_server)

            await self.bot.say('Changed birthday for **{}** to {}'.format(user.name, bd.dt.strftime('%B %-d')))

        @birthday.command(pass_context=True)
        @self.bot.test_high_perm
        async def remove(in_server, ctx, user: discord.User):
            bd = in_server.get_birthday(user=user)
            if not bd:
                await self.bot.say('User **{}** does not have a birthday registered'.format(user.name))
                return

            in_server.birthdays.remove(bd)

            storage.write_birthdays(in_server)

            await self.bot.say('Removed birthday for **{}**'.format(user.name))

        @birthday.command(pass_context=True)
        @self.bot.test_server
        async def get(in_server, ctx, *, arg: str):
            user = command_util.find_arg(ctx, arg, ['user'])
            if not isinstance(user, discord.User):
                user = await command_util.find_member(ctx, arg, percent=50)
                if not user:
                    try:
                        dt = timestring.Date(arg).date
                    except:
                        await self.bot.say('Please provide a user or date to get birthdays from')
                        return

            if user:
                bd = in_server.get_birthday(user=user)
                if not bd:
                    await self.bot.say('No birthday found for user **{}**'.format(user.name))
                    return

                em = discord.Embed(title=global_util.TITLE_BAR,
                                   description='**{}**\'s birthday is on **{}**'.format(user.name, bd.dt.strftime('%B %-d')),
                                   color=0xffff00)
                em.set_author(name='Birthday', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f389.png')

                await self.bot.send_message(ctx.message.channel, embed=em)

            elif dt:
                bds = in_server.get_birthdays(date=dt)
                if not bds:
                    await self.bot.say('No users found with birthday **{}**'.format(dt.strftime('%B %-d')))
                    return

                em = discord.Embed(title=global_util.TITLE_BAR,
                                   description='__Date: {}__'.format(dt.strftime('%B %-d')),
                                   color=0xffff00)
                em.set_author(name='Birthdays', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f389.png')

                names = ''
                for bd in bds:  # type: Birthday
                    names += '**{}**, '.format(bd.user.name)

                em.add_field(name=names[:-2], value=global_util.CHAR_ZWS)  # add names up to last ', '

                await self.bot.send_message(ctx.message.channel, embed=em)

        @self.bot.command(pass_context=True)
        async def clap(ctx, *, arg: str):
            output = ''.join([x + '👏' for x in arg.split(' ')])
            await self.bot.say(output[:1999])

        @self.bot.command(pass_context=True, aliases=['blap'])
        async def bclap(ctx, *, arg: str):
            output = ''.join([x + '👏🏿' for x in arg.split(' ')])
            await self.bot.say(output[:1999])

    @staticmethod
    def is_num(text: str):
        try:
            num = int(text)
            return num
        except ValueError:
            return None

    @staticmethod
    def get_wiki_page(title: str):
        terms = wikipedia.search(title)
        if not terms:
            return None
        use_title = title
        for term in terms:
            if term.find('disambiguation') == -1:
                use_title = term
                break
        try:
            page = wikipedia.page(use_title)
        except DisambiguationError as e:
            # print('OPTION CHOSEN: ' + e.options[0])
            new_title = e.options[0]
            if new_title.find('§') != -1:
                keys = new_title.split(' ')
                new_title = keys[0]
                # print('Changed to ' + new_title)
            try:
                page = wikipedia.page(new_title)
            except DisambiguationError:
                return False
        except PageError:
            return None
        simple_summary = page.summary[:page.summary.find('\n')]

        img = None
        for link in page.images:
            if link.find(page.title.replace(' ', '_')) != -1:
                img = link
        if not img:
            first_word = page.title.split(' ')[0]
            for link in page.images:
                if link.find(first_word) != -1:
                    img = link
        return {'title': page.title,
                'summary': simple_summary,
                'url': page.url,
                'image': img}

    @staticmethod
    def strip_args(args: str) -> list:
        arg_list = shlex.split(args, ' ')
        out_list = []
        for a in arg_list:
            if a:
                pieces = a.split('=')
                out_list.append((pieces[0], pieces[1]))
        return out_list

    @staticmethod
    def on_range(arg, min, max):
        """Test for value within a range

        Inclusive:Exclusive bounds

        :param arg: Test value
        :param min: Lower bound of range
        :param max: Upper bound of range
        :return: `bool`
        """
        return min <= arg < max

    @staticmethod
    def get_contrast(red, green, blue) -> int:
        if (1 - (0.299 * red + 0.587 * green + 0.114 * blue) / 255) < 0.5:
            return 0
        else:
            return 0xffffff

    def build_color_sample(self, rgb: tuple = None, hex_code: tuple = None) -> Image:
        """
        Generates a 100 x 50 color sample with hex code printed, centered

        :param rgb: tuple(int), formatted (red, green, blue)
        :param hex_code: int, intended format 0x######
        :return: :class:`Image`, the resulting sample
        """
        sample_width, sample_height = (100, 50)
        font = ImageFont.truetype('arial.ttf', 20)

        if rgb:
            # build background
            image = Image.new('RGB', (sample_width, sample_height), rgb)

            # build text string
            color = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
            color_text = hex(color)[2:]
            while len(color_text) < 6:
                color_text = '0' + color_text

            color_text = '#' + color_text

            # find text fill
            fill = self.get_contrast(rgb[0], rgb[1], rgb[2])

            # draw text
            draw = ImageDraw.Draw(image)
            w, h = draw.textsize(color_text, font=font)
            draw.text(((sample_width - w)/2, (sample_height - h)/2), color_text, fill=fill, font=font)

            return image
        elif hex_code:
            color_text = hex_code[0]
            color_value = hex_code[1]
            # build text string
            # color_text = '#{}'.format(hex(hex_code)[2:])

            # build background
            image = Image.new('RGB', (sample_width, sample_height), color_text)

            # get fill - shift r, g, b out of hex_code first
            fill = self.get_contrast((color_value >> 16) & 0xff, (color_value >> 8) & 0xff, color_value & 0xff)

            # draw text
            draw = ImageDraw.Draw(image)
            w, h = draw.textsize(color_text, font=font)
            draw.text(((sample_width - w)/2, (sample_height - h)/2), color_text, fill=fill, font=font)

            return image

    @staticmethod
    def color_compare(a, b, tol):
        if abs(a[0] - b[0]) <= tol:
            if abs(a[1] - b[1]) <= tol:
                if abs(a[2] - b[2]) <= tol:
                    return True
        return False

    def get_colors(self, im, tolerance=5):
        colors = []
        im = im.resize((150, 150))
        data = im.load()
        colors.append(data[0, 0])
        for y in range(im.size[1]):
            for x in range(im.size[0]):
                color = data[x, y]
                present = False
                for c in colors:
                    if self.color_compare(c, color, tolerance):
                        present = True
                        break
                if not present:
                    colors.append(color)
        return colors

    @staticmethod
    def color_tuple(c_hex: int):
        alpha = (c_hex & 0xff000000) >> 24
        red = (c_hex & 0xff0000) >> 16
        green = (c_hex & 0xff00) >> 8
        blue = c_hex & 0xff
        return red, green, blue, alpha

    @staticmethod
    def color_int(c_tuple: tuple):
        return (c_tuple[3] << 24) | (c_tuple[0] << 16) | (c_tuple[1] << 8) | c_tuple[2]


def setup(bot):
    return Fun(bot)