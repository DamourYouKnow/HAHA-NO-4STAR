import math
from operator import itemgetter
from posixpath import basename
from urllib.parse import urlsplit
from copy import deepcopy

from discord import User
from discord.ext import commands

from bot import HahaNo4Star
from core.argument_parser import parse_arguments
from core.checks import check_mongo
from core.image_generator import create_image, get_one_img, member_img_path

PAGE_SIZE = 16
ROWS = 4
SORTS = [
    'id',
    'name',
    'attribute',
    'rarity',
    'school_year',
    'date',
    'band',
    'newest',
    'instrument'
]

# Dictionary mapping user ids to last used album arguments
_last_user_args = {}


class Album:
    """
    A class to hold all album commands.
    """

    def __init__(self, bot: HahaNo4Star):
        self.bot = bot

    async def __send_error_msg(self, ctx, content):
        await self.bot.send_message(
            ctx.message.channel,
            f'<@{ctx.message.author.id }> ' + content
        )

    async def __handle_album_result(self, ctx, album_size, image):
        if not image:
            await self.__send_error_msg(ctx, 'No matching cards found.')
            _last_user_args[ctx.message.author.id] = _get_new_user_args()
        else:
            page = _last_user_args[ctx.message.author.id]["page"]
            max_page = int(math.ceil(album_size / PAGE_SIZE))
            msg = (f'<@{ctx.message.author.id}> Page {page+1} of {max_page}. '
                   f'`$help album` for more info.')
            await self.bot.upload(image, filename='a.png', content=msg)

    async def __handle_view_result(self, ctx, image):
        if not image:
            msg = ('Could not find card in album. '
                   f'`$help view` for more info.')
            await self.__send_error_msg(ctx, msg)
        else:
            msg = f'<@{ctx.message.author.id}>'
            await self.bot.upload(image, filename='c.png', content=msg)

    async def __handle_train_result(self, ctx, image):
        if not image:
            msg = ('Could not train card. '
                   f'`$help train` for more info.')
            await self.__send_error_msg(ctx, msg)
        else:
            msg = f'<@{ctx.message.author.id}>'
            await self.bot.upload(image, filename='c.png', content=msg)

    @commands.command(pass_context=True, aliases=['a'])
    @commands.cooldown(rate=3, per=2.5, type=commands.BucketType.user)
    @commands.check(check_mongo)
    async def album(self, ctx, *args: str):
        """
        Description: |
            View your album.

            Your selected filters and sort will be remembered.
            To clear filters, provide the argument <all>.
            For example, !album afterglow third year 4star or !album all

        Optional Arguments: |
            Page (1, 2, 3, ...)
            Sort (id, rarity, newest, attribute, year, band, date)
            Band name (Poppin' Party, Afterglow, ...)
            Member first name (Kasumi, Ran, ...)
            Attribute (powerful, pure, cool, happy)
            Year (first, second, third)
            Rarity (1star, 2star, 3star, 4star)
        """
        user = ctx.message.author
        album = await self.bot.db.users.get_user_album(user.id, True)
        _parse_album_arguments(self.bot, args, user)
        album = _apply_filter(album, user)
        album = _apply_sort(album, user)
        filtered_album_size = len(album)
        album = _splice_page(album, user)

        image = await create_image(
            self.bot.session_manager, album, ROWS, True, True
        ) if len(album) > 0 else None
        await self.__handle_album_result(ctx, filtered_album_size, image)

    @commands.command(pass_context=True, aliases=['v'])
    @commands.cooldown(rate=3, per=2.5, type=commands.BucketType.user)
    @commands.check(check_mongo)
    async def view(self, ctx, *args: str):
        """
        Description: |
            View a card from your album.
            For example, !view 1200 or !view 1200 trained.

        Optional Arguments: |
            Card ID (This is the left number of a card in your album)
            Trained (Shows the trained copy if it exist in your album)
        """
        user = ctx.message.author
        trained = False
        card_id = 0

        # Parse args for card id and idolized.
        for arg in args:
            if _is_number(arg):
                card_id = int(arg)
            if arg in ['trained', 't']:
                trained = True

        image = None
        card = await self.bot.db.users.get_card_from_album(user.id, card_id)

        if card:
            img_url = None
            if trained and card['art_trained']:
                img_url = card['art_trained']
            else:
                img_url = card['art']

            if img_url:
                fname = basename(urlsplit(img_url).path)
                image_path = member_img_path.joinpath(str(fname))
                image = await get_one_img(
                        img_url, image_path, self.bot.session_manager)

        await self.__handle_view_result(ctx, image)


