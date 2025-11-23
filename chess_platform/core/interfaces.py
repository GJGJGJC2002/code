from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .patterns import Subject, PieceType, PieceFactory

class Board(Subject):
    """
    棋盘基类
    继承 Subject 是为了让 UI (Observer) 能监听到棋盘变化
    """
    def __init__(self, size: int):
        super().__init__()
        self.size = size
        # 使用 2D 列表存储棋子引用 (Flyweight)
        # None 表示空位
        self._grid: List[List[Optional[PieceType]]] = [[None for _ in range(size)] for _ in range(size)]
        self.last_move: Optional[Tuple[int, int]] = None

    def is_valid_pos(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def get_piece(self, x: int, y: int) -> Optional[PieceType]:
        if not self.is_valid_pos(x, y):
            return None
        return self._grid[x][y]

    def place_piece(self, x: int, y: int, piece: PieceType):
        if self.is_valid_pos(x, y):
            self._grid[x][y] = piece
            self.last_move = (x, y)
            # 通知观察者(UI)更新
            self.notify(event="place", pos=(x, y), piece=piece)

    def remove_piece(self, x: int, y: int):
        if self.is_valid_pos(x, y):
            old_piece = self._grid[x][y]
            self._grid[x][y] = None
            self.notify(event="remove", pos=(x, y), piece=old_piece)

    def clear(self):
        self._grid = [[None for _ in range(self.size)] for _ in range(self.size)]
        self.last_move = None
        self.notify(event="clear")
    
    def get_snapshot(self) -> dict:
        """用于 Memento 模式，获取当前状态快照"""
        # 只需要保存有棋子的位置，或者直接保存grid的副本
        # 这里为了简单直接保存grid的这种结构(实际应该更轻量化)
        return {
            "size": self.size,
            "grid": [row[:] for row in self._grid],
            "last_move": self.last_move
        }

    def restore_snapshot(self, snapshot: dict):
        """从快照恢复"""
        self.size = snapshot["size"]
        self._grid = snapshot["grid"]
        self.last_move = snapshot["last_move"]
        self.notify(event="restore")


class RuleStrategy(ABC):
    """
    策略模式接口：定义游戏规则
    不同的游戏(五子棋/围棋)实现不同的规则
    """
    @abstractmethod
    def is_valid_move(self, board: Board, x: int, y: int, player_piece: PieceType) -> Tuple[bool, str]:
        """返回 (是否合法, 错误信息)"""
        pass

    @abstractmethod
    def check_win(self, board: Board, last_x: int, last_y: int) -> Optional[str]:
        """
        检查胜负
        返回: None(未分胜负), "Draw"(平局), 或 获胜者颜色名
        """
        pass
        
    @abstractmethod
    def post_move_action(self, board: Board, x: int, y: int, player_piece: PieceType) -> List[Tuple[int, int]]:
        """
        落子后的额外动作 (例如围棋提子)
        返回被移除的棋子坐标列表
        """
        pass


class Game(ABC):
    """游戏基类"""
    def __init__(self, size: int, rule: RuleStrategy):
        self.board = Board(size)
        self.rule = rule
        self.current_player_idx = 0
        # 定义玩家 (黑先白后)
        self.players = [
            PieceFactory.get_piece_type("Black", "X"),
            PieceFactory.get_piece_type("White", "O")
        ]
        self.is_game_over = False
        self.winner = None

    @property
    def current_player(self) -> PieceType:
        return self.players[self.current_player_idx]

    def switch_player(self):
        self.current_player_idx = 1 - self.current_player_idx

    @abstractmethod
    def start(self):
        pass

