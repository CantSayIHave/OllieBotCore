import discord
import asyncio
from discord.ext import commands
from base64 import b64encode
import time
import io
import aiohttp
from PIL import Image
from global_util import *
from containers import *


# custom help dict to hold data on command accessibility
help_args = {'clear': {'d': 'clear bot messages', 'm': True},
             'convert': {'d': 'convert image to different format', 'm': False},
             'b-ify': {'d': 'add some 🅱️ to text', 'm': False},
             'bigtext': {'d': 'transform text into regional indicators', 'm': False},
             'block': {'d': 'block any command from non-mods', 'm': True},
             'bun': {'d': 'summon a bun', 'm': False},
             'emotes': {'d': 'suggest server emotes to the mods', 'm': False},
             'good': {'d': 'easy way to check if bot is online', 'm': True},
             'getraw': {'d': 'get raw text from a message', 'm': True},
             'info': {'d': 'get bot info', 'm': False},
             'music': {'d': 'manage/play music from youtube', 'm': False},
             'perm': {'d': 'set user permissions', 'm': True},
             'playing': {'d': "set bot's 'playing' message", 'm': True},
             'prefix': {'d': "set bot's command prefix", 'm': True},
             'quote': {'d': 'manage/call quotes', 'm': False},
             'reee': {'d': 'manage autistic screaming response', 'm': True},
             'role': {'d': 'automate mass roll assignments', 'm': True},
             'roll': {'d': 'dice roller', 'm': False},
             'rss': {'d': 'manage rss feeds for each channel', 'm': True},
             'spamtimer': {'d': 'set spam timer for quotes', 'm': True},
             'think': {'d': 'really makes you think', 'm': False},
             'thinke': {'d': 'really makes you think about emotes', 'm': False},
             'unblock': {'d': 'unblock commands', 'm': True},
             'usrjoin': {'d': 'manage message to new users', 'm': True},
             'ytdl': {'d': 'youtube to mp3 converter', 'm': True},
             'wiki': {'d': 'search Wikipedia for something', 'm': False}}


