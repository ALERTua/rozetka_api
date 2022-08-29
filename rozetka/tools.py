import re


def title_clean(title):
    """
    Cleans
    Ноутбуки - ROZETKA | Купити ноутбук в Києві: ціна, відгуки, продаж, вибір ноутбуків в Україні'
    to
    Ноутбуки
    """
    if not title:
        return ''

    tails = [
        ' - ROZETKA',
        ' – в інтернет-магазині ROZETKA',
    ]
    output = title
    for tail in tails:
        split = re.split(tail, output)
        # noinspection PyUnresolvedReferences
        output = split[0].strip()
    return output


def ints_from_str(str_):
    blocks = str_.split()
    output = []
    for block in blocks:
        # noinspection PyBroadException
        try:
            output.append(int(block))
        except:  # noqa: E722
            pass

    return output


def floats_from_str(str_):
    blocks = str_.split()
    floats = []
    for block in blocks:
        # noinspection PyBroadException
        try:
            floats.append(float(block))
        except:  # noqa: E722
            pass

    return floats


def str_to_price(price_str):
    if not price_str:
        return

    price_str = price_str.replace("₴", "")
    price_str = price_str.split()
    price_str = "".join(price_str)
    return int(price_str)


def parse_rating(rating_str):
    if not rating_str:
        return

    floats = floats_from_str(rating_str)
    if len(floats) == 2:
        rating_value, rating_max = floats
        return rating_value / rating_max


def parse_reviews(reviews_str):
    if not reviews_str:
        return

    floats = floats_from_str(reviews_str)
    if floats:
        return int(floats[0])
