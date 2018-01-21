import discord
from discord.ext import commands
import random
import shlex
from global_util import *


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
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        @self.bot.group(pass_context=True)
        async def quote(ctx):
            if (ctx.invoked_subcommand is None) and ctx.message.server:  # random quote
                in_server = get_server(ctx.message.server.id, self.bot)

                if has_high_permissions(ctx.message.author, in_server):
                    quote_set = random.choice(in_server.commands)
                    if quote_set['author'] == 'none':
                        await self.bot.say('"' + quote_set['text'].replace('@a', ctx.message.author.mention) + '"')
                    else:
                        await self.bot.say('"' + quote_set['text'].replace('@a', ctx.message.author.mention) + '" - ' +
                                           quote_set['author'].replace('@a',
                                                                       ctx.message.author.mention))  # "quote" - author
                    return

                # turn this on to enable .quote for normies
                """
                available_quotes = []  # load in available quotes
                for c in in_server.commands:
                    if int(c['timer']) < 1:
                        available_quotes.append(c)
                if available_quotes:
                    quote_set = random.choice(available_quotes)
                    if quote_set:
                        quote_set['timer'] = str(in_server.command_delay * 60)
                        if quote_set['author'] == 'none':
                            await self.bot.say('"' + quote_set['text'].replace('@a', ctx.message.author.mention) + '"')
                        else:
                            await self.bot.say('"' + quote_set['text'].replace('@a', ctx.message.author.mention) + '" - ' +
                                               quote_set['author'].replace('@a', ctx.message.author.mention))  # "quote" - author
                else:
                    await self.bot.say('No quotes currently available')"""

        @quote.command(pass_context=True)
        async def add(ctx, name_in: str, quote_in: str, author_in: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if in_server:
                if self.bot.get_command(name_in):  # i forgot i did this but ver good job self
                    await self.bot.say('Sorry, ' + name_in + ' is already a control command')
                    return

                if author_in:
                    in_server.commands.append({'name': name_in,
                                               'text': quote_in,
                                               'timer': 0,
                                               'author': author_in})
                else:
                    in_server.commands.append({'name': name_in,
                                               'text': quote_in,
                                               'timer': 0,
                                               'author': 'none'})
                writeBot(self.bot)
                await self.bot.say('Added quote ' + name_in)

        @quote.command(pass_context=True)
        async def listall(ctx, arg: str = None):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if in_server:
                out_msg = 'Quote list:\n'
                if arg == 'debug':
                    for q in in_server.commands:
                        out_msg += '`{0}{1} - timer at {2}`\n'.format(self.bot.command_prefix, q['name'], q['timer'])
                else:
                    for q in in_server.commands:
                        out_msg += '`' + self.bot.command_prefix + q['name'] + '`\n'
                await self.bot.say(out_msg)

        @quote.command(pass_context=True)
        async def remove(ctx, r_name: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if in_server:
                q = None
                for c in in_server.commands:
                    if c['name'] == r_name:
                        q = c
                if q:
                    in_server.commands.remove(q)
                    writeBot(self.bot)
                    await self.bot.say('Removed quote "' + r_name + '"')
                else:
                    await self.bot.say('Quote "' + r_name + '" does not exist')

        @quote.command(pass_context=True)
        async def help(ctx):
            out_str = "**Quote usage**:\n"

            if has_high_permissions(ctx.message.author, b=self.bot):
                out_str += "`{0}quote <add> [name] [quote]`\n" \
                           "`{0}quote <add> [name] [quote] [author]`\n" \
                           "`{0}quote <remove> [name]`\n" \
                           "`{0}quote <list>`\n"

            out_str += "`{0}[quote name]`\n" \
                       "This is an archaic system that is soon to be replaced.\n"

            if has_high_permissions(ctx.message.author, b=self.bot):
                out_str += "Note: for `{0}add`/`{0}remove`, make sure 'name' contains no spaces " \
                           "and put quotes around 'quote' if said quote contains spaces.\n" \
                           'Note: if `[author]` is included, the quote will format as `"quote" - author`. Otherwise, ' \
                           'default format is simply `"quote"`\n' \
                           'Example: `{0}add greetings "Hi, I' + \
                           "'m a bot" + '" OllieBot` is called by ' \
                                        '`{0}greetings`'

            await self.bot.send_message(ctx.message.author, out_str.format(self.bot.command_prefix))

        @self.bot.group(pass_context=True)
        async def response(ctx):
            pass

        @response.command(pass_context=True)
        async def add(ctx, name: str, *, args: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

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

            writeResponses(self.bot, in_server)

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

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            if not in_server.response_lib.get(name, by_name=True):
                await self.bot.say('`{0}` does not exist in the response library. Use `{1}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            attempt = in_server.response_lib.remove(name)

            writeResponses(self.bot, in_server)

            if attempt:
                await self.bot.say('Successfully removed response {} from the library!'.format(name))
            else:
                await self.bot.say('Failed to remove response {} from the library.'.format(name))

        @response.command(pass_context=True)
        async def edit(ctx, name: str, *, args: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

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

            writeResponses(self.bot, in_server)

            new_options = self.get_display(r.__dict__)

            em = discord.Embed(title='───────────────────────', color=0xf4e542)  # yellow
            em.set_author(name='Response Edit', icon_url='https://abs.twimg.com/emoji/v2/72x72/270d.png')
            em.add_field(name='name', value=new_options['name'])
            em.add_field(name='id', value=new_options['id'])
            em.add_field(name='image', value=new_options['image'])
            em.add_field(name='high-perm', value=new_options['high-perm'])
            em.add_field(name='keyword', value=new_options['keyword'])
            em.add_field(name='spam-timer', value=new_options['spam-timer'])
            em.add_field(name='quote', value=new_options['quote'])
            em.add_field(name='author', value=new_options['author'])
            em.add_field(name='search-type', value=new_options['search-type'])
            em.add_field(name='delete', value=new_options['delete'])
            em.add_field(name='content', value=new_options['content'])
            await self.bot.say(embed=em)

        @response.command(pass_context=True)
        async def get(ctx, name: str):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            resp = in_server.response_lib.get(name, by_name=True)
            if not resp:
                await self.bot.say('`{0}` does not exist in the response library. Use `{1}response add` to add it.'
                                   ''.format(name, self.bot.command_prefix))
                return

            options = self.get_display(resp.__dict__)

            em = discord.Embed(title='───────────────────────', color=0x41f45c)  # pink
            em.set_author(name='Response', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4dd.png')
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
            em.add_field(name='content', value=options['content'])
            await self.bot.say(embed=em)

        """
        @response.command(pass_context=True)
        async def listall(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            em = discord.Embed(title='───────────────────────', color=0xff00dc)  # pink
            em.set_author(name='Response List', icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4d1.png')

            if len(in_server.response_lib.responses) > 0:
                index = 0
                for r in in_server.response_lib.responses:  # type: Response
                    a_type = 'command'
                    r_type = 'text'
                    if r.is_image:
                        r_type = 'image'
                    elif r.is_quote:
                        r_type = 'quote'
                    if not r.is_command:
                        a_type = 'keyword'
                    em.add_field(name=r.name, value='{}, {}'.format(a_type, r_type), inline=False)
                    index += 1
                    if index >= 25:
                        await self.bot.say(embed=em)
                        em = discord.Embed(title='───────────────────────', color=0xff00dc)
                        index = 0

            await self.bot.say(embed=em)"""

        @response.command(pass_context=True)
        async def listall(ctx):
            if not ctx.message.server:
                await self.bot.say('Sorry, but this command is only accessible from a server')
                return

            in_server = get_server(ctx.message.server.id, self.bot)

            if not has_high_permissions(ctx.message.author, in_server):
                return

            field_limit = 10

            def get_page(page_num: int, responses: list):
                limit = len(responses) / field_limit
                if int(limit) != limit:
                    limit = int(limit + 1)

                limit = int(limit)

                if page_num < 1:
                    page_num = 1
                if page_num > limit:
                    page_num = limit

                l_start = int(field_limit * (page_num - 1))
                if len(responses) > (l_start + field_limit):
                    page_list = responses[l_start:l_start + field_limit]
                else:
                    page_list = responses[l_start:len(responses)]

                em = discord.Embed(title='───────────────────────', color=0xff00dc)  # pink
                em.set_author(name='Response List - Page {}/{}'.format(int(page_num), int(limit)),
                              icon_url='https://abs.twimg.com/emoji/v2/72x72/1f4d1.png')

                for r in page_list:  # type: Response
                    a_type = 'command'
                    r_type = 'text'
                    if r.is_image:
                        r_type = 'image'
                    elif r.is_quote:
                        r_type = 'quote'
                    if not r.is_command:
                        a_type = 'keyword'
                    em.add_field(name=r.name, value='{}, {}'.format(a_type, r_type), inline=False)

                return em

            current_page = 1

            em = get_page(current_page, in_server.response_lib.responses)

            base_message = await self.bot.send_message(ctx.message.channel, embed=em)
            await self.bot.add_reaction(base_message, '⏮')
            await self.bot.add_reaction(base_message, '⏪')
            await self.bot.add_reaction(base_message, '⏩')
            await self.bot.add_reaction(base_message, '⏭')
            await self.bot.add_reaction(base_message, '❌')
            await self.bot.wait_for_reaction('❌', message=base_message)
            while True:
                reaction, user = await self.bot.wait_for_reaction(['⏮', '⏪', '⏩', '⏭', '❌'],
                                                                  message=base_message,
                                                                  timeout=60)

                if not reaction:
                    break

                limit = len(in_server.response_lib.responses) / field_limit
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
                    em = get_page(current_page, in_server.response_lib.responses)
                    base_message = await self.bot.edit_message(base_message, embed=em)

        @response.command(pass_context=True)
        async def help(ctx, arg: str = None):

            if not has_high_permissions(ctx.message.author, b=self.bot):
                return

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
                in_server = get_server(ctx.message.server.id, self.bot)
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


async def execute_responses(msg: discord.Message, bot: commands.Bot, in_server: Server):
    high_perm = has_high_permissions(msg.author, in_server)
    if msg.content.find(bot.command_prefix) == 0:
        command = msg.content.split(' ')[0].split(bot.command_prefix)[1].lower()
        if in_server.response_lib.has(command):  # commands
            com_response = in_server.response_lib.get(command)
            args = msg.content.split(' ')[1:]
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

    first_occurrence = in_server.response_lib.get_occurrence(msg)  # keywords

    if not first_occurrence:
        first_occurrence = in_server.response_lib.get_explicit(msg)

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
                    schedule_delete(bot, m, first_occurrence.delete)
                return
            elif type(resp_out) is discord.Embed:
                m = await bot.send_message(msg.channel, embed=resp_out)
                if first_occurrence.delete:
                    schedule_delete(bot, m, first_occurrence.delete)
                return


def setup(bot):
    return Responses(bot)
