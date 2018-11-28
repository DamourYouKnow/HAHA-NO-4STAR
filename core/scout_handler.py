from collections import namedtuple
from posixpath import basename
from random import randint, shuffle, uniform
from time import time
from urllib.parse import urlsplit

from discord import User

from bot import HahaNo4Star
from core.argument_parser import parse_arguments
from core.image_generator import create_image, get_one_img, \
    member_img_path

RATES = {
    "star": {1: 0.00, 2: 0.885, 3: 0.085, 4: 0.03},
}


class PlayImage(namedtuple('playImage', ('bytes', 'name'))):
    __slots__ = ()


class PlayHandler:
    """
    Provides scouting functionality for bot.
    """
    __slots__ = ('results', '_bot', '_user', '_box', '_count',
                 '_guaranteed_sr', '_args')

    def __init__(self, bot: HahaNo4Star, user: User,
                 box: str = "honour", count: int = 1,
                 guaranteed_sr: bool = False, args: tuple = ()):
        """
        Constructor for a Play.
        :param session_manager: the SessionManager.
        :param user: User requesting play.
        :param box: Box to play in (star).
        :param count: Number of cards in play.
        :param guaranteed_sr: Whether the play will roll at least one SR.
        :param args: Play command arguments
        """
        self.results = []
        self._bot = bot
        self._user = user
        self._box = box
        self._count = count
        self._guaranteed_sr = guaranteed_sr
        self._args = parse_arguments(self._bot, args, True)

    async def do_scout(self):
        return await self._handle_multiple_play()

    async def _handle_multiple_play(self):
        """
        Handles a play with multiple cards

        :return: Path of play image
        """
        cards = await self._play_cards()

        if len(cards) != self._count:
            self.results = []
            return None

        fname = f'{int(time())}{randint(0, 100)}.png'
        _bytes = await create_image(self._bot.session_manager, cards, 2)
        return PlayImage(_bytes, fname)

    async def _handle_solo_play(self):
        """
        Handles a solo scout

        :return: Path of scout image
        """
        card = await self._play_cards()

        # Send error message if no card was returned
        if not card:
            self.results = []
            return None

        card = card[0]

        url = card["art"]

        fname = basename(urlsplit(url).path)
        image_path = member_img_path.joinpath(fname)
        bytes_ = await get_one_img(
            url, image_path, self._bot.session_manager)
        return PlayImage(bytes_, fname)

    async def _play_cards(self) -> list:
        """
        Plays a specified number of cards

        :return: cards played
        """
        rarities = []

        if self._guaranteed_sr:
            for r in range(self._count - 1):
                rarities.append(self._roll_rarity())

            if rarities.count(1) + rarities.count(2) == self._count - 1:
                rarities.append(self._roll_rarity(True))
            else:
                rarities.append(self._roll_rarity())

        else:
            for r in range(self._count):
                rarities.append(self._roll_rarity())

        results = []

        for rarity in RATES[self._box].keys():
            if rarities.count(rarity) > 0:
                play = await self._play_request(
                    rarities.count(rarity), rarity
                )

                results += _get_adjusted_play(
                    play, rarities.count(rarity)
                )

        self.results = results
        shuffle(results)
        return results

    async def _play_request(self, count: int, rarity: int) -> dict:
        """
        Plays a specified number of cards of a given rarity

        :param rarity: Rarity of all cards in play

        :return: Cards played
        """
        if count == 0:
            return []

        params = {'i_rarity': rarity,}

        for arg_type, arg_values in self._args.items():
            if not arg_values:
                continue

            val = arg_values

            # Comma seperated strings need to use $in.
            if len(arg_values) > 0:
                val = {'$in': arg_values}

            if arg_type == "i_band":
                params['member.i_band'] = val
            elif arg_type == "name":
                params['member.name'] = val
            elif arg_type == "i_school_year":
                params['member.i_school_year'] = val
            elif arg_type == "i_attribute":
                params['i_attribute'] = val
            elif arg_type == "instrument":
                params['member.instrument'] = val

        # Get and return response
        return await self._bot.db.cards.get_random_cards(params, count)

    def _roll_rarity(self, guaranteed_sr: bool = False) -> str:
        """
        Generates a random rarity based on the defined scouting rates

        :param guaranteed_sr: Whether roll should be an SR

        :return: rarity represented as a int (1, 2, 3, 4)
        """
        roll = uniform(0, 1)

        required_roll = RATES[self._box][4]
        if roll < required_roll:
            return 4

        required_roll = RATES[self._box][3] + RATES[self._box][4]
        if roll < required_roll:
            return 3

        required_roll = RATES[self._box][2] + RATES[self._box][3]
        required_roll += RATES[self._box][4]
        if roll < required_roll:
            if guaranteed_sr:
                return 3
            else:
                return 2

        else:
            return 1

def _get_adjusted_play(play: list, required_count: int) -> list:
    """
    Adjusts a pull of a single rarity by checking if a card should flip to
    a similar one and by duplicating random cards in the play if there were
    not enough played.
    :param play: List representing the play.
        All these cards will have the same rarity.
    :param required_count: The number of cards that need to be played.
    :return: Adjusted list of cards played.
    """
    # Add missing cards to play by duplicating random cards already present
    current_count = len(play)

    # Something bad happened, return an empty list
    if current_count == 0:
        return []

    pool_size = current_count
    while current_count < required_count:
        play.append(
            play[randint(0, pool_size - 1)]
        )
        current_count += 1

    # Traverse scout and roll for flips
    for card_index in range(len(play) - 1):
        # for each card there is a (1 / total cards)
        # chance that we should dupe
        # the previous card
        roll = uniform(0, 1)
        if roll < 1 / len(play):
            play[card_index] = play[card_index + 1]

    return play