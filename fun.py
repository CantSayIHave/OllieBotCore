import functools

import discord
from discord.ext import commands
import copy
import random
import aiohttp
import io
import youtube_dl
import wikipedia
import time
from wikipedia import DisambiguationError
from wikipedia import PageError
from global_util import *


num2word = {'0': 'zero',
            '1': 'one',
            '2': 'two',
            '3': 'three',
            '4': 'four',
            '5': 'five',
            '6': 'six',
            '7': 'seven',
            '8': 'eight',
            '9': 'nine'}


class Fun:
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def reee(ctx, arg: str = None, *, msg: str = None):
            if arg == 'help':
                await self.bot.send_message(ctx.message.author, "**Reee usage**:\n"
                                                                "Set reee on/off: `{0}reee <true/false>`\n"
                                                                "Get reee state: `{0}reee`\n"
                                                                'Set reee response: `{0}reee <response> [response]`\n'
                                                                'Get reee response: `{0}reee <response>`'.format(
                    self.bot.command_prefix))
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if arg is None:
                await self.bot.say('reee is set to ' + str(in_server.reee).lower())
                return

            if arg.lower() == 'true':
                in_server.reee = True
                await self.bot.say('reee set to true')
                return
            elif arg.lower() == 'false':
                in_server.reee = False
                await self.bot.say('reee set to false')
                return

            if arg == 'response' and msg is None:
                await self.bot.say('reee response is set to `{0}`'.format(in_server.reee_message))
                return

            if arg == 'response' and msg is not None:
                in_server.reee_message = msg
                writeServerData(self.bot, in_server)
                await self.bot.say('reee response now set to `{0}`'.format(in_server.reee_message))

        @self.bot.command(pass_context=True)
        async def good(ctx, noun: str = None):
            if noun == 'bot':
                await self.bot.say('good human')
            elif noun == 'human':
                await self.bot.say('GOOD FELLOW HUMAN')
            else:
                await self.bot.say('good what?')

        @self.bot.command(pass_context=True)
        async def bad(ctx, arg: str = None):
            if arg is None:
                await self.bot.say('no u')
            if arg == 'bot':
                await self.bot.say('{0} bad human'.format(ctx.message.author.mention))
            elif arg == 'human':
                await self.bot.say('{0} BAD FELLOW HUMAN AS WELL'.format(ctx.message.author.mention))

        @self.bot.command(pass_context=True)
        async def playing(ctx, *, message: str):
            if not has_high_permissions(ctx.message.author, b=self.bot):
                return

            if message == 'help':
                await self.bot.send_message(ctx.message.author, '**Playing usage**: `{0}playing [thing]`\n'
                                                                "Changes bot's `playing` status\n"
                                                                'Argument does not need quotes\n'
                                                                'Example: `{0}playing with carrots`'.format(
                    self.bot.command_prefix))
                return

            self.bot.playing_message = message
            writeBotData(self.bot)

            await self.bot.change_presence(game=discord.Game(name=message, type=0))
            await self.bot.say('Changed `playing` status to `{0}`'.format(message))

        @self.bot.command(pass_context=True)
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

            global num2word
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
                    out_str += ':{}:'.format(num2word[c])
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
        async def convert(ctx, new_format: str, dummy_link: str = None):

            if new_format == 'help':
                await self.bot.send_message(ctx.message.author, '**Convert help:**\n'
                                                                '`{}convert [new filetype] (embed image)`\n'
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
        async def joined(ctx, member: discord.Member = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            if not member:
                member = ctx.message.author

            e = discord.Embed(description="{0} joined {1} on {2}".format(member.display_name,
                                                                         ctx.message.server.name,
                                                                         member.joined_at.strftime("%Y-%m-%d at "
                                                                                                   "%H:%M:%S")),
                              color=0x00d114)
            e.set_author(name=member.name, icon_url=member.avatar_url)

            await self.bot.say(embed=e)

        @self.bot.command(pass_context=True)
        async def userinfo(ctx, member: discord.Member = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            if not member:
                member = ctx.message.author

            e = discord.Embed(title='════╣User Info╠════\n{}'.format(CHAR_ZWS), color=member.colour)
            e.set_author(name=member.name, icon_url=member.avatar_url)

            if member == ctx.message.server.owner:
                e.add_field(name='Owns this server.', value=CHAR_ZWS, inline=False)

            e.add_field(name='Joined __{}__'.format(ctx.message.server.name),
                        value=member.joined_at.strftime('%d-%m-%Y at %H:%M:%S'),
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

            e.add_field(name='Created', value=member.created_at.strftime('%Y-%m-%d at %H:%M:%S'), inline=False)

            await self.bot.say(embed=e)

        @self.bot.command(pass_context=True)
        async def ytdl(ctx, link: str):
            if not has_high_permissions(ctx.message.author, b=self.bot):
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
                    if 'adv' in mods:
                        favor = 'adv'
                        mods = mods.replace('adv','')
                    elif 'dis' in mods:
                        favor = 'dis'
                        mods = mods.replace('dis','')

                    if '+' in mods:
                        extra = mods[mods.find('+'):]
                    elif '-' in mods:
                        extra = mods[mods.find('-'):]

                dice = roll_in[0:token_mods].split('d')
                iterations = self.is_num(dice[0])
                sides = self.is_num(dice[1])

                if not iterations:
                    iterations = 1

                if iterations:
                    if iterations < 1:
                        iterations = 1

                if favor:
                    iterations = 2

                if not sides:
                    sides = 1

                if sides:
                    if sides < 1:
                        sides = 1

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
                    async with session.get('http://random.cat/meow') as resp:
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

            if self.is_num(num):
                num = int(num)
                if num > 1000:
                    await self.bot.say('https://corgiorgy.com/')
                    return
            elif num == '∞':
                await self.bot.say('https://corgiorgy.com/')
                return

            if not num:
                num = 1

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
        async def late(ctx, arg: str = None, to_set: int = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if in_server.name != 'Shoe0nHead':
                return

            is_admin = checkAdmin(ctx.message.author.id)

            if not arg:
                if not in_server.late:
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
                    minutes = int((time.time() - in_server.late) / 60)
                    await self.bot.say('Shoe is now {} minutes late'.format(minutes))
            elif arg == 'start' and is_admin:
                in_server.late = time.time()
                await self.bot.say('Late timer started.')
            elif arg == 'stop' and is_admin:
                in_server.late = None
                await self.bot.say('Late timer stopped.')
            elif arg == 'set' and to_set and is_admin:
                in_server.late = time.time() - (to_set * 60)
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
            elif type == 'recent':
                if self.is_num(arg1):
                    message_num = int(arg1)
                    if message_num < 1:
                        message_num = 1
                    m_on = 0
                    async for m in self.bot.logs_from(ctx.message.channel, limit=int(message_num + 1)):
                        if m_on == message_num:
                            target_message = m
                            break
                        m_on += 1
                    text = arg2 + ' ' + text

            if not target_message:
                logs = self.bot.logs_from(ctx.message.channel, limit=2)
                target_message = logs[1]

            used_emotes = []
            failures = []

            for c in text.lower():
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
            print('OPTION CHOSEN: ' + e.options[0])
            new_title = e.options[0]
            if new_title.find('§') != -1:
                keys = new_title.split(' ')
                new_title = keys[0]
                print('Changed to ' + new_title)
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
    def is_num(text: str):
        try:
            num = int(text)
            return num
        except ValueError:
            return None


def setup(bot):
    return Fun(bot)