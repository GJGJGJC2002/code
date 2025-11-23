from typing import List, Optional
from src.core.enums import PieceType

class Board:
    """
    棋盘类：管理棋盘状态
    """
    def __init__(self, size: int = 15):
        self._size = size
        # 内部使用二维数组存储 PieceType
        # 0: Empty, 1: Black, 2: White
        self._grid = [[PieceType.NONE for _ in range(size)] for _ in range(size)]
        self._last_move = None  # (x, y) 记录最后一步

    @property
    def size(self) -> int:
        return self._size

    @property
    def grid(self) -> List[List[PieceType]]:
        return self._grid
    
    @property
    def last_move(self):
        return self._last_move

    def is_valid_pos(self, x: int, y: int) -> bool:
        return 0 <= x < self._size and 0 <= y < self._size

    def get_piece_type(self, x: int, y: int) -> PieceType:
        if not self.is_valid_pos(x, y):
            return PieceType.NONE
        return self._grid[x][y]

    def place_piece(self, x: int, y: int, piece_type: PieceType) -> bool:
        if not self.is_valid_pos(x, y):
            return False
        self._grid[x][y] = piece_type
        self._last_move = (x, y)
        return True

    def remove_piece(self, x: int, y: int):
        if self.is_valid_pos(x, y):
            self._grid[x][y] = PieceType.NONE

    def clear(self):
        for i in range(self._size):
            for j in range(self._size):
                self._grid[i][j] = PieceType.NONE
        self._last_move = None

    # Memento Pattern Support
    def get_state(self):
        # Return deep copy
        return [row[:] for row in self._grid]

    def set_state(self, grid_state):
        self._grid = [row[:] for row in grid_state]

