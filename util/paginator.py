# paginator module by Sierra
# created 2018/3/8
#
# paginates through an iterable of embed fields

import random

import asyncio

import collections
import discord
import time

from util.containers import EmbedField
from util import global_util


class Pages:
    def __init__(self, pages=[], icon=None, color=None):
        """Stores a list of embeds to display

        Parameters
        ----------
        pages : list[discord.Embed]
            list of embeds to be displayed
        icon : str
            icon for author of base embed
        color : int
            color for base embed
        """
        self.pages = pages
        self.icon = icon
        self.color = color

    def __str__(self):
        return 'Pages:({})'.format(len(self))

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self.pages)

    def __getitem__(self, item):
        return self.pages[item]

    def add_page(self, page):
        self.pages.append(page)

    def __iadd__(self, other):
        self.add_page(other)

    def base_embed(self) -> discord.Embed:
        em = discord.Embed(title='───────────────────────', color=self.color)

        if self.icon:
            em.set_author(name=global_util.CHAR_ZWS, icon_url=self.icon)

        return em


class Paginator:
    def __init__(self, items, title: str, item_limit=10, icon=None, color=None):
        self.items = items
        self.title = title
        self.item_limit = item_limit
        self.icon = icon
        self.color = color

        self.index = -1

        if not color:
            self.color = random.randint(0, 0xffffff)

        limit = len(items) / item_limit
        if int(limit) != limit:
            limit = int(limit + 1)

        self.total_pages = int(limit)

    def __str__(self):
        return 'Paginator:({})'.format(self.title)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.total_pages

    def __getitem__(self, page_num) -> discord.Embed:
        if page_num < 0:
            raise ValueError('Index cannot be less than 0.')
        if page_num > (self.total_pages - 1):
            raise ValueError('Index must be less than paginator length ({}).'.format(self.total_pages))

        """
        Find the indices of the new list of items for this page.
        First calculate the start of the list, then either extend
        by the item limit or run into the end of the list of items.
        """

        list_start = int(self.item_limit * (page_num - 1))

        page_list = self.items[list_start:list_start + self.item_limit]  # new

        """
        if len(self.items) > (list_start + self.item_limit):  # old
            page_list = self.items[list_start:list_start + self.item_limit]
        else:
            page_list = self.items[list_start:len(self.items)]"""

        em = discord.Embed(title='───────────────────────', color=self.color)  # create base embed

        # set icon if it exists, cannot be `None` because embed fields take on :class:`EmptyEmbed`
        # using `page_num + 1` so display is eg: 1/4 instead of 0/3
        if self.icon:
            em.set_author(name="{} - {}/{}".format(self.title, page_num + 1, self.total_pages), icon_url=self.icon)
        else:
            em.set_author(name="{} - {}/{}".format(self.title, page_num + 1, self.total_pages))

        for field in page_list:  # type:EmbedField
            em.add_field(name=field.name,
                         value=field.value,
                         inline=field.inline)

        return em

    def __iter__(self):
        return self

    def __next__(self):
        self.index += 1
        if self.index >= len(self):
            self.index = -1
            raise StopIteration
        return self[self.index]

    def base_embed(self) -> discord.Embed:
        em = discord.Embed(title='───────────────────────', color=self.color)

        if self.icon:
            em.set_author(name=global_util.CHAR_ZWS, icon_url=self.icon)

        return em


class Option:
    """Represents optional, extra button for paginator

    Attributes
    ----------
    button : str
        unicode emoji for display. must be a supported default discord emoji
    content : :class:`EmbedField`
        page content to be displayed when button is called

    """

    def __init__(self, button: str, content: EmbedField):
        self.button = button
        self.content = content

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Option:{}".format(self.button)


