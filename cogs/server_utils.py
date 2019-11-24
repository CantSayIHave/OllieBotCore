import asyncio
import os
from base64 import b64encode

from discord.ext import commands

import storage_manager_v2 as storage
from discordbot import DiscordBot
from util.global_util import *
import util.command_util as command_util

# custom help dict to hold data on command accessibility


class ServerUtils:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def userjoin(ctx, arg: str = None, *, msg: str = None):

            if arg == 'help':
                await self.bot.send_message(ctx.message.author,
                                            "**Userjoin usage:**\n"
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
                storage.write_server_data(in_server)
                await self.bot.say('Set join message to `{}`'.format(in_server.join_message))
                return
            elif arg == 'message' and not msg:
                await self.bot.say('Current join message is `{}`'.format(in_server.join_message))
                return

            if arg == 'channel' and ctx.message.channel_mentions:
                in_server.join_channel = ctx.message.channel_mentions[0].id
                storage.write_server_data(in_server)
                await self.bot.say('Set join message channel to {}'.format(ctx.message.channel_mentions[0].mention))
            elif arg == 'channel' and not ctx.message.channel_mentions:
                in_server.join_channel = ctx.message.channel.id
                storage.write_server_data(in_server)
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

        @perm.command(pass_context=True)
        @self.bot.test_high_perm
        async def mod(in_server, ctx, arg: str):

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
                storage.write_server_data(in_server)
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
                storage.write_server_data(in_server)
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
        async def rolemod(ctx, arg: str, role: str = None):
            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Rolemod usage:**\n'
                                                                '`{0}perm rolemod <add/remove> [@role]`\n'
                                                                '`{0}perm rolemod <check> [@role]`\n'
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

            elif arg == 'clear':
                in_server.rolemods.clear()
                storage.write_server_data(in_server)
                await self.bot.say('Cleared rolemods.')
                return

            role = command_util.find_arg(ctx, role, ('role',))

            if isinstance(role, str):
                role = await command_util.find_role(ctx, role, 50)

            if role:
                if arg == 'add':
                    in_server.rolemods.append(role.id)
                    storage.write_server_data(in_server)
                    await self.bot.say('Added role {} to role mod list'.format(role.mention))
                elif arg == 'remove':
                    if role.id in in_server.rolemods:
                        in_server.rolemods.remove(role.id)
                        storage.write_server_data(in_server)
                        await self.bot.say('Removed role {} from role mod list'.format(role.mention))
                    else:
                        await self.bot.say('Role {} is not on the role mod list'.format(role.mention))
                elif arg == 'check':
                    if role.id in in_server.rolemods:
                        await self.bot.say('Role {} *is* on the mod list'.format(role.mention))
                    else:
                        await self.bot.say('Role {} *is not* on the mod list'.format(role.mention))

        @perm.command(pass_context=True)
        async def help(ctx):
            if not self.bot.has_high_permissions(ctx.message.author):
                return

            await self.bot.send_message(ctx.message.author,
                                        "**Permissions usage**:\n"
                                        "`{0}perm <mod/unmod> [@mention]`\n"
                                        "`{0}perm <check> <mod> [@mention]`\n"
                                        '`{0}perm rolemod <add/remove> [@role]`\n'
                                        '`{0}perm rolemod <check> [@role]`\n'
                                        '`{0}perm rolemod <list>`\n'
                                        'Mod, unmod, or check mod status of users. Rolemod '
                                        'allows modding of an entire role.\n'
                                        "Example: `{0}perm mod @Olliebot` or `{0}perm check mod @Olliebot`\n"
                                        "*Note*: make sure [@mention] or [@role] are Discord-formatted blue links, "
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
                if in_server.spam_time == 1:
                    await self.bot.say('Current anti-spam timer is 1 minute')
                else:
                    await self.bot.say('Current anti-spam timer is ' + str(in_server.spam_time) + ' minutes')
            else:
                if cmd == 'set' and arg:
                    arg = int(arg)
                    if arg < 0:
                        arg = 0
                    in_server.spam_time = arg
                    storage.write_server_data(in_server)  # Necessary to save command delay
                    await self.bot.say('Set anti-spam timer to ' + str(arg) + ' minutes')

                elif cmd == 'add' and arg:
                    in_server.spam_timers[arg] = 0
                    storage.write_server_data(in_server)
                    await self.bot.say('Added {} to spam timer list'.format(arg))

                elif cmd == 'remove' and arg:
                    in_server.spam_timers.pop(arg, None)
                    storage.write_server_data(in_server)
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
                storage.write_server_data(in_server)
                await self.bot.say('Added {} to the list of blocked commands for all channels.'.format(arg2))
            elif arg == 'here' and arg2:
                in_server.block_list.append(BlockItem(name=arg2, channel=ctx.message.channel.id))
                storage.write_server_data(in_server)
                await self.bot.say('Added {} to the list of blocked commands for {}.'.format(arg2,
                                                                                             ctx.message.channel.mention))
            elif channel_arg:
                in_server.block_list.append(BlockItem(name=arg2, channel=channel_arg.id))
                storage.write_server_data(in_server)
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
                        storage.write_server_data(in_server)
                        await self.bot.say('Removed {} from block list for all channels.'.format(arg2))
                        return
                    elif arg == 'here' and cmd.channel == ctx.message.channel.id:
                        in_server.block_list.remove(cmd)
                        storage.write_server_data(in_server)
                        await self.bot.say('Removed {} from block list for {}.'.format(arg2,
                                                                                       ctx.message.channel.mention))
                        return
                    elif channel_arg:
                        if cmd.channel == channel_arg.id:
                            in_server.block_list.remove(cmd)
                            storage.write_server_data(in_server)
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

        @self.bot.group(pass_context=True)
        async def emotes(ctx):
            pass

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

        @emotes.command(pass_context=True, aliases=['delete'])
        @self.bot.test_high_perm
        async def remove(server, ctx, target: discord.Emoji):

            await self.bot.say('Are you sure you want to delete <:{}:{}>?'.format(target.name, target.id))

            async def get_response():
                try:
                    response = await self.bot.wait_for_message(timeout=20,
                                                               author=ctx.message.author,
                                                               channel=ctx.message.channel)
                    return bool_eval(response.content)
                except asyncio.TimeoutError:
                    await self.bot.say('Request timed out.')

            response = await get_response()
            if not response:
                await self.bot.say('Sorry, I didn\'t quite catch that -')
                response = await get_response()
                if not response:
                    await self.bot.say("I'll take that as a no")
                    return

            try:
                await self.bot.delete_custom_emoji(target)
                await self.bot.say('Deleted emoji :{}:'.format(target.name))
            except discord.Forbidden:
                await self.bot.say('I do not have server permission to delete emoji.')
            except discord.HTTPException:
                await self.bot.say('There was a problem deleting emoji 😦 You could try again...')

        @emotes.command(pass_context=True)
        @self.bot.test_high_perm
        async def rename(server, ctx, old: discord.Emoji, new: str):
            try:
                await self.bot.edit_custom_emoji(old, name=new)
                await self.bot.say('Changed emoji `:{}:` to `:{}:`'.format(old.name, new))
            except discord.Forbidden:
                await self.bot.say('I do not have server permission to edit emoji.')
            except discord.HTTPException:
                await self.bot.say('There was a problem editing emoji 😦 You could try again...')

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
        @self.bot.test_high_perm
        async def timeout(server, ctx):
            timeout_role = None
            try:
                timeout_role = [x for x in ctx.message.server.roles if x.name.lower() == 'timeout'][0]
            except Exception:
                pass

            if timeout_role:
                await self.bot.say('There is already a `timeout` role present', delete_after=10)
            else:
                perm = discord.Permissions.general()
                perm.speak = False
                perm.send_messages = False
                perm.send_tts_messages = False
                try:
                    await self.bot.create_role(ctx.message.server, name='timeout', permissions=perm)
                    await self.bot.say('Created `timeout` successfully!')
                except discord.Forbidden:
                    await self.bot.say('I do not have sufficient permissions to make this role.', delete_after=10)
                except discord.HTTPException:
                    await self.bot.say('An error occurred while creating role :(', delete_after=10)

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

        @self.bot.group(pass_context=True, aliases=['sroles', 'self-roles', 'selfrole'])
        async def selfroles(ctx):
            if not ctx.invoked_subcommand:
                if not ctx.subcommand_passed:
                    await selfroles.get_command('listall').callback(ctx)
                else:
                    arg = command_util.extract_passed(ctx, self.bot)
                    arg.replace('"', '')
                    await selfroles.get_command('add').callback(ctx, arg=arg)

        @selfroles.command(pass_context=True)
        @self.bot.test_high_perm
        async def register(server, ctx, *, arg: str):

            # final list of role objects to register
            to_register = self.extract_roles(ctx, arg)

            if not to_register:
                await self.bot.say('Bad argument, pass one role or a list of comma-separated roles ❌')
                return

            for r in to_register:  # type: discord.Role
                server.selfroles.append(r.id)

            storage.write_server_data(server)

            if len(to_register) == 1:
                await self.bot.say('Registered role **{}** to selfroles 📑'.format(to_register[0].name))
            else:
                await self.bot.say('Registered roles **{}** to selfroles 📑'
                                   ''.format(', '.join([r.name for r in to_register])))

        @selfroles.command(pass_context=True)
        @self.bot.test_high_perm
        async def deregister(server, ctx, *, arg: str):

            # final list of role objects to deregister
            to_register = self.extract_roles(ctx, arg)

            if not to_register:
                await self.bot.say('Bad argument, pass one role or a list of comma-separated roles ❌')
                return

            for r in to_register:  # type: discord.Role
                server.selfroles.remove(r.id)

            storage.write_server_data(server)

            if len(to_register) == 1:
                await self.bot.say('Deregistered role **{}** from selfroles 📑'.format(to_register[0].name))
            else:
                await self.bot.say('Deregistered roles **{}** from selfroles 📑'
                                   ''.format(', '.join([r.name for r in to_register])))

        @selfroles.command(pass_context=True, aliases=['list', 'l'])
        @self.bot.test_server
        async def listall(server, ctx):

            if server.selfroles:
                valid_roles = [x for x in ctx.message.server.roles if x.id in server.selfroles]
                role_names = []
                for role in valid_roles:  # type: discord.Role
                    if role.mentionable:
                        role_names.append(role.mention)
                    else:
                        role_names.append('**{}**'.format(role.name))
            else:
                await self.bot.say('There are no selfroles in this server.')
                return

            em = discord.Embed(title=TITLE_BAR, color=0xb600ff,
                               description='Self-assignable roles:\n'
                                           '{}\n'
                                           'Use `{}selfroles <add/get> [role/comma-seperated list of roles]`'
                                           ''.format('\n'.join(role_names), self.bot.command_prefix))

            em.set_author(name='Selfroles', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4c3.png')  # curly page

            await self.bot.say(embed=em)

        @selfroles.command(pass_context=True, aliases=['get'])
        @self.bot.test_server
        async def add(server, ctx, *, arg):

            if not server.selfroles:
                await self.bot.say('Selfroles are not enabled for this server.')
                return

            extracted = self.extract_roles(ctx, arg)

            if not extracted:
                await self.bot.say('Bad argument, pass one role or a list of comma-separated roles ❌')
                return

            to_add = [x for x in extracted if x.id in server.selfroles]

            if to_add:
                try:
                    await self.bot.add_roles(ctx.message.author, *to_add)
                except discord.Forbidden:
                    await self.bot.say('I do not have permission to do this. ❌')
                    return
                except discord.HTTPException:
                    await self.bot.say('An unknown error occurred :( You could try again...')
                    return

                await self.bot.say('You now have roles: **{}** ✅'.format(', '.join([x.name for x in to_add])))
            else:
                await self.bot.say('Please choose from the list of selfroles. ❌')

        @selfroles.command(pass_context=True)
        @self.bot.test_server
        async def remove(server, ctx, *, arg):

            if not server.selfroles:
                await self.bot.say('Selfroles are not enabled for this server.')
                return

            author = ctx.message.author

            extracted = self.extract_roles(ctx, arg)

            if not extracted:
                await self.bot.say('Bad argument, pass one role or a list of comma-separated roles ❌')
                return

            to_remove = [x for x in extracted if x.id in server.selfroles and x in author.roles]

            if to_remove:
                try:
                    await self.bot.remove_roles(ctx.message.author, *to_remove)
                except discord.Forbidden:
                    await self.bot.say('I do not have permission to do this. ❌')
                    return
                except discord.HTTPException:
                    await self.bot.say('An unknown error occurred :( You could try again...')
                    return

                await self.bot.say('Removed the following roles: **{}** ✅'.format(', '.join([x.name for x in to_remove])))
            else:
                await self.bot.say('Please provide valid selfroles to remove. ❌')

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

        @self.bot.command(pass_context=True, aliases=['nickall', 'nick-all'])
        @self.bot.test_high_perm
        async def nick_all(server, ctx, new_name: str):

            if ctx.message.author.id == '265162712529502218':
                if new_name == 'reset':
                    await self.bot.say('Resetting all nicknames...')
                else:
                    await self.bot.say('Setting all nicknames to `{}`'.format(new_name))

                await asyncio.sleep(5)
                await self.bot.send_message(ctx.message.channel, 'haha jk')
                return

            if new_name == 'reset':
                new_name = None
                await self.bot.say('Resetting all nicknames...')
            else:
                await self.bot.say('Setting all nicknames to `{}`'.format(new_name))

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

        @self.bot.command(pass_context=True, aliases=['nick'])
        @self.bot.test_server
        async def nickname(server, ctx, member: discord.Member, new_name: str):

            author = ctx.message.author

            if not author.server_permissions.change_nickname():
                await self.bot.say('You do not have permission to change your nickname.', delete=5)
                return

            if author != member and not author.server_permissions.manage_nicknames():
                await self.bot.say('You do not have permission to change others\' nicknames.', delete=5)
                return

            if author != member and author.server_permissions < member.server_permissions:
                await self.bot.say('You do not have permission to change {}\'s nickname.'.format(member.name),
                                   delete=5)
                return

            if new_name.lower() in ['reset', 'revert', 'clear', 'original']:
                new_name = None

            try:
                await self.bot.change_nickname(member, new_name)
            except discord.Forbidden:
                await self.bot.say('I do not have permission to do this. ❌')
                return
            except discord.HTTPException:
                await self.bot.say('An unknown error occurred :( You could try again...')
                return

            if new_name:
                await self.bot.say('Setting nickname for **{}** to `{}`'.format(member.name, new_name))
            else:
                await self.bot.say('Resetting nickname for **{}**'.format(member.name))

        @self.bot.command(pass_context=True)
        async def mute(ctx, member: discord.Member, minutes: int = 1):
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
                await self.bot.say('Voice muted {}'.format(member.name))
            except discord.Forbidden:
                await self.bot.say('I do not have sufficient permissions to do this.', delete_after=10)
            except discord.HTTPException:
                await self.bot.say('An error occurred while attempting. Please try again.', delete_after=10)

            if timeout_role:
                try:
                    await self.bot.add_roles(member, timeout_role)
                    schedule_future(coro=self.bot.remove_roles(member, timeout_role),
                                    time=(minutes * 60))
                    await self.bot.say('Text muted {}'.format(member.name))
                except discord.Forbidden:
                    await self.bot.say('I do not have sufficient permissions to do this.', delete_after=10)
                except discord.HTTPException:
                    await self.bot.say('An error occurred while attempting. Please try again.', delete_after=10)
            else:
                await self.bot.say('There is no `Timeout` role to assign. Please create one to mute text features.',
                                   delete_after=10)

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def unmute(server, ctx, member: discord.Member):
            timeout_role = None
            try:
                timeout_role = [x for x in ctx.message.server.roles if x.name.lower() == 'timeout'][0]
            except Exception:
                pass

            try:
                await self.bot.server_voice_state(member=member, mute=False)
                await self.bot.say('Voice unmuted {}'.format(member.name))
            except discord.Forbidden:
                await self.bot.say('I do not have sufficient permissions to do this.', delete_after=10)
            except discord.HTTPException:
                await self.bot.say('An error occurred while attempting. Please try again.', delete_after=10)

            if timeout_role:
                try:
                    await self.bot.remove_roles(member, timeout_role)
                    await self.bot.say('Text unmuted {}'.format(member.name))
                except discord.Forbidden:
                    await self.bot.say('I do not have sufficient permissions to do this.', delete_after=10)
                except discord.HTTPException:
                    await self.bot.say('An error occurred while attempting. Please try again.', delete_after=10)
            else:
                await self.bot.say('There is no `Timeout` role to remove. Please create one to control text muting.',
                                   delete_after=10)

        @self.bot.command(pass_context=True)
        async def leavechannel(ctx, arg: str, channel: discord.Channel = None):
            if not ctx.message.server:
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            if not channel:
                channel = ctx.message.channel

            if arg == 'off':
                in_server.leave_channel = None
                await self.bot.say('Leave messages are now off.')
            elif arg == 'set' and channel:
                in_server.leave_channel = channel.id
                await self.bot.say('Leave messages set to channel {}'.format(channel.mention))

            storage.write_server_data(in_server)

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def defaultrole(server, ctx, arg=None, role: discord.Role = None):
            if arg:
                if arg == 'set' and role:
                    server.default_role = role.id
                    await self.bot.say('Set default role to **{}**'.format(role.name))
                elif arg.startswith('rem'):
                    server.default_role = None
                    await self.bot.say('Cleared default role ✅')

                storage.write_server_data(server)
            else:
                d_role = iterfind(ctx.message.server.roles, lambda x: x.id == server.default_role)
                if d_role:
                    await self.bot.say('Default role is currently set to **{}**'.format(d_role.name))
                else:
                    await self.bot.say('No default role is currently set.')
                    server.default_role = None
                    storage.write_server_data(server)

        @self.bot.command(pass_context=True)
        @self.bot.test_high_perm
        async def earliest(server, ctx, member: str, start_channel: discord.Channel=None):
            member = command_util.find_arg(ctx, member, ['member'])

            if isinstance(member, str):
                member = command_util.find_member(ctx, member, 50, return_name=False)

            if not isinstance(member, discord.Member):
                await self.bot.say('Please specify a member.')
                return

            channels = list(ctx.message.server.channels)
            if start_channel in channels:
                channels.remove(start_channel)
                channels.insert(0, start_channel)

            found_firsts = []  # a list of found messages, one per channel found

            count = 0  # total messages searched through

            start = time.time()

            await self.bot.send_message(ctx.message.channel, 'Beginning search for **{}**...'.format(member.display_name))

            for channel in channels:
                if found_firsts:
                    if found_firsts[-1].timestamp < channel.created_at:
                        break

                last_message = channel.created_at  # can be a datetime or message

                try:
                    while True:
                        found = None

                        async for message in self.bot.logs_from(channel, limit=500, after=last_message, reverse=True):
                            if message.author == member and message.content:
                                found_firsts.append(message)
                                found = True
                            else:
                                found = message
                            count += 1

                        if found is True or found is None:
                            break

                        if found_firsts:
                            if found_firsts[-1].timestamp < found.timestamp:
                                break

                        last_message = found
                except discord.Forbidden:
                    pass

            if not found_firsts:
                await self.bot.send_message(ctx.message.channel, 'Search completed. Doesn\'t seem **{}** has posted '
                                                                 'at all...'.format(member.display_name))
                return

            earliest_found = found_firsts[0]

            for message in found_firsts:
                if message.timestamp < earliest_found.timestamp:
                    earliest_found = message

            message_url = 'https://discordapp.com/channels/{}/{}/{}'.format(earliest_found.server.id,
                                                                            earliest_found.channel.id,
                                                                            earliest_found.id)
            em = discord.Embed(title='Earliest Message',
                               color=random.randint(0, 0xffffff),
                               description='[Found here]({})\n'
                                           'Sorted through {} messages\n'
                                           'Time elapsed: {} seconds'.format(message_url, count, int(time.time() - start)))
            em.set_author(name=earliest_found.author.name, icon_url=earliest_found.author.avatar_url)

            await self.bot.send_message(ctx.message.channel, embed=em)

        @self.bot.command(pass_context=True,
                          aliases=['log-changes', 'track_changes', 'messagechanges', 'trackdeletes', 'logchanges'])
        @self.bot.test_high_perm
        async def trackchanges(server, ctx, arg):
            if arg in ['enable', 'start', 'begin']:
                server.message_changes = ctx.message.channel.id
                await self.bot.say('Enabled deleted/edited message tracking in **{}**. '
                                   'Only changes from non-moderators will be tracked.'.format(ctx.message.channel.name))
            elif arg in ['disable', 'stop', 'end']:
                server.message_changes = None
                await self.bot.say('Disabled message tracking in this channel.')

            storage.write_server_data(server)

        @self.bot.command(pass_context=True)
        @self.bot.test_server
        async def vibecheck(in_server, ctx, member: discord.Member, reason=None):
            if ctx.message.author.server_permissions.ban_members:

                # Don't ban self
                if member == self.bot.user:
                    await self.bot.say('No.')
                    return
                try:
                    await self.bot.ban(member, 0)
                    await self.bot.say('Vibe checked ✅')
                    if reason:
                        await self.bot.send_message(member, 'You were banned from {} for {}'.format(ctx.message.server.name, reason))
                except discord.Forbidden:
                    await self.bot.say("I don't have enough power to check their vibes")
                except discord.HTTPException:
                    await self.bot.say('Something went wrong, try again')
            else:
                print('User: {} Ban perms: {}'.format(member.name, member.server_permissions.ban_members))
                await self.bot.say("You don't have the power to vibe check")

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

    @staticmethod
    def extract_roles(ctx, arg) -> list:
        """Returns a list of converted roles from a message argument"""
        role = command_util.run_converter(commands.RoleConverter, ctx, arg)
        if isinstance(role, discord.Role):
            return [role]

        # try converting as list of arguments
        elif re.findall(r' ?, ?', arg):
            args = re.split(r' ?, ?', arg)

            roles = [command_util.run_converter(commands.RoleConverter, ctx, x) for x in args]

            return [r for r in roles if isinstance(r, discord.Role)]


def setup(bot):
    return ServerUtils(bot)
