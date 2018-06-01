import asyncio
from base64 import b64encode

import storage_manager as storage
from discordbot import DiscordBot
from util.global_util import *

# custom help dict to hold data on command accessibility
help_args = {
             'audioconvert': {'d': 'convert audio to different format', 'm': False},
             'clear': {'d': 'clear bot messages', 'm': True},
             'cat': {'d': 'summon a cat', 'm': False},
             'b-ify': {'d': 'add some 🅱️ to text', 'm': False},
             'bigtext': {'d': 'transform text into regional indicators', 'm': False},
             'block': {'d': 'block any command from non-mods', 'm': True},
             'bun': {'d': 'summon a bun', 'm': False},
             'emotes': {'d': 'suggest server emotes to the mods', 'm': False},
             'good': {'d': 'easy way to check if bot is online', 'm': True},
             'getraw': {'d': 'get raw text from a message', 'm': True},
             'imageconvert': {'d': 'convert image to different format', 'm': False},
             'info': {'d': 'get bot info', 'm': False},
             'music': {'d': 'manage/play music from youtube', 'm': False},
             'perm': {'d': 'set user permissions', 'm': True},
             'purge': {'d': 'mass-clear messages', 'm': True},
             'playing': {'d': "set bot's 'playing' message", 'm': True},
             'prefix': {'d': "set bot's command prefix", 'm': True},
             'quote': {'d': 'manage/call quotes', 'm': True},
             'react': {'d': 'react to a message with bigtext', 'm': False},
             'reee': {'d': 'manage autistic screaming response', 'm': True},
             'response': {'d': 'manage custom responses', 'm': True},
             'roles': {'d': 'automate mass roll assignments', 'm': True},
             'roll': {'d': 'dice roller', 'm': False},
             'rss': {'d': 'manage rss feeds for each channel', 'm': True},
             'spamtimer': {'d': 'set spam timer for quotes', 'm': True},
             'think': {'d': 'really makes you think', 'm': False},
             'thinke': {'d': 'really makes you think about emotes', 'm': False},
             'thinkpfp': {'d': 'really makes you think about pfps', 'm': False},
             'unblock': {'d': 'unblock commands', 'm': True},
             'usrjoin': {'d': 'manage message to new users', 'm': True},
             'ytdl': {'d': 'youtube to mp3 converter', 'm': True},
             'wiki': {'d': 'search Wikipedia for something', 'm': False},
             'woof': {'d': 'summon a woof', 'm': False}}


