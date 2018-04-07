from discord.ext import commands

from bot import HahaNo4Star
from core.scout_handler import PlayHandler, PlayImage
from core.checks import check_mongo


class Play:
    """
    A class to hold all Play commands.
    """

    def __init__(self, bot: HahaNo4Star):
        self.bot = bot

    async def __handle_result(self, ctx, results, image: PlayImage):
        """
        Handle a play result.
        :param ctx: the context.
        :param results: the play results.
        :param image: play image result.
        """
        if not image:
            msg = (f'<@{ctx.message.author.id}> '
                   f'A transmission error occured. No cards found!')
            await self.bot.say(msg)
            return
        await self.bot.upload(
            image.bytes, filename=image.name,
            content=f'<@{ctx.message.author.id}>'
        )

        if not await self.bot.db.users.find_user(ctx.message.author.id):
            await self.bot.db.users.insert_user(ctx.message.author.id)
        await self.bot.db.users.add_to_user_album(
                ctx.message.author.id, results)

    @commands.command(pass_context=True, aliases=['1play'])
    @commands.cooldown(rate=5, per=2.5, type=commands.BucketType.user)
    @commands.check(check_mongo)
    async def play1(self, ctx, *args: str):
        """
        Description: |
            Solo play.

            **Rates:** 2star: 88.5%, 3star: 8.5%,4 star: 3.0%
        Optional Arguments: |
            Main unit name (Poppin' Party, Afterglow)
            Idol first name (Kasumi, Ran, ...)
            Attribute (powerful, pure, cool, happy)
            Year (first, second, third)
        """
        play = PlayHandler(
            self.bot, ctx.message.author, 'play', 1, False, args)
        image = await play.do_scout()
        await self.__handle_result(ctx, play.results, image)

    @commands.command(pass_context=True, aliases=['play10'])
    @commands.cooldown(rate=3, per=2.5, type=commands.BucketType.user)
    @commands.check(check_mongo)
    async def play10(self, ctx, *args: str):
        """
        Description: |
            10 play with guaranteed 3 Star.

            **Rates:** 2star: 88.5%, 3star: 8.5%, 4star: 3.0%
        Optional Arguments: |
            Main unit name (Poppin' Party, Afterglow)
            Idol first name (Kasumi, Ran, ...)
            Attribute (powerful, pure, cool, happy)
            Year (first, second, third)
        """
        play = PlayHandler(
            self.bot, ctx.message.author, 'play', 10, True, args)
        image = await play.do_scout()
        await self.__handle_result(ctx, play.results, image)