async def paginate(items,
                   title: str,
                   bot,
                   destination,
                   author,
                   item_limit=10,
                   timeout=60,
                   extra_options: list = None,
                   icon=None,
                   color=None):

    """Breaks a list of options into numbered pages, displayed on a Discord
    embed, uses reactions to scroll pages. This paginator creates each page on demand.

        Parameters
        ----------
        items : collections.Iterable
            iterable of items to paginate
        title : str
            title for each page
        bot : discordbot.DiscordBot
            discord bot
        destination
            channel to send pagination to
        author : discord.User
            user to take reactions from
        item_limit : int
            items allowed per page
        timeout : int
            timeout for reaction input
        extra_options : list[Option]
            list of extra options to display next to basic buttons
        icon : str
            icon for embed, if available
        color : int
            color for embed, if available

        """

    items = list(items)

    paginator = Paginator(items=items, title=title, item_limit=item_limit, icon=icon, color=color)

    await display(pages=paginator,
                  bot=bot,
                  destination=destination,
                  author=author,
                  timeout=timeout,
                  extra_options=extra_options)


async def display(pages,
                  bot,
                  destination,
                  author,
                  timeout=60,
                  extra_options: list = []):

    """Displays a list of embeds one at a time, using reactions to control page number

    Parameters
    ----------
    pages : iterable
        iterable of embeds to display
    bot : discordbot.DiscordBot
        discord bot
    destination
        channel to send pagination to
    author : discord.User
        user to take reactions from
    timeout : int
        timeout for reaction input
    extra_options : list[Option]
        list of extra options to display next to basic buttons

    """

    entry_time = time.time()  # used for timeout failsafe

    # Verify `extra_options` contains only :class:`Option`
    if extra_options:
        for o in extra_options:
            if type(o) is not Option:
                raise ValueError("Expected type `Option` in `extra_options`")

    current_page = 0

    base_message = await bot.send_message(destination, embed=pages[current_page])
    await bot.add_reaction(base_message, '⏮')
    await bot.add_reaction(base_message, '⏪')
    await bot.add_reaction(base_message, '⏩')
    await bot.add_reaction(base_message, '⏭')
    await bot.add_reaction(base_message, '❌')

    # Wait for final reaction for main wait loop
    if extra_options:
        for o in extra_options:  # type: Option
            await bot.add_reaction(base_message, o.button)
        await bot.wait_for_reaction(extra_options[-1].button, message=base_message)
    else:
        await bot.wait_for_reaction('❌', message=base_message)

    reactions = ['⏮', '⏪', '⏩', '⏭', '❌']
    extra_reactions = []

    if extra_options:
        extra_reactions = [x.button for x in extra_options]
        reactions.extend(extra_reactions)

    while True:
        try:
            reaction, user = await bot.wait_for_reaction(reactions,
                                                         message=base_message,
                                                         timeout=timeout,
                                                         user=author)
        except asyncio.TimeoutError:
            for r in reactions:
                await bot.remove_reaction(base_message, r, bot.user)
            break
        except Exception as e:
            await bot.send_message(discord.User(id=global_util.OWNER_ID), 'Paginator Except: {}'.format(e))

        if not reaction:
            if (time.time() - entry_time) > (timeout - 10):
                break
            else:
                continue

        entry_time = time.time()

        recent_page = current_page

        choice = str(reaction.emoji)
        if choice == '⏮':
            current_page = 1
        elif choice == '⏪':
            current_page -= 1
            if current_page < 0:
                current_page = len(pages) - 1
        elif choice == '⏩':
            current_page += 1
            if current_page >= len(pages):
                current_page = 0
        elif choice == '⏭':
            current_page = len(pages) - 1
        elif choice == '❌':
            await bot.delete_message(base_message)
            break

        if current_page != recent_page:
            base_message = await bot.edit_message(base_message, embed=current_page)

        if choice in extra_reactions:
            field = [x.content for x in extra_options if x.button == choice][0]
            field  # type:EmbedField

            em = pages.base_embed()
            em.add_field(name=field.name,
                         value=field.value,
                         inline=field.inline)

            await bot.edit_message(base_message, embed=em)
