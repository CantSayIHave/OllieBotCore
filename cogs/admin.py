import asyncio

import storage_manager_v2 as storage
from discordbot import DiscordBot
from util import global_util
from util.global_util import *
import util.scheduler as scheduler


class Admin:
    def __init__(self, bot: DiscordBot):
        self.bot = bot

        @self.bot.command(pass_context=True)
        async def repl(ctx, user: discord.Member = None):

            if not self.bot.check_admin(ctx.message.author):
                return

            session_log = ''

            def prints(anything):
                self.print_log += str(anything) + '\n'

            await self.bot.say('Entering REPL for {}.'.format(ctx.message.author.name))
            base_message = await self.bot.say('```python\n\n```')

            async def push_line(text):
                """
                Rather than pushing a newline, this just prints.
                This way a >>> may be filled in.
                """
                nonlocal base_message, session_log
                session_log += text
                if len(session_log) > 500:
                    # New message created here, so session log is cleared too
                    session_log = ''
                    base_message = self.bot.send_message(base_message.channel, '```python\n{}\n```'.format(text))
                else:
                    await self.bot.edit_message(base_message, '```python\n{}\n```'.format(session_log))

            while True:
                self.print_log = ""
                await push_line('>>> ')
                try:
                    response = await self.bot.wait_for_message(author=ctx.message.author, timeout=10.0 * 60.0)
                except asyncio.TimeoutError:
                    await self.bot.say('Exiting REPL.')
                    break

                line = self.extract_code(response.content)

                await push_line(line + '\n')

                # attempt to delete input line
                try:
                    await self.bot.delete_message(response)
                except:
                    pass

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
                    if ret_print is not None:
                        prints(ret_print)
                except Exception:
                    try:
                        ret_print = exec(line)
                        if ret_print is not None:
                            prints(ret_print)
                    except Exception as e:
                        prints(e)
                if self.print_log:
                    await push_line(self.print_log)
                else:
                    await push_line('\n')

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

            storage.write_bot_data(self.bot)
            for s in self.bot.local_servers:
                storage.write_server(s)

            await self.bot.say('Bot serialized to json.')

        @self.bot.command(pass_context=True)
        async def invite(ctx):
            if not self.bot.check_admin(ctx.message.author):
                return

            await self.bot.say('My invite link is '
                               'https://discordapp.com/oauth2/authorize?'
                               '&client_id={}'
                               '&scope=bot'
                               '&permissions=2146823281'.format(self.bot.user.id))

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
                symbol = symbol.replace(' ', '').replace('\n', '')
                self.bot.command_prefix = symbol
                storage.write_bot_data(self.bot)
                await self.bot.say('Set bot prefix to `{0}`'.format(symbol))

        @self.bot.group(pass_context=True)
        async def server(ctx):
            if not self.bot.check_admin(ctx.message.author):
                raise discord.Forbidden

        @server.command(pass_context=True)
        async def remove(ctx, remove_name: str):

            to_remove = self.bot.get_server(name=remove_name)
            if to_remove:
                self.bot.local_servers.remove(to_remove)
            else:
                await self.bot.say('Server ' + remove_name + ' does not exist')

        """
        @self.bot.command(pass_context=True)
        async def backup(ctx):
            if not self.bot.check_admin(ctx.message.author):
                return

            storage.save_backup()

            await self.bot.say('All bots serialized to backup.')"""

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

            await self.bot.delete_message(ctx.message)

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
        @self.bot.test_high_perm
        async def serverid(server, ctx, name: str):
            if name:
                server = self.bot.get_server(name=name)

            if server:
                await self.bot.say('`{}`'.format(server.id))

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
    def str2bool(text: str):
        return True if text.lower() == 'true' else False


def setup(bot):
    return Admin(bot)
