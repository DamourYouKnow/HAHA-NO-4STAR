ALIASES = {
    'name': {
        'misaki': 'Michelle',
        'rimirin': 'Rimi Ushigome',
        'choco': 'Rimi Ushigome',
        'cornet': 'Rimi Ushigome',
        'o-tao': 'Tae Hanazono',
        'tsugu': 'Tsugumi Hazawa',
        'tsugurific': 'Tsugumi Hazawa',
        'rinrin': 'Rinko Shirokane',
        'bushido': 'Eve Wakamiya',
        'fleeting': 'Kaoru Seta',
        'boppin': 'Hina Hikawa',
        "boppin'": 'Hina Hikawa',
        'combo': 'Hina Hikawa',
        'fc': 'Hina Hikawa',
        'fuee': 'Kanon Matsubara',
        'bread': 'Saaya Yamabuki',
        'saya': 'Saaya Yamabuki',
        'koko': 'Kokoro Tsurumaki',
        'fortnite': 'Kokoro Tsurumaki',
        'hoh': 'Himari Uehara',
        'gamer': 'Ako Udagawa',
        'tatoe': 'Yukina Minato'
    },
    'i_band': {
        'poppin': "Poppin' Party",
        "poppin'": "Poppin' Party",
        "popping'": "Poppin' Party",
        'party': "Poppin' Party",
        "afterglow": "Afterglow",
        "hello": "Hello, Happy World!",
        "world": "Hello, Happy World!",
        'hhw': "Hello, Happy World!",
        'pastel': 'Pastel*Palettes',
        'palettes': 'Pastel*Palettes',
        'pastel*palettes': 'Pastel*Palettes',
        'roselia': 'Roselia'
    },
    'i_rarity': {
        '1star': 1,
        '2star': 2,
        '3star': 3,
        '4star': 4
    },
    'instrument': {
        'vocals': 'Guitar/Vocals',
        'vocalist': 'Guitar/Vocals',
        'guitarist': 'Guitar',
        'drummer': 'Drums',
        'keytarist': 'Keytar',
        'keyboardist': 'Guitar/Vocals',
        'bassist': 'Bass'
    }
}


def parse_arguments(bot, args: tuple, 
                    allow_unsupported_lists: bool = False) -> dict:
    """
    Parse all user arguments

    :param args: Tuple of all arguments
    :param allow_unsupported_lists: Whether parameters that the Bang Dream API
        does not allow multiple values of are reduced.

    :return: A list of tuples of (arg_type, arg_value)
    """
    parsed_args = {
        'name': [],
        'i_band': [],
        'i_school_year': [],
        'i_attribute': [],
        'i_rarity': [],
        'instrument': []
    }

    for arg in args:
        for arg_type, arg_value in _parse_argument(bot, arg):
            parsed_args[arg_type].append(arg_value)

    # Covert all values to sets and back to lists to remove duplicates.
    for arg_type in parsed_args:
        parsed_args[arg_type] = list(set(parsed_args[arg_type]))

    return parsed_args


def _parse_argument(bot, arg: str) -> list:
    """
    Parse user argument.

    :param arg: An argument.

    :return: List of tuples of (arg_type, arg_value)
    """
    arg = arg.lower()
    found_args = []

    # Check for unit and idol names by alias
    for key, val in ALIASES.items():
        search_result = val.get(arg, None)
        if search_result:
            return [(key, search_result)]

    # Check for names/surnames
    for full_name in bot.member_names:
        name_split = full_name.split(' ')
        if arg.title() in name_split:
            found_args.append(('name', full_name))

    if found_args:
        return found_args

    # Check for years
    if arg in ('first', 'second', 'third'):
        return [('i_school_year', arg.title())]

    # Check for attribute
    if arg in ('cool', 'happy', 'pure'):
        return [('i_attribute', arg.title())]
    if arg in ('power, powerful'):
        return [('i_attribute', 'Power')]

    # Check for instrument
    instruments = [
        'dj', 'drums', 'guitar', 'guitar/vocals', 'keytar', 'bass', 'keyboard'
    ]
    if arg in instruments:
        return [('instrument', arg.title())]

    # Check for rarity
    if arg.lower() in ALIASES['i_rarity'].items():
        return [('i_rarity', ALIASES['i_rarity'][arg.lower()])]

    return []
