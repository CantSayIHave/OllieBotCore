# paginator module by Sierra
# created 2018/3/8
#
# paginates through an iterable of embed fields

import random

import asyncio
import discord
import time

from util.containers import EmbedField
from util import global_util


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
                   page_limit=10,
                   timeout=60,
                   extra_options: list = None,
                   icon=None,
                   color=None):

    """Breaks a list of options into numbered pages for display in `_paginator`

        Parameters
        ----------
        items : collections.Iterable
            iterable of items to paginate
        title : str
            title for each page
        bot : discordbot.DiscordBot
            discord bot
        destination : discord.Channel
            channel to send pagination to
        author : discord.User
            user to take reactions from
        page_limit : int
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

    entry_time = time.time()  # used for listening failsafe

    items = list(items)  # for generators and other iterables

    limit = len(items) / page_limit
    if int(limit) != limit:
        limit = int(limit + 1)

    limit = int(limit)  # remove floating point

    def base_embed(page_num: int) -> discord.Embed:
        """Builds base embed - title bar, color, icon, page number

        Parameters
        ----------
        page_num : int
            number of page to build. uses direct display range of [1 - end]

        Returns
        -------
        :class:`discord.Embed`
            base embed

        """

        nonlocal color, title, icon, limit

        if not color:
            color = random.randint(0, 0xffffff)

        em = discord.Embed(title='───────────────────────', color=color)
        if icon:
            em.set_author(name="{} - {}/{}".format(title, page_num, limit), icon_url=icon)
        else:
            em.set_author(name="{} - {}/{}".format(title, page_num, limit))

        return em

    def get_page(page_num: int, args: list) -> discord.Embed:
        """Builds a page for paginator

        Parameters
        ----------
        page_num : int
            number of page to build. uses direct display range of [1 - end]
        args : list
            a list of :class:`EmbedField` to build embed fields for display

        Returns
        -------
        :class:`discord.Embed`
            complete page

        """
        nonlocal limit, base_embed

        if page_num < 1:
            page_num = 1
        if page_num > limit:
            page_num = limit

        l_start = int(page_limit * (page_num - 1))
        if len(args) > (l_start + page_limit):
            page_list = args[l_start:l_start + page_limit]
        else:
            page_list = args[l_start:len(args)]

        em = base_embed(page_num)

        for field in page_list:  # type:EmbedField
            em.add_field(name=field.name,
                         value=field.value,
                         inline=field.inline)

        return em

    # Verify `extra_options` contains only :class:`Option`
    if extra_options:
        for o in extra_options:
            if type(o) is not Option:
                raise ValueError("Expected type `Option` in `extra_options`")

    current_page = 1

    em = get_page(current_page, items)

    base_message = await bot.send_message(destination, embed=em)
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
            if current_page < 1:
                current_page = limit
        elif choice == '⏩':
            current_page += 1
            if current_page > limit:
                current_page = 1
        elif choice == '⏭':
            current_page = limit
        elif choice == '❌':
            await bot.delete_message(base_message)
            break

        if current_page != recent_page:
            em = get_page(current_page, items)
            base_message = await bot.edit_message(base_message, embed=em)

        if choice in extra_reactions:
            field = [x.content for x in extra_options if x.button == choice][0]
            field  # type:EmbedField

            em = base_embed(current_page)
            em.add_field(name=field.name,
                         value=field.value,
                         inline=field.inline)

            await bot.edit_message(base_message, embed=em)
