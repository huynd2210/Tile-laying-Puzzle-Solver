from enum import Enum


class PieceUsagePolicy(Enum):
    EXACTLY_ONE = "exactly_one"
    AT_MOST_ONE = "at_most_one"