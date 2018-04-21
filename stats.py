# stats module by CantSayIHave
# created 2018/2/9
#
# Keeps stats for various bot features


import discord
from discord.ext import commands
from discordbot import DiscordBot


class Stats:
    def __init__(self, bot: DiscordBot):
        self.bot = bot


async def load_stats():
    pass


def setup(bot):
    return Stats(bot)