class ServerUtils:
    def __init__(self, bot: DiscordBot):
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

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'message' and msg:
                in_server.join_message = msg
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Set join message to `{}`'.format(in_server.join_message))
                return
            elif arg == 'message' and not msg:
                await self.bot.say('Current join message is `{}`'.format(in_server.join_message))
                return

            if arg == 'channel' and ctx.message.channel_mentions:
                in_server.join_channel = ctx.message.channel_mentions[0].id
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Set join message channel to {}'.format(ctx.message.channel_mentions[0].mention))
            elif arg == 'channel' and not ctx.message.channel_mentions:
                in_server.join_channel = ctx.message.channel.id
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Set join message channel to {}'.format(ctx.message.channel.mention))

        @self.bot.group(pass_context=True)
        async def perm(ctx):
            if ctx.invoked_subcommand is None:
                "do not a thing"

        @perm.command(pass_context=True)
        async def admin(ctx, key: str):
            global adminKey
            if key == 'generate':
                # await self.bot.say('Generating key...')
                bytesKey = os.urandom(32)
                adminKey = b64encode(bytesKey).decode('utf-8')
                print('Your key is: ' + adminKey)
            else:
                if key == adminKey:
                    member = ctx.message.author
                    self.bot.admins.append(member.id)
                    storage.write_admins(self.bot.admins)
                    await self.bot.say('Added {0.mention} as an admin'.format(member))
                else:
                    print('Failed admin attempt on ' + time.strftime('%a %D at %H:%M:%S'))

        @perm.group(pass_context=True)
        async def mod(ctx, arg: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'listall':
                em = discord.Embed(title='───────────────────────', color=0xf4f142)  # yellow
                em.set_author(name='Mod List', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4d1.png')

                mod_users = [x for x in ctx.message.server.members if x.id in in_server.mods]
                for m in mod_users:
                    em.add_field(name=m.name, value=CHAR_ZWS, inline=False)

                await  self.bot.send_message(ctx.message.channel, embed=em)
                return

            id = extract_mention_id(arg)

            match = [x for x in ctx.message.mentions if x.id == id]

            if not match:
                return

            member = match[0]  # type: discord.Member

            if member.id not in in_server.mods:
                in_server.mods.append(member.id)
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Added {} to the mod list'.format(member.mention))
            else:
                await self.bot.say('{} is already a mod'.format(member.mention))

        @perm.command(pass_context=True)
        async def unmod(ctx, member: discord.Member):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            try:
                in_server.mods.remove(member.id)
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Removed {} from the mod list'.format(member.mention))
            except Exception:
                await self.bot.say('{} is not on the mod list'.format(member.mention))

        @perm.command(pass_context=True)
        async def check(ctx, arg: str, member: discord.Member):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'admin':
                if self.bot.check_admin(member):
                    await self.bot.say('{} is an admin'.format(member.mention))
                else:
                    await self.bot.say('{} is *not* an admin'.format(member.mention))
            elif arg == 'mod':
                if in_server.is_mod(member):
                    await self.bot.say('{} is a mod'.format(member.mention))
                else:
                    await self.bot.say('{} is *not* a mod'.format(member.mention))

        @perm.command(pass_context=True)
        async def rolemod(ctx, arg: str, role: discord.Role = None):
            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Rolemod usage:**\n'
                                                                '`{0}perm rolemod <add/remove> [@role]`\n'
                                                                '`{0}perm rolemod <check> [@role]`'
                                                                '`{0}perm rolemod <list>`'.format(
                    self.bot.command_prefix))
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'listall':
                em = discord.Embed(title='───────────────────────', color=0xf4b541)  # yellow
                em.set_author(name='RoleMod List', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4d1.png')

                mod_roles = [x for x in ctx.message.server.roles if x.id in in_server.rolemods]
                for rm in mod_roles:
                    em.add_field(name=rm.name, value=CHAR_ZWS, inline=False)

                await self.bot.send_message(ctx.message.channel, embed=em)
                return

            if role:
                if arg == 'add':
                    in_server.rolemods.append(role.id)
                    storage.write_server_data(self.bot, in_server)
                    await self.bot.say('Added role ' + role.mention + ' to role mod list')
                elif arg == 'remove':
                    if role.id in in_server.rolemods:
                        in_server.rolemods.remove(role.id)
                        storage.write_server_data(self.bot, in_server)
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
            if not self.bot.has_high_permissions(ctx.message.author):
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

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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
                    storage.write_bot(self.bot)  # Necessary to save command delay
                    await self.bot.say('Set anti-spam timer to ' + str(arg) + ' minutes')

                elif cmd == 'add' and arg:
                    in_server.spam_timers[arg] = 0
                    storage.write_server_data(self.bot, in_server)
                    await self.bot.say('Added {} to spam timer list'.format(arg))

                elif cmd == 'remove' and arg:
                    in_server.spam_timers.pop(arg, None)
                    storage.write_server_data(self.bot, in_server)
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

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Added {} to the list of blocked commands for all channels.'.format(arg2))
            elif arg == 'here' and arg2:
                in_server.block_list.append(BlockItem(name=arg2, channel=ctx.message.channel.id))
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Added {} to the list of blocked commands for {}.'.format(arg2,
                                                                                             ctx.message.channel.mention))
            elif channel_arg:
                in_server.block_list.append(BlockItem(name=arg2, channel=channel_arg.id))
                storage.write_server_data(self.bot, in_server)
                await self.bot.say('Added {} to the list of blocked commands for {}.'.format(arg2, channel_arg.mention))

            if not arg2:
                await self.bot.say('Please pass a name to block')

        @self.bot.command(pass_context=True)
        async def unblock(ctx, arg: str, arg2: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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
                        storage.write_server_data(self.bot, in_server)
                        await self.bot.say('Removed {} from block list for all channels.'.format(arg2))
                        return
                    elif arg == 'here' and cmd.channel == ctx.message.channel.id:
                        in_server.block_list.remove(cmd)
                        storage.write_server_data(self.bot, in_server)
                        await self.bot.say('Removed {} from block list for {}.'.format(arg2,
                                                                                       ctx.message.channel.mention))
                        return
                    elif channel_arg:
                        if cmd.channel == channel_arg.id:
                            in_server.block_list.remove(cmd)
                            storage.write_server_data(self.bot, in_server)
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
        async def clear(ctx, number: str = '99', channel: discord.Channel = None):
            if not self.bot.has_high_permissions(ctx.message.author):
                return

            if number == 'help':
                await self.bot.send_message(ctx.message.author, '**Clear usage**: `{0}clear [message number]`\n'
                                                                'Clears a number of bot messages'.format(
                    self.bot.command_prefix))
                return

            if not channel:
                channel = ctx.message.channel

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
            number += 1  # Delete whatever is required plus 'Deleting...'

            limit = min(number, 99)

            i = 0

            now = datetime.now()

            def user_check(msg):
                nonlocal limit, i

                message_age = (now - msg.timestamp).total_seconds()

                if message_age >= 1209600:
                    i = limit

                if i >= limit:
                    return False
                if msg.author == self.bot.user:
                    i += 1
                    return True
                return False

            async def bootleg_purge():
                async for x in self.bot.logs_from(channel, limit=99):
                    if user_check(x):
                        await self.bot.delete_message(x)

            if isinstance(channel, discord.PrivateChannel):
                await bootleg_purge()
            else:
                await self.bot.purge_from(ctx.message.channel, limit=100, check=user_check)

        @self.bot.command(pass_context=True)
        async def purge(ctx, arg: str, arg2: str = None):
            if not self.bot.has_high_permissions(ctx.message.author):
                return

            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Purge usage**:\n'
                                                                '`{0}purge [message number]`\n'
                                                                '`{0}purge [member] [message number:optional]`\n'
                                                                'Clears a number of messages. If `member` is not \n'
                                                                'passed, clearing is indiscriminate'.format(
                                                                    self.bot.command_prefix))
                return

            elif ctx.message.server:
                number = is_num(arg)
                if not number:
                    if not ctx.message.mentions:
                        m = await self.bot.say('Please pass a member or a number as first argument.')
                        schedule_delete(self.bot, m, 5)
                        return

                    member = ctx.message.mentions[0]

                    number = is_num(arg2)
                    if not number:
                        number = 10
                else:
                    member = None
            else:
                await self.bot.say('This command may only be called from a server.')
                return

            if number < 1:
                number = 1

            if number > 99:
                number = 99

            purged = 0

            def check(msg):
                nonlocal purged

                if purged >= number:
                    return False

                if msg.author == member:
                    purged += 1
                    return True
                else:
                    return False

            def count(msg):
                nonlocal purged
                purged += 1
                return True

            try:
                if member:
                    await self.bot.purge_from(ctx.message.channel, check=check)
                    await self.bot.say('Removed **{}** messages by {}'.format(purged, member.name))
                else:
                    await self.bot.purge_from(ctx.message.channel, limit=number, check=count)
                    await self.bot.say('Removed **{}** messages'.format(purged))
            except discord.Forbidden:
                await self.bot.say('I do not have permissions to do this.')
            except discord.HTTPException:
                await self.bot.say('Error in purge. Try again?')

        @self.bot.command(pass_context=True)
        async def info(ctx):
            e = discord.Embed(title="**Bot Info**",
                              description="{} is a bot operated by the **OllieBot Core** network, a platform "
                                          "developed by <@{}> and powered by "
                                          "[discord.py](https://github.com/Rapptz/discord.py), a Python API wrapper "
                                          "for Discord.\n\n"
                                          "Feel free to PM me (CantSayIHave#6969) for suggestions and bug reports.\n\n"
                                          "Webpage: www.olliebot.cc".format(self.bot.user.name, OWNER_ID),
                              color=0xff9000)
            await self.bot.send_message(ctx.message.author,
                                        embed=e)

        """
        @self.bot.command(pass_context=True)
        async def help(ctx):
            global help_args

            field_limit = 10
            high_perm = self.bot.has_high_permissions(ctx.message.author, b=self.bot)

            def get_page(page_num: int, args: list):
                limit = len(args) / field_limit
                if int(limit) != limit:
                    limit = int(limit + 1)

                limit = int(limit)

                if page_num < 1:
                    page_num = 1
                if page_num > limit:
                    page_num = limit

                l_start = int(field_limit * (page_num - 1))
                if len(args) > (l_start + field_limit):
                    page_list = args[l_start:l_start + field_limit]
                else:
                    page_list = args[l_start:len(args)]

                em = discord.Embed(title='───────────────────────', color=0xff0000)
                em.set_author(name='Command Help - Page {}/{}'.format(int(page_num), int(limit)),
                              icon_url='https://abs.twimg.com/emoji/v2/72x72/2753.png')

                for arg in page_list:  # type: str
                    em.add_field(name=arg,
                                 value=help_args[arg]['d'].capitalize(),
                                 inline=False)

                return em

            sorted_args = sorted(help_args)

            for arg in sorted_args[:]:
                if not high_perm:
                    if help_args[arg]['m']:
                        sorted_args.remove(arg)

            current_page = 1

            em = get_page(current_page, sorted_args)

            base_message = await self.bot.send_message(ctx.message.author, embed=em)
            await self.bot.add_reaction(base_message, '⏮')
            await self.bot.add_reaction(base_message, '⏪')
            await self.bot.add_reaction(base_message, '⏩')
            await self.bot.add_reaction(base_message, '⏭')
            await self.bot.add_reaction(base_message, '❌')
            await self.bot.add_reaction(base_message, 'ℹ')
            await self.bot.wait_for_reaction('ℹ', message=base_message)
            while True:
                reaction, user = await self.bot.wait_for_reaction(['⏮', '⏪', '⏩', '⏭', '❌', 'ℹ'],
                                                                  message=base_message,
                                                                  timeout=120)

                if not reaction:
                    break

                limit = len(sorted_args) / field_limit
                if int(limit) != limit:
                    limit = int(limit + 1)

                recent_page = current_page

                choice = str(reaction.emoji)
                if choice == '⏮':
                    current_page = 1
                elif choice == '⏪':
                    current_page -= 1
                    if current_page < 1:
                        current_page = 1
                elif choice == '⏩':
                    current_page += 1
                    if current_page > limit:
                        current_page = limit
                elif choice == '⏭':
                    current_page = limit
                elif choice == '❌':
                    await self.bot.delete_message(base_message)
                    break

                if current_page != recent_page:
                    em = get_page(current_page, sorted_args)
                    base_message = await self.bot.edit_message(base_message, embed=em)

                if choice == 'ℹ':
                    em = discord.Embed(title='───────────────────────', color=0xff0000)
                    em.set_author(name='Command Help - Info',
                                  icon_url='https://abs.twimg.com/emoji/v2/72x72/2139.png')

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

                    await self.bot.edit_message(base_message, embed=em)"""

        @self.bot.group(pass_context=True)
        async def emotes(ctx):
            pass

        @emotes.command(pass_context=True)
        async def suggest(ctx, link: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

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

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if link is not None and link != '-r':
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

                                    if link == '-r':
                                        self.replace_color(image, 0x36393E, 5)

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
                        await self.bot.say(
                            'No image detected in message. Please upload image as part of command message')

        @emotes.command(pass_context=True)
        async def listall(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            in_server.suggest_emotes.clear()
            await self.bot.say('Emote suggestions cleared')

        @emotes.command(pass_context=True)
        async def steal(ctx, arg: str, new_name: str = None, location: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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

            add_server = ctx.message.server

            if location == 'mine':
                add_server = discord.Server(id='338507735358242816', name='Bot Test')

            with aiohttp.ClientSession() as session:
                async with session.get(add_url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()

                        await self.bot.create_custom_emoji(add_server, name=new_name,
                                                           image=image_bytes)
                        await self.bot.say('Stole `:{}:` for the server!'.format(new_name))

        @emotes.command(pass_context=True)
        async def help(ctx):
            out_str = "**Emotes usage:**\n"
            if self.bot.has_high_permissions(ctx.message.author):
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
        async def roles(ctx):
            pass

        @roles.command(pass_context=True)
        async def add(ctx, base_role: discord.Role, add_role: discord.Role, no_role: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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

        @roles.command(pass_context=True)
        async def remove(ctx, base_role: discord.Role, rem_role: discord.Role, no_role: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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
                    'Remove failed. Bot does not have sufficient permissions to remove {} from {}'.format(
                        rem_role.mention,
                        base_role.mention))
            except discord.HTTPException:
                await self.bot.say('Remove failed, role could not be removed for some reason ¯\_(ツ)_/¯')

        @roles.command(pass_context=True)
        async def replace(ctx, base_role: discord.Role, rep_role: discord.Role):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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

        @roles.command(pass_context=True)
        async def create(ctx, name: str, color: str = '0xffffff'):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            try:
                color = int(color, 16)
            except Exception:
                color = 0xffffff

            try:
                r = await self.bot.create_role(server=ctx.message.server, name=name,
                                               color=discord.Color(color),
                                               mentionable=True)
                await self.bot.say('Created role {}!'.format(r.mention))
            except discord.Forbidden:
                await self.bot.say("I don't have permission to do this.")
            except discord.HTTPException:
                await self.bot.say("Error in creating role :(")

        @roles.command(pass_context=True)
        async def edit(ctx, name: str, *, options: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            role = [x for x in ctx.message.server.roles if x.name == name]

            if not role:
                await self.bot.say('Role `{}` does not exist'.format(name))
                return

            options_d = {}

            for o in shlex.split(options, comments=False, posix=' '):
                if o:
                    parts = o.split('=')
                    options_d[parts[0].lower()] = parts[1]

            if 'color' in options_d:
                options_d['color'] = options_d['color'].replace('#', '0x')
                try:
                    color = int(options_d['color'], 16)
                except Exception:
                    color = 0xffffff
                options_d['color'] = discord.Color(color)

            try:
                r = await self.bot.edit_role(server=ctx.message.server, role=role[0], **options_d)
                await self.bot.say('Updated role `{}`'.format(name))
            except discord.Forbidden:
                await self.bot.say('I do not have permissions for this.')
            except Exception:
                await self.bot.say('Error in formatting')


        @roles.command(pass_context=True)
        async def help(ctx):
            await self.bot.send_message(ctx.message.author,
                                        '**Roles usage:**\n'
                                        '`{0}roles <add/remove> [base role] [new role] [optional:"NoRole"]`\n'
                                        '`{0}roles <replace> [old role] [new role]`\n'
                                        '`{0}roles <create> [name] [color]`\n'
                                        'The roles command automates mass addition, removal and replacement of roles, '
                                        'as well as creation for custom colors.'
                                        'Example:\n'
                                        '`{0}roles add @SomeRole @OtherRole` will add `@OtherRole` to all users with '
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

            if not is_num(arg):
                return

            try:
                msg = None
                if arg2:
                    msg = await self.bot.get_message(self.bot.get_channel(arg), arg2)
                else:
                    m_count = int(arg)
                    if m_count <= 30:
                        i = 0
                        async for m in self.bot.logs_from(ctx.message.channel, limit=30):
                            if i >= m_count:
                                msg = m
                                break
                            i += 1
                    else:
                        msg = await self.bot.get_message(ctx.message.channel, arg)

                if not msg:
                    await self.bot.say('Message not found.')
                    return

                await self.bot.say('```\n{}\n```'.format(msg.content))
            except discord.Forbidden:
                await self.bot.say("I don't have permission for that")

        @self.bot.command(pass_context=True)
        async def nick_all(ctx, new_name: str):
            if not ctx.message.server:
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
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
                await self.bot.say(
                    'Operation complete. Failed to change: {}'.format(', '.join([x.name for x in failures])))

        @self.bot.command(pass_context=True)
        async def mute(ctx, member: discord.Member, minutes: int = None):
            if not ctx.message.server:
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            timeout_role = None
            try:
                timeout_role = [x for x in ctx.message.server.roles if x.name.lower() == 'timeout'][0]
            except Exception:
                pass

            try:
                await self.bot.server_voice_state(member=member, mute=True)
                schedule_future(coro=self.bot.server_voice_state(member=member, mute=False),
                                time=(minutes * 60))
                await self.bot.say('Voice Muted {}'.format(member.name))
            except discord.Forbidden:
                await self.bot.say('I do not have sufficient permissions to do this.')
            except discord.HTTPException:
                await self.bot.say('An error occurred while attempting. Please try again.')

            if timeout_role:
                try:
                    await self.bot.add_roles(member, timeout_role)
                    schedule_future(coro=self.bot.remove_roles(member, timeout_role),
                                    time=(minutes * 60))
                    await self.bot.say('Text Muted {}'.format(member.name))
                except discord.Forbidden:
                    await self.bot.say('I do not have sufficient permissions to do this.')
                except discord.HTTPException:
                    await self.bot.say('An error occurred while attempting. Please try again.')
            else:
                await self.bot.say('There is no `Timeout` role to assign. Please create one to mute text features.')

        @self.bot.command(pass_context=True)
        async def leavechannel(ctx, arg: str, channel: discord.Channel = None):
            if not ctx.message.server:
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if arg == 'off':
                in_server.leave_channel = None
            elif arg == 'set' and channel:
                in_server.leave_channel = channel.id

            storage.write_server_data(self.bot, in_server)

            out = await self.bot.say('✅')
            schedule_delete(self.bot, out, 5)

        # @perm(type_=permissions.MOD, bot=self.bot)
        @self.bot.command(pass_context=True)
        async def echo(ctx, *, arg: str):
            await self.bot.say(arg)


    @staticmethod
    def replace_color(img: Image.Image, color: int, variance: int):
        alpha = (color & 0xff000000) >> 24
        red = (color & 0xff0000) >> 16
        green = (color & 0xff00) >> 8
        blue = color & 0xff

        pixels = img.load()

        for y in range(img.size[1]):
            for x in range(img.size[0]):
                at = pixels[x, y]
                test_color = alpha | (at[0] << 16) | (at[1] << 8) | at[2]

                if abs(color - test_color) <= variance:
                    pixels[x, y] = (red, green, blue, alpha)


def setup(bot):
    return ServerUtils(bot)
