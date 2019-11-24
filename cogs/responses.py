import copy
import shlex

from discord.ext import commands

import storage_manager_v2 as storage
from response import *
from server import Server
from util import global_util, paginator
from util.containers import *

arg_to_data = {'true': True,
               'false': False,
               'none': None,
               'empty': ""}

data_to_arg = {True: 'true',
               False: 'false',
               None: 'none',
               "": 'empty'}

display_to_correct = {'name': 'name',
                      'id': 'id',
                      'image': 'is_image',
                      'high-perm': 'high_permissions',
                      'keyword': 'is_command',
                      'spam-timer': 'spam_timer',
                      'quote': 'is_quote',
                      'author': 'author',
                      'content': 'content',
                      'search-type': 'search_type',
                      'delete': 'delete'}

correct_to_display = {v: a for a, v in display_to_correct.items()}


class Responses:
    def __init__(self, bot):  # : discordbot.DiscordBot
        self.bot = bot

        @self.bot.group(pass_context=True)
        async def response(ctx):
            pass

        @response.command(pass_context=True)
        async def add(ctx, name: str, *, args: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            name = name.lower()

            if name.find('"') == 0:
                name = name + args[:args.find('"') + 1]
                args = args[args.find('"') + 1:]

            name = name.replace('"', '')

            if in_server.response_lib.get(name, by_name=True):
                await self.bot.say('`{0}` already exists in the response library. Use `{1}response '
                                   'edit` and `{1}response remove` to manage it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            if self.bot.get_command(name=name):
                await self.bot.say('`{}` already exists as a default command, so it may not be used.'
                                   ''.format(name))
                return

            add_dict = self.process_args(args, force_content=True)
            add_dict['name'] = name
            if '```' not in add_dict['content']:
                add_dict['content'] = add_dict['content'].replace('`', '')

            r = in_server.response_lib.add(Response(**add_dict))

            storage.write_responses(in_server)

            if r.is_image:
                await self.bot.say('Added image response {} to library ✅'.format(name))
            else:
                if r.is_command:
                    await self.bot.say('Added command response {} to library ✅'.format(name))
                else:
                    await self.bot.say('Added keyword response {} to library ✅'.format(name))

        @response.command(pass_context=True)
        async def remove(ctx, name: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            name = name.lower()

            if not in_server.response_lib.get(name, by_name=True):
                await self.bot.say('`{0}` does not exist in the response library. Use `{1}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            attempt = in_server.response_lib.remove(name)

            storage.write_responses(in_server)

            if attempt:
                await self.bot.say('Successfully removed response {} from the library!'.format(name))
            else:
                await self.bot.say('Failed to remove response {} from the library.'.format(name))

        @response.command(pass_context=True)
        async def edit(ctx, name: str, *, args: str = ""):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            name = name.lower()

            resp = in_server.response_lib.get(name, by_name=True)
            if not resp:
                await self.bot.say('`{0}` does not exist in the response library. Use `{1}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            add_dict = self.process_args(args)

            if 'content' in add_dict:
                if '```' not in add_dict['content']:
                    add_dict['content'] = add_dict['content'].replace('`', '')

            if 'name' in add_dict:
                if self.bot.get_command(add_dict['name']):
                    await self.bot.say('`{}` already exists as a default command, so it may not be used.'
                                       ''.format(add_dict['name']))
                    add_dict.pop('name')

            r = in_server.response_lib.edit(resp, add_dict)

            storage.write_responses(in_server)

            new_options = self.get_display(r.__dict__)

            em = self.build_embed(new_options, 0xf4e542, 'https://abs.twimg.com/emoji/v2/72x72/1f4dd.png')
            await self.bot.say(embed=em)

            if len(new_options['content']) > 2048:
                await self.bot.say('**Content:** {}'.format(new_options['content']))

        @response.command(pass_context=True)
        async def append(ctx, method: str, name: str, to_append: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            name = name.lower()

            resp = in_server.response_lib.get(name, by_name=True)
            if not resp:
                await self.bot.say('`{}` does not exist in the response library. Use `{}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            if 'before=true' in to_append.lower() and ' @and ' in resp.content:
                to_append = to_append.replace('before=true', '')
                halves = resp.content.split(' @and ')
                resp.content = '{}{} @and {}'.format(halves[0], to_append, halves[1])
            elif method == 'r':
                to_append = to_append.replace('before=true', '')

                suffixes = ['@ra', '@ru', '@rn']
                present_suffixes = []
                for s in suffixes:
                    if s in resp.content:
                        present_suffixes.append(s)
                        resp.content = resp.content.replace(s, '')

                resp.content += to_append

                for s in present_suffixes:
                    resp.content += s
            else:
                resp.content += to_append

            storage.write_responses(in_server)

            options = self.get_display(resp.__dict__)

            em = self.build_embed(options, 0xf4e542, 'https://abs.twimg.com/emoji/v2/72x72/1f4dd.png')
            await self.bot.say(embed=em)

            if len(options['content']) > 2048:
                await self.bot.say('**Content:** {}'.format(options['content']))

        @response.command(pass_context=True)
        async def transfer(ctx, name: str, to_server_name: str):
            if ctx.message.author.id != global_util.OWNER_ID:
                return

            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            name = name.lower()

            resp = in_server.response_lib.get(name, by_name=True)
            if not resp:
                await self.bot.say('`{}` does not exist in the response library. Use `{}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            if not global_util.is_num(to_server_name):
                to_server = self.bot.get_server(name=to_server_name)
                if not to_server:
                    await self.bot.say('This server does not exist!')
                    return
            else:
                to_server = self.bot.get_server(id=to_server_name)

            if to_server.response_lib.get(resp.name, by_name=True):
                await self.bot.say('`{}` already exists in {}'.format(name, to_server.name))

            to_server.response_lib.responses.append(copy.deepcopy(resp))

            storage.write_responses(to_server)

            await self.bot.say('Sent response `{}` to server `{}`'.format(name, to_server.name))

        @response.command(pass_context=True)
        async def get(ctx, name: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            name = name.lower()

            resp = in_server.response_lib.get(name, by_name=True)
            if not resp:
                await self.bot.say('`{0}` does not exist in the response library. Use `{1}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            options = self.get_display(resp.__dict__)

            em = self.build_embed(options, 0x41f45c, 'https://abs.twimg.com/emoji/v2/72x72/1f4dd.png')

            await self.bot.say(embed=em)

            if len(options['content']) > 2048:
                await self.bot.say('**Content:** {}'.format(options['content']))

        @response.command(pass_context=True)
        async def listall(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = self.bot.get_server(server=ctx.message.server)

            if not self.bot.has_high_permissions(ctx.message.author, in_server):
                return

            responses = in_server.response_lib.responses

            def list_responses():
                nonlocal responses
                for r in responses:  # type: Response
                    a_type = 'command'
                    r_type = 'text'
                    if r.is_image:
                        r_type = 'image'
                    elif r.is_quote:
                        r_type = 'quote'
                    if not r.is_command:
                        a_type = 'keyword'
                    yield EmbedField(name=r.name, value='{}, {}'.format(a_type, r_type), inline=False)

            await paginator.paginate(list_responses(),
                                     title='Response List',
                                     bot=self.bot,
                                     destination=ctx.message.channel,
                                     icon='https://abs.twimg.com/emoji/v2/72x72/1f4d1.png',
                                     color=0xff00dc,
                                     author=ctx.message.author)

        @response.command(pass_context=True)
        @self.bot.test_high_perm
        async def image(server, ctx, operation, target, *, url):

            target = target.lower()

            resp = server.response_lib.get(target, by_name=True)  # type: Response
            if not resp:
                await self.bot.say('`{0}` does not exist in the response library. Use `{1}response add` to add it.'
                                   ''.format(target, self.bot.command_prefix))
                return

            if not operation.startswith(('add', 'rem')):
                await self.bot.say('Please format as {}response image <add/remove> [target] [image url/#]'
                                   ''.format(self.bot.command_prefix))
                return

            if not resp.is_image:
                await self.bot.say('**{}** is not an image response!'.format(target))
                return

            if operation == 'add':
                url_list = None
                if ',' in url:
                    url_list = url.split(',')
                elif not global_util.validate_url(url):
                    await self.bot.say('The url provided is invalid.')
                    return

                fixed_coding = self.fix_album(resp.content)
                if url_list:
                    for u in url_list:
                        if global_util.validate_url(u):
                            fixed_coding += ' @r {}'.format(u)
                else:
                    fixed_coding += ' @r  {}'.format(url)
                resp.content = fixed_coding
                storage.write_responses(server)
                await self.bot.say('Added image to response **{}** ✅'.format(target))
            else:
                await self.bot.say('Utility not implemented (but it will be)')

        @response.command(pass_context=True)
        async def help(ctx, arg: str = None):

            if not self.bot.has_high_permissions(ctx.message.author):
                return

            def help_form(text: str):
                """Simply allows for formatting paragraphs without need for line continue characters"""
                return text

            if arg == 'formatting':
                out_msg = help_form("**Response Formatting:**\n"
                                    "Responses support several types of formatting "
                                    "for regular responses and image responses.\n\n"
                                    "**__For Text:__**\n"
                                    "`@u` is replaced with the message author's mention\n"
                                    "`@a` is replaced with an argument, if called.\n"
                                    "`@a @a @a` will be replaced with the first, second "
                                    "and third argument supplied.\n"
                                    "An \"argument\" is anything that comes after the command:\n\n"
                                    "`.command arg1 arg2 arg3`\n\n"
                                    "*Note: arguments only work with command responses*\n"
                                    "Adding `@ru` at the very end of `content` will replace "
                                    "all `@u` instances with `@a` *if* arguments are passed.\n"
                                    "Finally, use `' @r '` to break content into tags that "
                                    "will be randomly selected from. Make sure to include the "
                                    "spaces around `@r`. For example, a response "
                                    "called `fren` may have the formatting:\n\n"
                                    "```@u is my fren @r @u may be my fren @r @u is not my fren @ru```\n\n"
                                    "When called, one of these three pieces will be chosen:\n"
                                    "`@u is my fren`\n"
                                    "`@u may be my fren`\n"
                                    "`@u is not my fren`\n"
                                    "If the response is called like `{0}fren`, the response will "
                                    "format like\n\n"
                                    "{1} is not my fren\n\n"
                                    "however if it's called like `{0}fren` {2}, the response will "
                                    "format like\n\n"
                                    "{2} is my fren\n\n"
                                    "due to the `@ru` on the end.\n\n"
                                    "**__For Images__**\n"
                                    "The content of images should always be links to sources. Two tags apply here:\n"
                                    "`' @r '` for random selections\n"
                                    "`' @m '` for multiple images in one selection\n"
                                    "Once again, spaces around the tag are important. For the following content"
                                    "formatting:\n\n"
                                    "```https://abs.twimg.com/emoji/v2/72x72/1f34d.png @m "
                                    "https://abs.twimg.com/emoji/v2/72x72/1f6ab.png @m "
                                    "https://abs.twimg.com/emoji/v2/72x72/1f355.png @r "
                                    "https://abs.twimg.com/emoji/v2/72x72/1f645-200d-2640-fe0f.png```\n\n"
                                    "One of these two pieces will be selected:\n"
                                    "`https://abs.twimg.com/emoji/v2/72x72/1f34d.png`\n"
                                    "`https://abs.twimg.com/emoji/v2/72x72/1f6ab.png`\n"
                                    "`https://abs.twimg.com/emoji/v2/72x72/1f355.png`\nor\n"
                                    "`https://abs.twimg.com/emoji/v2/72x72/1f645-200d-2640-fe0f.png`"
                                    "".format(self.bot.command_prefix,
                                              self.bot.user.mention,
                                              ctx.message.author.mention))
                await self.bot.send_message(ctx.message.author, out_msg)
                return
            elif arg == 'images':
                out_msg_a = help_form("**Response Images:**\n"
                                      "While you may format albums on your own with `' @m '` and `' @r '`, use\n"
                                      "`{0}response <image> <add> [target] [image url] [optional:args]`\n"
                                      "`{0}response <image> <remove> [target] [image url/#]`\n"
                                      "to speed up the addition/removal of images. Here, `target` is the name of "
                                      "the response, `image url` is the specific url you'd like to add/remove, and "
                                      "`#` is the number of the url starting at 1 and counting up that you would "
                                      "like to remove. By default `add` appends `' @m '` and the image url, but you "
                                      "may change this with args:\n".format(self.bot.command_prefix))

                em = discord.Embed(title='───────────────────────', color=0x0000ff)
                em.set_author(name='Args', icon_url='https://abs.twimg.com/emoji/v2/72x72/27a1.png')
                em.add_field(name='random',
                             value="`['true'/'false'] default:false`\n"
                                   "append an `' @r '` instead of an `' @m '`",
                             inline=False)
                em.add_field(name='raw',
                             value="`['true'/'false'] default:false`\n"
                                   "treats `image url` parameter as *already-formatted* so you may add "
                                   "whatever special tags you like",
                             inline=False)

                out_msg_b = help_form("**__Example:__**\n"
                                      "For an image response named `doggo` that has the content:\n\n"
                                      "```https://i.redd.it/95js7oygrr8z.jpg @r "
                                      "https://i.imgur.com/HlYZxBP.jpg```\n\n"
                                      "Calling `{0}response image add doggo https://i.redd.it/t2usfrtt2q301.jpg` "
                                      "will produce:\n\n"
                                      "```https://i.redd.it/95js7oygrr8z.jpg @r "
                                      "https://i.imgur.com/HlYZxBP.jpg @m "
                                      "https://i.redd.it/t2usfrtt2q301.jpg```\n\n"
                                      "However, calling `{0}response image add doggo "
                                      "https://i.redd.it/t2usfrtt2q301.jpg random=true` will produce\n\n"
                                      "```https://i.redd.it/95js7oygrr8z.jpg @r "
                                      "https://i.imgur.com/HlYZxBP.jpg @r "
                                      "https://i.redd.it/t2usfrtt2q301.jpg```\n\n"
                                      "If you wanted to remove the middle link at this point, you could remove it "
                                      "by name, or just call\n\n"
                                      "`{0}response image remove doggo 2`\n\n"
                                      "which would produce:\n\n"
                                      "```https://i.redd.it/95js7oygrr8z.jpg @r "
                                      "https://i.redd.it/t2usfrtt2q301.jpg```".format(self.bot.command_prefix))
                await self.bot.send_message(ctx.message.author, out_msg_a)
                await self.bot.send_message(ctx.message.author, embed=em)
                await self.bot.send_message(ctx.message.author, out_msg_b)
                return

            spam_timer_def = 1
            if ctx.message.server:
                in_server = self.bot.get_server(server=ctx.message.server)
                spam_timer_def = in_server.command_delay

            first_half = help_form("**Response help:**\n"
                                   "`{0}response <add/edit> [name] [args]`\n"
                                   "`{0}response <remove> [name]`\n"
                                   "`{0}response <image> <add/remove> [target] [image url/#]`\n"
                                   "`{0}response <get> [name]`\n"
                                   "`{0}response <list>`\n\n"
                                   "Use `response` to add/manage/remove custom commands \n"
                                   "and keyword responses. Custom commands will be called "
                                   "in the format:\n"
                                   "`{0}command`\n"
                                   "while keyword responses will be called by a keyword\n"
                                   "found somewhere in a message. A keyword response with\n"
                                   "the name `wtf` would be called by the following message:\n"
                                   "`hey wtf`\n"
                                   "Keyword responses will auto-delete in 10 seconds.\n\n"
                                   "Use `{0}response <add/edit>` to add/edit responses, and\n"
                                   "pass custom args after `name` to specify all attributes\n"
                                   "for each command. The list of args is as follows:\n"
                                   "".format(self.bot.command_prefix))

            em = discord.Embed(title='───────────────────────', color=0x0000ff)
            em.set_author(name='Args', icon_url='https://abs.twimg.com/emoji/v2/72x72/27a1.png')
            em.add_field(name='id',
                         value="`[anything/'none'] default:none`\n"
                               "alternate id used to call the response instead of name",
                         inline=False)
            em.add_field(name='image',
                         value="`['true'/'false']  default:false`\n"
                               "whether response is an image/image album",
                         inline=False)
            em.add_field(name='high-perm',
                         value="`['true'/'false']  default:false`\n"
                               "whether response is mod+ only",
                         inline=False)
            em.add_field(name='keyword',
                         value="`['true'/'false']  default:false`\n"
                               "whether response is keyword activated or a command",
                         inline=False)
            em.add_field(name='spam-timer',
                         value="`[minutes/'none']  default:{}`\n"
                               "spam timer for response".format(spam_timer_def),
                         inline=False)
            em.add_field(name='quote',
                         value="`['true'/'false']  default:false`\n"
                               "whether response is formatted as a quote",
                         inline=False)
            em.add_field(name='author',
                         value="`[anything/'none'] default:none`\n"
                               "author to go with quote",
                         inline=False)
            em.add_field(name='search-type',
                         value="`['explicit'/'contains'] default:none`\n"
                               "author to go with quote",
                         inline=False)
            em.add_field(name='author',
                         value="`[anything/'none'] default:none`\n"
                               "author to go with quote",
                         inline=False)
            em.add_field(name='content',
                         value="`[anything]        default:empty`\n"
                               "actual content of response",
                         inline=False)

            second_half = help_form("Format args with an `=`, like `arg=value`.\n"
                                    "`args` are not necessary as defaults will be assumed\n"
                                    "without them, and the final argument will always be assumed\n"
                                    "to be `content`. Therefore, the simplest way to add a command\n"
                                    "is as follows:\n\n"
                                    "```{0}response add fren \"@u is not my fren\"```\n\n"
                                    "This will be called by `.fren`. The most complicated way\n"
                                    "would be as follows:\n\n"
                                    "```{0}response add screech id=reee image=false high-perm=false keyword=true "
                                    "spam-timer=none quote=false author=none content=\"stop hitting yourself\"```\n\n"
                                    "This would be triggered by any instance of reee found in the message.\n\n"
                                    "Call `{0}response help formatting` for tag formatting in content\n"
                                    "Call `{0}response help images` for info on special album commands\n"
                                    "Call `{0}response help examples` for more examples using `response`"
                                    "".format(self.bot.command_prefix))

            await self.bot.send_message(ctx.message.author, first_half)
            await self.bot.send_message(ctx.message.author, embed=em)
            await self.bot.send_message(ctx.message.author, second_half)

    @staticmethod
    def process_args(args: str, force_content=False) -> dict:
        arg_list = shlex.split(args, ' ')
        out_dict = {}

        for key in arg_list:
            key_parts = key.split('=')
            if len(key_parts) == 2:
                name = key_parts[0]
                value = key_parts[1]
                if name.lower() in display_to_correct and value.lower() in arg_to_data:
                    out_dict[display_to_correct[name.lower()]] = arg_to_data[value.lower()]
                elif name.lower() in display_to_correct:
                    out_dict[display_to_correct[name.lower()]] = value

        if 'is_command' in out_dict:
            out_dict['is_command'] = not out_dict['is_command']  # opposite of keyword

        if 'content' not in out_dict and force_content:
            content = arg_list[len(arg_list) - 1].split('=')
            out_dict['content'] = content[len(content) - 1]

        return out_dict

    @staticmethod
    def get_display(options: dict):
        out_dict = {}
        out_dict['keyword'] = str(not options['is_command']).lower()
        options['author'] = None

        if options['is_quote']:
            if '@ca' in options['content']:
                options['author'] = options['content'].rsplit('@ca')[1]
        for k, v in options.items():
            if k != 'is_command':
                if k in correct_to_display and v in data_to_arg and type(v) is not int:
                    out_dict[correct_to_display[k]] = data_to_arg[v]
                elif k in correct_to_display:
                    out_dict[correct_to_display[k]] = v  # for content, author, id etc

        return out_dict

    @staticmethod
    def build_embed(options: dict, color: int, icon: str) -> discord.Embed:
        em = discord.Embed(title='───────────────────────', color=color)  # pink
        em.set_author(name='Response', icon_url=icon)
        em.add_field(name='name', value=options['name'])
        em.add_field(name='id', value=options['id'])
        em.add_field(name='image', value=options['image'])
        em.add_field(name='high-perm', value=options['high-perm'])
        em.add_field(name='keyword', value=options['keyword'])
        em.add_field(name='spam-timer', value=options['spam-timer'])
        em.add_field(name='quote', value=options['quote'])
        em.add_field(name='author', value=options['author'])
        em.add_field(name='search-type', value=options['search-type'])
        em.add_field(name='delete', value=options['delete'])
        content = options['content']
        if len(content) <= 1024:
            em.add_field(name='content', value=content)
        if 1024 < len(content) <= (2048 - len('Content: ')):
            em.set_footer(text='**Content:** {}'.format(content))
        return em

    @staticmethod
    def fix_album(coding):
        coding = coding.replace(' @m  @m ', ' @m ')
        coding = coding.replace(' @m  @r ', ' @r ')
        coding = coding.replace(' @r  @m ', ' @r ')
        coding = coding.replace(' @r  @r ', ' @r ')

        if coding.startswith(' @r '):
            coding = coding[4:]

        if coding.endswith(' @r '):
            coding = coding[:-4]

        return coding

async def execute_responses(msg: discord.Message, bot: commands.Bot, in_server: Server, content_lower: str):
    high_perm = bot.has_high_permissions(msg.author, in_server)
    if content_lower.find(bot.command_prefix) == 0:
        command = content_lower.split(' ')[0].split(bot.command_prefix)[1].lower()
        if in_server.response_lib.has(command):  # commands
            com_response = in_server.response_lib.get(command)
            args = shlex.split(content_lower, ' ')[1:]
            resp_out = in_server.response_lib.get_processed(com_response,
                                                            msg=msg,
                                                            args=args,
                                                            has_high_perm=high_perm,
                                                            first_arg=True)
            if resp_out:
                if type(resp_out) is str:
                    await bot.send_message(msg.channel, resp_out)
                    return
                elif type(resp_out) is discord.Embed:
                    await bot.send_message(msg.channel, embed=resp_out)
                    return

    first_occurrence = in_server.response_lib.get_exact(content_lower)  # exact

    if not first_occurrence:
        first_occurrence = in_server.response_lib.get_occurrence(content_lower)  # keywords

    if not first_occurrence:
        first_occurrence = in_server.response_lib.get_explicit(content_lower)  # keyword - split()

    if first_occurrence:
        resp_out = in_server.response_lib.get_processed(first_occurrence,
                                                        msg=msg,
                                                        args=[],
                                                        has_high_perm=high_perm,
                                                        first_arg=False)
        if resp_out:
            if type(resp_out) is str:
                m = await bot.send_message(msg.channel, resp_out)
                if first_occurrence.delete:
                    global_util.schedule_delete(bot, m, first_occurrence.delete)
                return
            elif type(resp_out) is discord.Embed:
                m = await bot.send_message(msg.channel, embed=resp_out)
                if first_occurrence.delete:
                    global_util.schedule_delete(bot, m, first_occurrence.delete)
                return


def setup(bot):
    return Responses(bot)
