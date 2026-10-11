"""Question and passage templates per relation.

Several templates per relation, so results can be broken down by phrasing (to catch template artifacts).
"{s}" is the subject, "{o}" the object.
"""

RELATIONS: dict[str, dict] = {
    "capital": {
        "wikidata": "P36",
        "type": "city",
        "questions": ["What is the capital of {s}?", "Which city is the capital of {s}?"],
        "passages": [
            "{o} is the capital of {s}. It is the seat of the national government.",
            "The capital city of {s} is {o}, which is also its largest administrative centre.",
            "Since its designation as the capital, {o} has served as the political heart of {s}.",
        ],
    },
    "currency": {
        "wikidata": "P38",
        "type": "currency",
        "questions": ["What is the currency of {s}?", "Which currency is used in {s}?"],
        "passages": [
            "The official currency of {s} is the {o}.",
            "In {s}, prices are quoted in the {o}, the country's legal tender.",
        ],
    },
    "author": {
        "wikidata": "P50",
        "type": "person",
        "questions": ["Who wrote {s}?", "Who is the author of {s}?"],
        "passages": [
            "{s} was written by {o}.",
            "{o} is the author of {s}, one of the works they are best known for.",
        ],
    },
    "official_language": {
        "wikidata": "P37",
        "type": "language",
        "questions": ["What is the official language of {s}?"],
        "passages": [
            "The official language of {s} is {o}.",
            "{o} is the official language used by the government of {s}.",
        ],
    },
    "place_of_birth": {
        "wikidata": "P19",
        "type": "city",
        "questions": ["Where was {s} born?", "In which city was {s} born?"],
        "passages": [
            "{s} was born in {o}.",
            "Born in {o}, {s} spent their early years there before becoming known for their work.",
        ],
    },
    "country": {
        "wikidata": "P17",
        "type": "country",
        "questions": ["In which country is {s}?", "{s} is located in which country?"],
        "passages": [
            "{s} is a city in {o}.",
            "{s} is located in {o}.",
        ],
    },
}

# Question templates for multi-hop chains (C4). "{s}" is the chain's starting entity (a book).
MULTIHOP_QUESTIONS = {
    2: ["In which city was the author of {s} born?", "Where was the person who wrote {s} born?"],
    3: ["In which country was the author of {s} born?", "The author of {s} was born in which country?"],
}

# Country-style names that need a definite article in running text ("the capital of the United Kingdom").
_ARTICLE_EXACT = {"Netherlands", "Bahamas", "Philippines", "Maldives", "Comoros", "Gambia", "Vatican City",
                  "Seychelles"}
_ARTICLE_PREFIX = ("United ", "Republic of", "Democratic Republic", "Kingdom of", "Federated States", "State of ")
_ARTICLE_SUFFIX = (" Republic", " Islands", " Emirates")


def with_article(name: str) -> str:
    """Add 'the' to names like 'United Kingdom' or 'Czech Republic'. Leaves other names unchanged."""
    if name.lower().startswith("the "):
        return name
    if name in _ARTICLE_EXACT or name.startswith(_ARTICLE_PREFIX) or name.endswith(_ARTICLE_SUFFIX):
        return "the " + name
    return name


def fill(template: str, s: str, o: str = "") -> str:
    """Fill a question/passage template, adding articles where needed and capitalising the first letter."""
    text = template.format(s=with_article(s), o=with_article(o))
    return text[0].upper() + text[1:] if text else text
