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
}