class ServerUtils:
    def __init__(self, bot: discord.ext.commands.Bot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def usrjoin(ctx, arg: str = None, *, msg: str = None):

            if arg == 'help':
                await self.bot.send_message(ctx.message.author,
                                            "**Usrjoin usage:**\n"
                                            "Get user join message: `{0}usrjoin <message>`\n"
                                            "Set user join message: `{0}usrjoin <message> [message]`\n"
                                            "Set user join output channel: `{0}usrjoin <channel> [channel]`\n\n"
                                            "The user join message may be formatted with an `@u` as a placeholder "
                                            "for the new member.\n"
                                            "For example: `Welcome to the server, @u!` displays as:\n"
                                            "Welcome to the server, {1}!\n\n"
                                            "The channel this message is displayed in defaults to the server's "
                                            "default channel but may be set with the `<channel>` subcommand, where "
                                            "`[channel]` is the blue-link mention of the channel."
                                            "".format(self.bot.command_prefix, self.bot.user.mention))
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'message' and msg:
                in_server.join_message = msg
                writeServerData(self.bot, in_server)
                await self.bot.say('Set join message to `{}`'.format(in_server.join_message))
                return
            elif arg == 'message' and not msg:
                await self.bot.say('Current join message is `{}`'.format(in_server.join_message))
                return

            if arg == 'channel' and ctx.message.channel_mentions:
                in_server.join_channel = ctx.message.channel_mentions[0].id
                writeServerData(self.bot, in_server)
                await self.bot.say('Set join message channel to {}'.format(ctx.message.channel_mentions[0].mention))
            elif arg == 'channel' and not ctx.message.channel_mentions:
                in_server.join_channel = ctx.message.channel.id
                writeServerData(self.bot, in_server)
                await self.bot.say('Set join message channel to {}'.format(ctx.message.channel.mention))

        @self.bot.group(pass_context=True)
        async def perm(ctx):
            if ctx.invoked_subcommand is None:
                "do not a thing"

        @perm.command(pass_context=True)
        async def admin(ctx, key: str):
            global adminKey, admins
            if key == 'generate':
                # await self.bot.say('Generating key...')
                bytesKey = os.urandom(32)
                adminKey = b64encode(bytesKey).decode('utf-8')
                print('Your key is: ' + adminKey)
            else:
                if key == adminKey:
                    member = ctx.message.author
                    admins.append(member.id)
                    writeAdmins(admins)
                    await self.bot.say('Added {0.mention} as an admin'.format(member))
                else:
                    print('Failed admin attempt on ' + time.strftime('%a %D at %H:%M:%S'))

        @perm.command(pass_context=True)
        async def mod(ctx, member: discord.Member):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            in_server.mods.append(member.id)
            writeServerData(self.bot, in_server)
            await self.bot.say('Added {} to the mod list'.format(member.mention))

        @perm.command(pass_context=True)
        async def unmod(ctx, member: discord.Member):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            try:
                in_server.mods.remove(member.id)
                writeServerData(self.bot, in_server)
                await self.bot.say('Removed {} from the mod list'.format(member.mention))
            except Exception:
                await self.bot.say('{} is not on the mod list'.format(member.mention))

        @perm.command(pass_context=True)
        async def check(ctx, arg: str, member: discord.Member):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'admin':
                if checkAdmin(member.id):
                    await self.bot.say('{} is an admin'.format(member.mention))
                else:
                    await self.bot.say('{} is *not* an admin'.format(member.mention))
            elif arg == 'mod':
                if in_server.is_mod(member.id):
                    await self.bot.say('{} is a mod'.format(member.mention))
                else:
                    await self.bot.say('{} is *not* a mod'.format(member.mention))

        @perm.command(pass_context=True)
        async def rolemod(ctx, arg: str, role: discord.Role = None):
            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Rolemod usage:**\n'
                                                                '`{0}perm rolemod <add/remove> [@role]`\n'
                                                                '`{0}perm rolemod <check> [@role]`'.format(
                    self.bot.command_prefix))
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if role:
                if arg == 'add':
                    in_server.rolemods.append(role.id)
                    writeServerData(self.bot, in_server)
                    await self.bot.say('Added role ' + role.mention + ' to role mod list')
                elif arg == 'remove':
                    if role.id in in_server.rolemods:
                        in_server.rolemods.remove(role.id)
                        writeServerData(self.bot, in_server)
                        await self.bot.say('Removed role ' + role.mention + ' from role mod list')
                    else:
                        await self.bot.say('Role ' + role.mention + ' is not on the role mod list')
                elif arg == 'check':
                    if role.id in in_server.rolemods:
                        await self.bot.say('Role ' + role.mention + ' *is* on the mod list')
                    else:
                        await self.bot.say('Role ' + role.mention + ' *is not* on the mod list')

        @perm.command(pass_context=True)
        async def help(ctx):
            if not has_high_permissions(ctx.message.author, b=self.bot):
                return

            await self.bot.send_message(ctx.message.author,
                                        "**Permissions usage**:\n"
                                        "`{0}perm <mod/unmod> [@mention]`\n"
                                        "`{0}perm <check> <mod> [@mention]`\n"
                                        "Example: `{0}perm mod @Olliebot` or `{0}perm check mod @Olliebot`\n"
                                        "*Note*: make sure [@mention] is a Discord-formatted blue link, "
                                        "like {1}".format(self.bot.command_prefix, self.bot.user.mention))

        @self.bot.command(pass_context=True)
        async def spamtimer(ctx, cmd: str = None, arg: str = None):

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if cmd == 'help':
                await self.bot.send_message(ctx.message.author, "**Spam timer usage**:\n"
                                                                "`{0}spamtimer`\n"
                                                                "`{0}spamtimer <set> [minutes]`\n"
                                                                "`{0}spamtimer <add/remove> [name]`\n"
                                                                "`{0}spamtimer <list>`\n"
                                                                "Sets timer for each `quote` or "
                                                                "add/remove command to spam time".format(
                    self.bot.command_prefix))
                return

            if not cmd:
                if in_server.command_delay == 1:
                    await self.bot.say('Current anti-spam timer is 1 minute')
                else:
                    await self.bot.say('Current anti-spam timer is ' + str(in_server.command_delay) + ' minutes')
            else:
                if cmd == 'set' and arg:
                    arg = int(arg)
                    if arg < 0:
                        arg = 0
                    in_server.command_delay = arg
                    writeBot(self.bot)  # Necessary to save command delay
                    await self.bot.say('Set anti-spam timer to ' + str(arg) + ' minutes')

                elif cmd == 'add' and arg:
                    in_server.spam_timers[arg] = 0
                    writeServerData(self.bot, in_server)
                    await self.bot.say('Added {} to spam timer list'.format(arg))

                elif cmd == 'remove' and arg:
                    in_server.spam_timers.pop(arg, None)
                    writeServerData(self.bot, in_server)
                    await self.bot.say('Removed {} from spam timer list'.format(arg))

                elif cmd == 'listall':
                    out_str = '**__Spam Timed Commands:__**\n'
                    for key in in_server.spam_timers:
                        out_str += '`{}`'.format(key)
                    await self.bot.say(out_str)

        @self.bot.command(pass_context=True)
        async def block(ctx, arg: str, arg2: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Block usage:**\n'
                                                                '`{0}block <all/here> [command]`\n'
                                                                '`{0}block [#channel] [command]`\n'
                                                                '`{0}block <list>`\n'
                                                                'Blocks a specific command from non-mods. You can '
                                                                'block any command, even quotes. \n'
                                                                'Using `all` will block the command server-wide, while '
                                                                '`here` will block in only the channel this is called '
                                                                'from.\n'
                                                                'See `{0}unblock` '
                                                                'to unblock commands'.format(self.bot.command_prefix))
                return

            if arg == 'listall':
                em = discord.Embed(title='───────────────────────', color=0xff0000)  # red
                em.set_author(name='Blocked Commands', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f6ab.png')
                for cmd in in_server.block_list:  # type: BlockItem
                    if cmd.channel == 'all':
                        em.add_field(name='{}{}'.format(self.bot.command_prefix, cmd.name),
                                     value='in *all*',
                                     inline=False)
                    else:
                        em.add_field(name='{}{}'.format(self.bot.command_prefix, cmd.name),
                                     value='in <#{}>'.format(cmd.channel),
                                     inline=False)
                if len(in_server.block_list) < 1:
                    em.add_field(name='No commands are blocked.',
                                 value='Add to this list with `{}block`'.format(self.bot.command_prefix))
                await self.bot.say(embed=em)
                return

            if arg2 == 'block' or arg2 == 'unblock':
                await self.bot.say('This is a keyword and may not be blocked.')
                return

            channel_arg = None
            if ctx.message.channel_mentions:
                if arg == ctx.message.channel_mentions[0].mention:
                    channel_arg = ctx.message.channel_mentions[0]

            # check for existence
            for cmd in in_server.block_list:  # type: BlockItem
                if cmd.name == arg2:
                    if arg == 'all' and cmd.channel == 'all':
                        await self.bot.say('`{}` is already blocked everywhere.'.format(arg2))
                        return
                    elif arg == 'here' and cmd.channel == ctx.message.channel.id:
                        await self.bot.say('`{}` is already blocked here.'.format(arg2))
                        return
                    elif channel_arg:
                        if arg == channel_arg.mention and cmd.channel == channel_arg.id:
                            await self.bot.say('`{}` is already blocked in {}.'.format(arg2, channel_arg.mention))
                            return

            if arg == 'all' and arg2:
                in_server.block_list.append(BlockItem(name=arg2, channel='all'))
                writeServerData(self.bot, in_server)
                await self.bot.say('Added {} to the list of blocked commands for all channels.'.format(arg2))
            elif arg == 'here' and arg2:
                in_server.block_list.append(BlockItem(name=arg2, channel=ctx.message.channel.id))
                writeServerData(self.bot, in_server)
                await self.bot.say('Added {} to the list of blocked commands for {}.'.format(arg2,
                                                                                             ctx.message.channel.mention))
            elif channel_arg:
                in_server.block_list.append(BlockItem(name=arg2, channel=channel_arg.id))
                writeServerData(self.bot, in_server)
                await self.bot.say('Added {} to the list of blocked commands for {}.'.format(arg2, channel_arg.mention))


            if not arg2:
                await self.bot.say('Please pass a name to block')

        @self.bot.command(pass_context=True)
        async def unblock(ctx, arg: str, arg2: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Unblock usage:**\n'
                                                                '`{0}unblock <all/here> [command]`\n'
                                                                '`{0}unblock [#channel] [command]`\n'
                                                                'Unblocks a specific command for non-mods.\n'
                                                                'Use `all` to unblock it everywhere, and `here` to '
                                                                'unblock it in the channel this is called from.\n'
                                                                'See `{0}block` '
                                                                'to block commands'.format(self.bot.command_prefix))
                return

            if arg2 == 'block' or arg2 == 'unblock':
                await self.bot.say('This is a keyword and may not be blocked.')
                return

            channel_arg = None
            if ctx.message.channel_mentions:
                if arg == ctx.message.channel_mentions[0].mention:
                    channel_arg = ctx.message.channel_mentions[0]

            for cmd in in_server.block_list:  # type: BlockItem
                if cmd.name == arg2:
                    if arg == 'all' and cmd.channel == 'all':
                        in_server.block_list.remove(cmd)
                        writeServerData(self.bot, in_server)
                        await self.bot.say('Removed {} from block list for all channels.'.format(arg2))
                        return
                    elif arg == 'here' and cmd.channel == ctx.message.channel.id:
                        in_server.block_list.remove(cmd)
                        writeServerData(self.bot, in_server)
                        await self.bot.say('Removed {} from block list for {}.'.format(arg2,
                                                                                       ctx.message.channel.mention))
                        return
                    elif channel_arg:
                        if cmd.channel == channel_arg.id:
                            in_server.block_list.remove(cmd)
                            writeServerData(self.bot, in_server)
                            await self.bot.say('Removed {} from block list for {}.'.format(arg2, channel_arg.mention))
                            return

            if not arg2:
                await self.bot.say('Please pass a name to unblock.')
                return

            if arg == 'all':
                await self.bot.say('No block for name `{}` in all channels exists.'.format(arg2))
            elif arg == 'here':
                await self.bot.say('No block for name `{}` in {} exists.'.format(arg2, ctx.message.channel.mention))

        @self.bot.command(pass_context=True)
        async def clear(ctx, number: str = '99'):
            if not has_high_permissions(ctx.message.author, b=self.bot):
                return

            if number == 'help':
                await self.bot.send_message(ctx.message.author, '**Clear usage**: `{0}clear [message number]`\n'
                                                                'Clears a number of bot messages'.format(
                    self.bot.command_prefix))
                return

            number = int(number)

            if number > 100:
                await self.bot.say('Maximum clear at one time is 100 messages.')
                number = 100
            if number < 1:
                number = 1

            if number > 1:
                await self.bot.say('Deleting ' + str(number) + ' messages...')
            else:
                await self.bot.say('Deleting 1 message...')

            await asyncio.sleep(1)

            mgs = []  # Empty list to put all the messages in the log
            number = int(number)  # Converting the amount of messages to delete to an integer
            number += 1  # Delete whatever is required plus 'Deleting...'

            async for x in self.bot.logs_from(ctx.message.channel, limit=100):
                if x.author == self.bot.user:
                    mgs.append(x)
                if len(mgs) >= number:
                    break
            while len(mgs) < number:
                async for x in self.bot.logs_from(ctx.message.channel, limit=100, after=mgs[len(mgs) - 1]):
                    if x.author == self.bot.user:
                        mgs.append(x)

            if isinstance(ctx.message.channel, discord.PrivateChannel):
                for m in mgs:
                    await self.bot.delete_message(m)
            else:
                await self.bot.delete_messages(mgs)


        @self.bot.command(pass_context=True)
        async def info(ctx):
            e = discord.Embed(title="**Bot Info**",
                              description="{0} is a bot operated by the **OllieBot Core** network, a Python script "
                                          "developed by <@{1}> and powered by "
                                          "[discord.py](https://github.com/Rapptz/discord.py), a Python API wrapper "
                                          "for Discord.\n\n"
                                          "Feel free to PM me (CantSayIHave) for suggestions and bug reports.\n\n"
                                          "Webpage coming soon.".format(self.bot.user.name, "305407800778162178"),
                              color=0xff9000)
            await self.bot.send_message(ctx.message.author,
                                        embed=e)

        @self.bot.command(pass_context=True)
        async def help(ctx):
            global help_args
            em = discord.Embed(title='Commands:', description='───────────────────────────', color=0xff0000)
            em.set_author(name=self.bot.user.name + ' Help', icon_url=self.bot.user.avatar_url)
            sorted_args = sorted(help_args)
            if has_high_permissions(ctx.message.author, b=self.bot):
                for arg in sorted_args[:-1]:
                    em.add_field(name=arg,
                                 value=help_args[arg]['d'].capitalize(),
                                 inline=False)
                em.add_field(name=sorted_args[-1],
                             value=help_args[sorted_args[-1]]['d'].capitalize() + '\n\n───────────────────────────\n',
                             inline=False)
            else:
                for arg in sorted_args[:-1]:
                    if not help_args[arg]['m']:
                        em.add_field(name=arg,
                                     value=help_args[arg]['d'].capitalize(),
                                     inline=False)
                if not help_args[sorted_args[-1]]['m']:
                    em.add_field(name=sorted_args[-1],
                                 value=help_args[sorted_args[-1]]['d'].capitalize() + '\n\n───────────────────────────\n',
                                 inline=False)

            out_str = 'Commands follow the format\n\n`'
            out_str += '{0}command <required arguments> [optional arguments]`\n\n' \
                       'Note that `optional arguments` means an argument must be provided, ' \
                       'but it can be anything. For example, in:\n\n' \
                       '`{0}music <play/queue> [link/query/search number]`\n\n' \
                       'the arguments provided in <play/queue> **must** be either `play` ' \
                       'or `queue`, but the next argument may be either a youtube link, ' \
                       'a query, or a search result number like so:\n\n`' + \
                       '{0}music play https://www.youtube.com/watch?v=tVj0ZTS4WF4`\n\n' \
                       'To learn more about the syntax of each command, call `' + \
                       '{0}[command] help`'
            em.add_field(name='__Command Syntax__',
                         value=out_str.format(self.bot.command_prefix),
                         inline=False)

            await self.bot.send_message(ctx.message.author, embed=em)

        @self.bot.group(pass_context=True)
        async def emotes(ctx):
            pass

        @emotes.command(pass_context=True)
        async def suggest(ctx, link: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if link is not None:
                if link[:4] != 'http':
                    await self.bot.say('Sorry, but that is not a valid link. Please provide form '
                                       '`http(s):\\\\...`')
                    return
                in_server.suggest_emotes.append(link)
                await self.bot.say('Added link to emote suggestions')
                return
            else:
                await asyncio.sleep(1)
                if ctx.message.attachments:
                    try:
                        if ctx.message.attachments[0]:
                            add_url = ctx.message.attachments[0]['url']
                            if add_url:
                                in_server.suggest_emotes.append(add_url)
                                await self.bot.say('Added image to emote suggestions')
                                return
                    except IndexError:
                        pass
                await self.bot.say('No image detected in message. Please upload image as part of command message')

        @emotes.command(pass_context=True)
        async def add(ctx, name: str, link: str = None, arg: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if link is not None:
                if link[:4] != 'http':
                    await self.bot.say('Sorry, but that is not a valid link. Please provide form '
                                       '`http(s):\\\\...`')
                    return

                if arg != '-c':
                    if link[len(link) - 3:].lower() != 'jpg' and link[len(link) - 3:].lower() != 'png':
                        await self.bot.say('Sorry, but only `jpg` and `png` file types are supported.')
                        return

                with aiohttp.ClientSession() as session:
                    async with session.get(link) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            try:
                                await self.bot.create_custom_emoji(ctx.message.server, name=name, image=image_bytes)
                                await self.bot.say('Added emoji :{}: to server!'.format(name))
                            except discord.Forbidden:
                                await self.bot.say('I do not have permissions to make custom emoji.')
                            except discord.HTTPException:
                                await self.bot.say('Emoji creation failed ¯\_(ツ)_/¯ Perhaps try a different link?')
                        else:
                            await self.bot.say('Link does not return image ¯\_(ツ)_/¯ Perhaps try a different link?')
            else:
                back_msg = ctx.message
                if back_msg.attachments or back_msg.embeds:
                    add_url = None
                    try:
                        add_url = ctx.message.attachments[0]['url']
                    except Exception:
                        try:
                            add_url = ctx.message.embeds[0]['url']
                        except Exception:
                            pass

                    if not add_url:
                        await self.bot.say('Please embed an image.')
                        return

                    try:
                        with aiohttp.ClientSession() as session:
                            async with session.get(add_url) as resp:
                                if resp.status == 200:
                                    image_bytes = await resp.read()

                                    image = Image.open(io.BytesIO(image_bytes))
                                    image = image.convert('RGBA')
                                    new_type = io.BytesIO()
                                    image.save(new_type, 'PNG')
                                    new_bytes = new_type.getvalue()

                                    try:
                                        await self.bot.create_custom_emoji(ctx.message.server, name=name,
                                                                           image=new_bytes)
                                        await self.bot.say('Added emoji :{}: to server!'.format(name))
                                    except discord.Forbidden:
                                        await self.bot.say('I do not have permissions to make custom emoji.')
                                    except discord.HTTPException:
                                        await self.bot.say(
                                            'Emoji creation failed ¯\_(ツ)_/¯ Perhaps try a different link?')
                                else:
                                    await self.bot.say(
                                        'Link does not return image ¯\_(ツ)_/¯ Perhaps try a different link?')
                                    return
                    except Exception:
                        pass
                        await self.bot.say('No image detected in message. Please upload image as part of command message')

        @emotes.command(pass_context=True)
        async def listall(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if len(in_server.suggest_emotes) == 0:
                await self.bot.say('No suggestions found')

            out_str = "**Suggested emotes:**\n"
            for url in in_server.suggest_emotes:
                out_str += '`{0}`\n'.format(url)
            await self.bot.say(out_str)
            return

        @emotes.command(pass_context=True)
        async def clear(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            in_server.suggest_emotes.clear()
            await self.bot.say('Emote suggestions cleared')

        @emotes.command(pass_context=True)
        async def steal(ctx, arg: str, new_name: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if arg[0] == '<':
                arg = arg.replace('<:', '')
                arg = arg.replace('>', '')
                emote = arg.split(':')

                if not new_name:
                    new_name = emote[0]

                add_url = 'https://cdn.discordapp.com/emojis/{}.png'.format(emote[1])
            else:
                emote_uni = hex(ord(arg[0]))[2:]
                add_url = 'https://abs.twimg.com/emoji/v2/72x72/{}.png'.format(emote_uni)

                if not new_name:
                    new_name = emote_uni

            with aiohttp.ClientSession() as session:
                async with session.get(add_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()

                        await self.bot.create_custom_emoji(ctx.message.server, name=new_name,
                                                           image=image_bytes)
                        await self.bot.say('Stole `:{}:` for the server!'.format(new_name))

        @emotes.command(pass_context=True)
        async def help(ctx):
            out_str = "**Emotes usage:**\n"
            if has_high_permissions(ctx.message.author, b=self.bot):
                out_str += '`{0}emotes <suggest> [link]`\n' \
                           '`{0}emotes <suggest> (upload image in message)`\n' \
                           '`{0}emotes <add> <name> [link]`\n' \
                           '`{0}emotes <add> <name> (upload image in message)`\n' \
                           '`{0}emotes <list/clear>`\n' \
                           '*Note: `add`, `list` and `clear` are only visible to and usable by mods\n' \
                           'This is a method for suggesting emotes to the ' \
                           'moderators and adding custom emoji to the server.\n' \
                           '`[link]` should be the full web ' \
                           'address to the image. `suggest/add` ' \
                           'may be called without a link as long as an image ' \
                           'is uploaded within the ' \
                           'message'.format(self.bot.command_prefix)
            else:
                out_str += '`{0}emotes <suggest> [link]`\n' \
                           '`{0}emotes <suggest> (upload image in message)`\n' \
                           'This is a method for suggesting emotes to the ' \
                           'moderators. `[link]` should be the full web ' \
                           'address to the image. This command ' \
                           'may be called without a link as long as an image ' \
                           'is uploaded within the ' \
                           'message'.format(self.bot.command_prefix)

            await self.bot.send_message(ctx.message.author, out_str)

        @self.bot.group(pass_context=True)
        async def role(ctx):
            pass

        @role.command(pass_context=True)
        async def add(ctx, base_role: discord.Role, add_role: discord.Role, no_role: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            try:
                if no_role == 'NoRole':
                    for m in ctx.message.server.members:
                        if len(m.roles) == 1:
                            await self.bot.add_roles(m, add_role)
                    await self.bot.say('Added role {} to all members with no role'.format(add_role.mention))
                else:
                    for m in ctx.message.server.members:
                        for r in m.roles:
                            if r.id == base_role.id:
                                await self.bot.add_roles(m, add_role)
                                break
                    await self.bot.say('Added role {} to all members in role {}'.format(add_role.mention,
                                                                                        base_role.mention))
            except discord.Forbidden:
                await self.bot.say(
                    'Add failed. Bot does not have sufficient permissions to add {} to {}'.format(add_role.mention,
                                                                                                  base_role.mention))
            except discord.HTTPException:
                await self.bot.say('Add failed, roles could not be added for some reason ¯\_(ツ)_/¯')

        @role.command(pass_context=True)
        async def remove(ctx, base_role: discord.Role, rem_role: discord.Role, no_role: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            try:
                if no_role == 'NoRole':
                    for m in ctx.message.server.members:
                        if len(m.roles) == 1:
                            await self.bot.add_roles(m, rem_role)
                    await self.bot.say('Removed role {} from all members with no role'.format(rem_role.mention))
                else:
                    for m in ctx.message.server.members:
                        for r in m.roles:
                            if r.id == base_role.id:
                                await self.bot.remove_roles(m, rem_role)
                                break
                    await self.bot.say('Removed role {} from all members in role {}'.format(rem_role.mention,
                                                                                            base_role.mention))
            except discord.Forbidden:
                await self.bot.say(
                    'Remove failed. Bot does not have sufficient permissions to remove {} from {}'.format(rem_role.mention,
                                                                                                          base_role.mention))
            except discord.HTTPException:
                await self.bot.say('Remove failed, role could not be removed for some reason ¯\_(ツ)_/¯')

        @role.command(pass_context=True)
        async def replace(ctx, base_role: discord.Role, rep_role: discord.Role):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            try:
                for m in ctx.message.server.members:
                    for r in m.roles:
                        if r.id == base_role.id:
                            await self.bot.remove_roles(m, base_role)
                            await self.bot.add_roles(m, rep_role)
                            break
                await self.bot.say('Replaced role {} for all members with role {}'.format(rep_role.mention,
                                                                                          base_role.mention))
            except discord.Forbidden:
                await self.bot.say(
                    'Remove failed. Bot does not have sufficient permissions to replace {} with {}'.format(
                        base_role.mention,
                        rep_role.mention))
            except discord.HTTPException:
                await self.bot.say('Replace failed, role could not be replaced for some reason ¯\_(ツ)_/¯')

        @role.command(pass_context=True)
        async def help(ctx):
            await self.bot.send_message(ctx.message.author,
                                        '**Role usage:**\n'
                                        '`{0}role <add/remove> [base role] [new role] [optional:"NoRole"]`\n'
                                        '`{0}role <replace> [old role] [new role]`\n'
                                        'The role command automates mass addition, removal and replacement of roles. '
                                        'Example:\n'
                                        '`{0}role add @SomeRole @OtherRole` will add `@OtherRole` to all users with '
                                        'role `@SomeRole`\n'
                                        'If the third argument "NoRole" is passed to `add/remove`, the second role '
                                        'will be added to/removed from only users with no role\n'
                                        'In `add/remove`, "base role" is used only to qualify, it will not be '
                                        'affected.\n'
                                        '*Note: make sure [base role] and [new role] are discord-formatted '
                                        'mentions*'.format(self.bot.command_prefix))

        @self.bot.command(pass_context=True)
        async def getraw(ctx, arg: str, arg2: str = None):
            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Getraw help:**\n'
                                                                '`{0}getraw [message id]`\n'
                                                                '`{0}getraw [channel id] [message id]`\n'
                                                                'Returns the raw string from a message. Useful '
                                                                'to capture `:id:` formatted emoji. If `channel_id` '
                                                                'is not provided, current channel will be used.'
                                                                ''.format(self.bot.command_prefix))
                return

            try:
                if arg2:
                    msg = await self.bot.get_message(self.bot.get_channel(arg), arg2)
                    await self.bot.say('```\n{}\n```'.format(msg.content))
                else:
                    msg = await self.bot.get_message(ctx.message.channel, arg)
                    await self.bot.say('```\n{}\n```'.format(msg.content))
            except discord.Forbidden:
                await self.bot.say("I don't have permission for that")

        @self.bot.command(pass_context=True)
        async def nick_all(ctx, new_name: str):
            if not ctx.message.server:
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if new_name == 'help':
                await self.bot.send_message(ctx.message.author, '**Nick-all help:**\n'
                                                                '`{}nick-all [new name]`\n'
                                                                '`{}nick-all <reset>`\n'
                                                                'Change the nickname of everyone on the server to '
                                                                '`new name`. Because why not.\n'
                                                                'Using `reset` will remove all nicknames again.')
                return

            if new_name == 'reset':
                new_name = None

            failures = []

            for m in ctx.message.server.members:
                try:
                    await self.bot.change_nickname(m, new_name)
                except discord.Forbidden:
                    failures.append(m)
                except discord.HTTPException:
                    failures.append(m)

            if len(failures) > 0:
                await self.bot.say('Operation complete. Failed to change: {}'.format(', '.join([x.name for x in failures])))

        @self.bot.command(pass_context=True)
        async def mute(ctx, member: discord.Member, minutes: int = None):
            if not ctx.message.server:
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            try:
                await self.bot.server_voice_state(member=member, mute=True)
                await self.bot.say('Muted ')
            except discord.Forbidden:
                await self.bot.say('I do not have sufficient permissions to do this.')
            except discord.HTTPException:
                await self.bot.say('An error occurred while attempting. Please try again.')


def setup(bot):
    return ServerUtils(bot)