def _apply_filter(album: list, user: User):
    """
    Applys a user's filters to a card album, removing anything not matching
        the filter.

    :param album: Album being filtered.
    :param user: User who requested the album.

    :return: Filtered album.
    """
    filters = _last_user_args[user.id]['filters']

    for filter_type in filters:
        filter_values = filters[filter_type]

        if not filter_values:
            continue

        # Looping backwards since we are removing elements
        for i in range(len(album) - 1, -1, -1):
            # Generic case
            print(filter_type)
            print(filter_values)
            print(album[i])
            if album[i][filter_type] not in filter_values:
                album.pop(i)

    return album


def _apply_sort(album: list, user: User) -> list:
    """
    Applys a user's sort to a card album.

    :param album: Album being sorted.
    :param user: User who requested the album.

    :return: Sorted album.
    """
    sort = _last_user_args[user.id]['sort']

    # FIXME This var doesn't seem to have any use.
    order = _last_user_args[user.id]['order']

    if not sort:
        return album
    if sort == 'date':
        sort = 'release_date'
    if sort == 'band':
        sort = 'i_band'
    if sort == 'newest':
        sort = 'time_aquired'
    if sort == 'attribute':
        sort = 'i_attribute'
    if sort == 'rarity':
        sort = 'i_rarity'

    sort_descending = sort in [
        'i_rarity',
        'i_attribute',
        'release_date',
        'time_aquired',
        'i_band'
    ]

    return sorted(album, key=itemgetter(sort, 'id'), reverse=sort_descending)


def _splice_page(album: list, user: User) -> list:
    """
    Splices a user's last requested page out of their album.

    :param album: Album being spliced
    :param user: User who requested the album.

    :return: Spliced album.
    """
    page = _last_user_args[user.id]['page']
    max_page = int(math.ceil(len(album) / PAGE_SIZE)) - 1

    if page > max_page:
        page = max_page
    if page < 0:
        page = 0
    _last_user_args[user.id]['page'] = page

    start = PAGE_SIZE * page
    end = (PAGE_SIZE * page) + PAGE_SIZE
    return album[start:end]


def _parse_album_arguments(bot, args: tuple, user: User):
    """
    Parse arguments to get how an album will be sorted and filtered. The parsed
        arguments are stored in the user's last used arguments dictionary.

    :param args: Tuple of arguments.
    :param user: User who requested the album.
    """
    # Add user to last used argument dictionary if they don't already exist.
    if user.id not in _last_user_args:
        _last_user_args[user.id] = _get_new_user_args()

    # Get values of user's last album preview.
    page = _last_user_args[user.id]['page']
    filters = _last_user_args[user.id]['filters']
    sort = _last_user_args[user.id]['sort']

    # FIXME This var doesn't seem to have any use.
    order = _last_user_args[user.id]['order']

    new_filters = parse_arguments(bot, args, True)
    if _has_filter(new_filters):
        filters = new_filters

    # Parse other arguments
    for arg in args:
        arg = arg.lower()

        # Reset filter if "all" is given
        if arg == 'all':
            filters = {
                'name': [],
                'i_band': [],
                'i_school_year': [],
                'i_attribute': [],
                'i_rarity': [],
                'instrument': []
            }

        # Parse sort
        if arg in SORTS:
            sort = arg
            page = 0

        # Parse sort order
        if arg in ('+', '-'):
            # FIXME This var doesn't seem to have any use.
            order = arg

        # Parse if page number
        if _is_number(arg):
            page = int(arg) - 1

        _last_user_args[user.id]['page'] = page
        _last_user_args[user.id]['filters'] = filters
        _last_user_args[user.id]['sort'] = sort


def _get_new_user_args():
    args = {
        'page': 0,
        'filters': {
            'name': [],
            'i_band': [],
            'i_school_year': [],
            'i_attribute': [],
            'i_rarity': [],
            'instrument': []
        },
        'sort': None,
        'order': None  # Sort by ID if None
    }
    return args


def _has_filter(filters: dict) -> bool:
    """
    Checks if a filter dictionary has any active filters.

    :param filters: Target filter dictionary.

    :return: True if target has filters, otherwise False.
    """
    return any(filters.values())


def _is_number(string: str) -> bool:
    """
    Checks if a string is a valid number.

    :param string: String being tested.

    :return: True if valid number, otherwise false.
    """
    try:
        int(string)
        return True
    except ValueError:
        return False
