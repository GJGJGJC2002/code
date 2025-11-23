from enum import Enum

class PieceType(Enum):
    NONE = 0
    BLACK = 1
    WHITE = 2

class GameType(Enum):
    GOBANG = 1  # 五子棋
    GO = 2      # 围棋

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    ENDED = 2

