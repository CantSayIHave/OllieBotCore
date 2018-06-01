import asyncio

import storage_manager as storage
from cogs.server_utils import help_args
from discordbot import DiscordBot
from server import Server
from util import global_util
from util.global_util import *


class Admin:
    def __init__(self, bot: DiscordBot):
        self.bot = bot
        self.help_args = help_args

        @self.bot.command(pass_context=True)
        async def repl(ctx, user: discord.Member = None):

            if not self.bot.check_admin(ctx.message.author):
                return

            def prints(anything):
                self.print_log += str(anything) + '\n'

            def gen(obj):
                stuff = yield from obj
                return stuff

            await self.bot.say('Entering REPL for {}.'.format(ctx.message.author.name))
            while True:
                self.print_log = ""
                await self.bot.say('>>> ')
                try:
                    response = await self.bot.wait_for_message(author=ctx.message.author, timeout=10.0 * 60.0)
                except asyncio.TimeoutError:
                    await self.bot.say('Exiting REPL.')
                    break

                line = self.extract_code(response.content)

                if 'prints' not in line:
                    line = line.replace('print', 'prints')

                if ('exit' in line) or ('quit' in line):
                    await self.bot.say('Exiting REPL.')
                    break
                if ('exec' in line) or ('eval' in line):
                    if not self.bot.check_admin(ctx.message.author):
                        await self.bot.say('`exec` and `eval` are not allowed.')
                        continue
                if 'global' in line:
                    await self.bot.say('Global references are not allowed.')
                    continue

                try:
                    ret_print = eval(line)
                    if ret_print:
                        prints(ret_print)
                except Exception:
                    try:
                        ret_print = exec(line)
                        if ret_print:
                            prints(ret_print)
                    except Exception as e:
                        prints(e)
                if self.print_log:
                    await self.bot.say('```\n{}\n```'.format(self.print_log))

        @self.bot.command(pass_context=True)
        async def send(ctx, channel_id: str, *, msg_out: str):
            if not self.bot.check_admin(ctx.message.author):
                return

            await self.bot.send_message(discord.Object(id=channel_id), msg_out)
            out = await self.bot.say('✅')
            schedule_delete(self.bot, out, 5)

        @self.bot.command(pass_context=True)
        async def write(ctx):
            if not self.bot.check_admin(ctx.message.author):
                return
            for b in self.bot.bot_list:
                storage.write_bot(b)
            await self.bot.say('All bots serialized to json.')

        @self.bot.command(pass_context=True)
        async def invite(ctx):
            if not self.bot.check_admin(ctx.message.author):
                return

            await self.bot.say('My invite link is '
                               'https://discordapp.com/oauth2/authorize?'
                               '&client_id={}&scope=bot'.format(self.bot.user.id))

        @self.bot.command(pass_context=True)
        async def prefix(ctx, arg: str = None, *, symbol: str = None):
            if not self.bot.check_admin(ctx.message.author):
                return

            if arg is None:
                if self.bot.command_prefix == "":
                    await self.bot.say('Bot has no current prefix set. Set one with `prefix set [prefix]`')
                else:
                    await self.bot.say('Current bot prefix is `{0}`'.format(self.bot.command_prefix))
                return

            if arg == 'help':
                await self.bot.send_message(ctx.message.author, '**Prefix usage:**\n'
                                                                'Get current command prefix: `{0}prefix`\n'
                                                                'Set command prefix: `{0}prefix <set> [prefix]`'.format(
                    self.bot.command_prefix))
                return

            if arg == 'set' and symbol is not None:
                self.bot.command_prefix = symbol
                self.prefix = symbol
                storage.write_bot_data(self.bot)
                await self.bot.say('Set bot prefix to `{0}`'.format(symbol))

        @self.bot.group(pass_context=True)
        async def server(ctx):
            pass

        @server.command(pass_context=True)
        async def add(ctx, bot_name: str, invite: str, q_delay: int):

            if not self.bot.check_admin(ctx.message.author):
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_bot = None
            if bot_name == 'this':
                in_bot = self.bot
            else:
                bot_exists = False  # ensure requested bot actually exists
                for b in self.bot.bot_list:
                    if b.user.name == bot_name:
                        in_bot = b
                        bot_exists = True
                if not bot_exists:
                    await self.bot.say('Requested bot does not exist')
                    return

            if invite == 'this':
                in_server = ctx.message.server
            else:
                in_server = discord.Client.get_invite(invite)

            for se in in_bot.local_servers:
                if se.name == in_server.server.name:
                    await self.bot.say('Server {} is already added to bot {}'.format(in_server.server.name,
                                                                                     in_bot.user.name))
                    return

            if in_server:
                s_name = in_server.name
                s_mods = []
                s_commands = []
                s_rss = []
                s_id = in_server.id
                if q_delay < 1:
                    q_delay = 1
                s_mods.append(in_server.owner.id)
                in_bot.local_servers.append(Server(name=s_name,
                                             mods=s_mods,
                                             commands=s_commands,
                                             rss=s_rss,
                                             command_delay=q_delay,
                                             id=s_id))
                storage.write_bot(in_bot)
                await self.bot.say('Server ' + s_name + ' added to bot ' + in_bot.user.name + '!')

        @server.command(pass_context=True)
        async def rename(ctx, to_name: str, new_name: str):

            if not self.bot.check_admin(ctx.message.author):
                return

            if to_name == new_name:
                await self.bot.say("You can't rename a server to its own name (╯°□°）╯︵ ┻━┻")
                return

            server_target = self.bot.get_server(name=to_name)

            if server_target is None:
                await self.bot.say('Server {} does not exist'.format(to_name))
                return

            # if renaming an old server to a new, delete new version
            new_wrong_server = self.bot.get_server(name=new_name)
            if new_wrong_server:
                self.bot.local_servers.remove(new_wrong_server)

            server_target.name = new_name

        @server.command(pass_context=True)
        async def remove(ctx, remove_name: str):

            if not self.bot.check_admin(ctx.message.author):
                return

            to_remove = self.bot.get_server(name=remove_name)
            if to_remove:
                self.bot.local_servers.remove(to_remove)
            else:
                await self.bot.say('Server ' + remove_name + ' does not exist')

        @server.command(pass_context=True)
        async def help(ctx):
            if not self.bot.check_admin(ctx.message.author):
                return

            await self.bot.send_message(ctx.message.author,
                                        "**Server usage**: `{0}server <add> [(bot name)/'this'] [(invite url)/'this'] ["
                                        "quote delay]`\n"
                                        "Note: 'this' refers to bot/server this command is being executed from\n"
                                        "Example: `{0}server add this this 3` adds current server to current bot with "
                                        "spam timer of 3 minutes\n"
                                        "*Note: This command is deprecated, as servers are now added automagically. "
                                        "It remains for manual control in case of errors, but you shouldn't ever have "
                                        "to use it*".format(self.bot.command_prefix))

        @self.bot.command(pass_context=True)
        async def backup(ctx):
            if not self.bot.check_admin(ctx.message.author):
                return

            storage.save_backup()

            await self.bot.say('All bots serialized to backup.')

        @self.bot.command(pass_context=True)
        async def sleep(ctx):
            if ctx.message.author.id != OWNER_ID:
                return

            if not global_util.save_in_progress:
                await self.bot.say('Good night :blush: :sleeping:')
                print('Bot process shut down internally.')
                global_util.internal_shutdown = True

        @self.bot.command(pass_context=True)
        async def regen(ctx):
            if ctx.message.author.id != OWNER_ID:
                return

            await self.bot.say('Regenerating core processes :zap: :repeat:')
            print('Bot process restarted internally.')

            while global_util.save_in_progress:
                pass

            if not global_util.save_in_progress:
                exit(1)

        @self.bot.command(pass_context=True)
        async def writeresp(ctx):
            if ctx.message.author.id != global_util.OWNER_ID:
                return

            global_util.save_in_progress = True

            for b in self.bot.bot_list:
                for s in b.servers:
                    with open('bots/{}/{}/responses.json'.format(b.name, s.name), 'w') as fi:
                        resps = []
                        for q in s.commands:
                            q_name = q['name']
                            q_content = q['text']
                            q_quote = True
                            q_timer = s.command_delay
                            if '@c' in q_content:
                                q_content = q_content.replace('@c', '')
                                q_quote = False
                            else:
                                if q['author'] != 'none':
                                    q_content += '@ca' + q['author']
                            if '@t' in q_content:
                                q_content = q_content.replace('@t', '')
                                q_timer = None
                            add_resp = {'name': q_name,
                                        'content': q_content,
                                        'identifier': None,
                                        'is_image': False,
                                        'high_permissions': False,
                                        'is_command': True,
                                        'spam_timer': q_timer,
                                        'is_quote': q_quote}
                            resps.append(add_resp)
                        json.dump(resps, fi)

            global_util.save_in_progress = False

            await self.bot.say('Turned all quotes in all servers in all bots into responses.')

        @self.bot.command(pass_context=True)
        async def writeblock(ctx):
            if ctx.message.author.id != global_util.OWNER_ID:
                return

            global_util.save_in_progress = True

            for b in self.bot.bot_list:
                for s in b.servers:
                    s.block_list = [{'name': x, 'channel': 'all'} for x in s.block_list]
                    storage.write_server_data(b, s)

            global_util.save_in_progress = False

            await self.bot.say('Transformed all block items in all bots.')

        @self.bot.command(pass_context=True)
        async def delet(ctx, serv_id: str, chan_id: str, m_id: str):
            if ctx.message.author.id != global_util.OWNER_ID:
                return

            await self.bot.http.delete_message(channel_id=chan_id, message_id=m_id, guild_id=serv_id)
            out = await self.bot.say('✅')
            schedule_delete(self.bot, out, 5)

        @self.bot.command(pass_context=True)
        async def sayd(ctx, text: str, *, args: str = None):
            if not self.bot.has_high_permissions(ctx.message.author):
                return

            if text == 'help':
                await self.bot.send_message(ctx.message.author, "**Sayd help:**\n"
                                                                "`{0}sayd [message]`\n"
                                                                "`{0}sayd <embed> [args]`\n"
                                                                "Sayd (say-delete) says a message, then "
                                                                "deletes your command. Args should be space "
                                                                "separated and subargs comma-separated. Use "
                                                                "a `:` to denote the start of an arg. Arg list:\n"
                                                                "`init - title,desc,url,colour`\n"
                                                                "`footer - text,icon_url`\n"
                                                                "`image - url`\n"
                                                                "`thumbnail - url`\n"
                                                                "`author - name,url,icon_url`\n"
                                                                "`field - name,value,inline`\n"
                                                                "Example:\n"
                                                                "```python\n"
                                                                "{0}sayd embed init:title=SampleEmbed,desc=\"a "
                                                                "description\",color=0xff0000 field:name=\"One "
                                                                "field\",value=things field:name=\"Two field\","
                                                                "value=\"more things\",inline=False\n```"
                                                                "".format(self.bot.command_prefix))
                return

            await self.bot.delete_message(ctx.message)

            if text == 'embed' and args:
                arg_d = self.process_args(args)
                em = None
                av_init = arg_d['init']
                em = discord.Embed(title=av_init.get('title', discord.embeds.EmptyEmbed),
                                   description=av_init.get('desc', discord.embeds.EmptyEmbed),
                                   url=av_init.get('url', discord.embeds.EmptyEmbed),
                                   color=int(av_init.get('color', '50535C'), 16))
                for k, av in arg_d.items():
                    if k == 'footer':
                        em.set_footer(text=av.get('text', discord.embeds.EmptyEmbed),
                                      icon_url=av.get('icon_url', discord.embeds.EmptyEmbed))
                    elif k == 'image':
                        em.set_image(url=av.get('url', ''))
                    elif k == 'thumbnail':
                        em.set_thumbnail(url=av.get('url', ''))
                    elif k == 'author':
                        em.set_author(name=av.get('name', CHAR_ZWS),
                                      url=av.get('url', discord.embeds.EmptyEmbed),
                                      icon_url=av.get('icon_url', discord.embeds.EmptyEmbed))
                    elif k.find('field') == 0:
                        em.add_field(name=av.get('name', CHAR_ZWS),
                                     value=av.get('value', CHAR_ZWS),
                                     inline=self.str2bool(av.get('inline', 'true')))
                await self.bot.say(embed=em)
                # await self.bot.say('Debug dict is {}'.format(arg_d))
            else:
                if args:
                    await self.bot.say(text + ' ' + args)
                else:
                    await self.bot.say(text)

        @self.bot.command(pass_context=True)
        async def delay(ctx, time: int, arg: str, *, args: str = None):
            if ctx.message.author.id != global_util.OWNER_ID:
                return

            if arg == 'send':
                schedule_future(coro=self.bot.send_message(ctx.message.channel, args), time=time)

            elif arg == 'react':
                if args.find('<') == 0:
                    args = args.replace('<:', '')
                    args = args.replace('>', '')
                    emoji = args.split(':')
                    emoji = discord.Emoji(name=emoji[0], id=emoji[1], require_colons=True)
                else:
                    emoji = args[0]

                schedule_future(coro=self.bot.add_reaction(ctx.message, emoji), time=time)

        @self.bot.command(pass_context=True)
        async def serverid(ctx, name: str):
            for b in self.bot.bot_list:
                for s in b.servers:
                    if s.name.lower() == name.lower():
                        await self.bot.say('`{}`'.format(s.id))
                        return

        @self.bot.command(pass_context=True)
        async def checkadmin(ctx):
            result = self.bot.check_admin(ctx.message.author)
            await self.bot.say('check_admin shows you as: {}'.format(result))


    @staticmethod
    def extract_code(line: str) -> str:
        code_start = line.find('```')
        if code_start != -1:
            code_end = line.find('```', code_start + 3)
            if code_end != -1:
                return line[code_start + 3:code_end]
            else:
                return line
        code_start = line.find('`')
        if code_start != -1:
            code_end = line.find('`', code_start + 1)
            if code_end != -1:
                return line[code_start + 1:code_end]
        return line

    @staticmethod
    def process_args(args: str) -> dict:
        arg_list = shlex.split(args, ' ')
        out_d = {}
        for a in arg_list:
            pieces = a.split(':', 1)
            base = pieces[0]
            sa_dict = {}
            sub_args = pieces[1].split(',')
            for sa in sub_args:
                sa_pieces = sa.split('=')
                sa_dict[sa_pieces[0]] = sa_pieces[1]
            out_d[base] = sa_dict
        return out_d

    @staticmethod
    def str2bool(text: str):
        return True if text.lower() == 'true' else False


def setup(bot):
    return Admin(bot)
