from typing import Tuple, List, Optional, Set
from chess_platform.core.interfaces import RuleStrategy, Board
from chess_platform.core.patterns import PieceType

class GomokuRule(RuleStrategy):
    def is_valid_move(self, board: Board, x: int, y: int, player_piece: PieceType) -> Tuple[bool, str]:
        if not board.is_valid_pos(x, y):
            return False, "Position out of bounds"
        if board.get_piece(x, y) is not None:
            return False, "Position already occupied"
        return True, ""

    def post_move_action(self, board: Board, x: int, y: int, player_piece: PieceType) -> List[Tuple[int, int]]:
        # 五子棋落子后没有提子动作
        return []

    def check_win(self, board: Board, last_x: int, last_y: int) -> Optional[str]:
        if last_x is None or last_y is None:
            return None
            
        piece = board.get_piece(last_x, last_y)
        if not piece:
            return None

        # 四个方向：横、竖、左斜、右斜
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        
        for dx, dy in directions:
            count = 1
            # 正向查找
            cx, cy = last_x + dx, last_y + dy
            while board.is_valid_pos(cx, cy) and board.get_piece(cx, cy) == piece:
                count += 1
                cx += dx
                cy += dy
            # 反向查找
            cx, cy = last_x - dx, last_y - dy
            while board.is_valid_pos(cx, cy) and board.get_piece(cx, cy) == piece:
                count += 1
                cx -= dx
                cy -= dy
            
            if count >= 5:
                return piece.color_name
        
        # 检查平局 (满盘)
        is_full = True
        for r in range(board.size):
            for c in range(board.size):
                if board.get_piece(r, c) is None:
                    is_full = False
                    break
        if is_full:
            return "Draw"
            
        return None


class GoRule(RuleStrategy):
    def is_valid_move(self, board: Board, x: int, y: int, player_piece: PieceType) -> Tuple[bool, str]:
        # 1. 基本位置检查
        if not board.is_valid_pos(x, y):
            return False, "Position out of bounds"
        if board.get_piece(x, y) is not None:
            return False, "Position already occupied"
        
        # 2. 围棋特殊规则：自杀手检测 (简单版：如果落子后没有气且不能提对方子，则禁入)
        # 注意：完整的规则比较复杂，需要模拟落子后是否提子。
        # 这里为了性能，我们可以在 post_move_action 之后如果发现自己没气且没提子，则回滚（或者在 Command 中处理）。
        # 简单的预判：
        # 模拟落子
        board._grid[x][y] = player_piece # 临时落子
        captured = self._get_captured_stones(board, x, y, player_piece)
        liberties = self._count_liberties(board, x, y)
        board._grid[x][y] = None # 恢复

        # 如果落子后没有气，且没有提掉对方的子 -> 禁止 (自杀)
        if liberties == 0 and len(captured) == 0:
             return False, "Suicide move is forbidden"

        return True, ""

    def post_move_action(self, board: Board, x: int, y: int, player_piece: PieceType) -> List[Tuple[int, int]]:
        """
        围棋落子后，检查四周是否有对方棋子气尽（被提）
        """
        opponent_stones_to_remove = self._get_captured_stones(board, x, y, player_piece)
        
        # 执行提子
        removed_positions = []
        for rx, ry in opponent_stones_to_remove:
            board.remove_piece(rx, ry)
            removed_positions.append((rx, ry))
            
        return removed_positions

    def _get_captured_stones(self, board: Board, x: int, y: int, player_piece: PieceType) -> Set[Tuple[int, int]]:
        """
        检查 (x,y) 落子后，周围对手的死子
        """
        directions = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        captured = set()
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if board.is_valid_pos(nx, ny):
                neighbor_piece = board.get_piece(nx, ny)
                # 如果是对方棋子，检查那一块棋是否有气
                if neighbor_piece and neighbor_piece != player_piece:
                    if self._count_group_liberties(board, nx, ny) == 0:
                        # 获取这块死子的所有坐标
                        group = self._get_group(board, nx, ny)
                        captured.update(group)
        return captured

    def _get_group(self, board: Board, x: int, y: int) -> Set[Tuple[int, int]]:
        """获取连通的同色棋子块"""
        piece = board.get_piece(x, y)
        if not piece: return set()
        
        group = set()
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in group: continue
            group.add((cx, cy))
            
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if board.is_valid_pos(nx, ny) and board.get_piece(nx, ny) == piece:
                    stack.append((nx, ny))
        return group

    def _count_group_liberties(self, board: Board, x: int, y: int) -> int:
        """计算一块棋的气"""
        group = self._get_group(board, x, y)
        liberties = 0
        visited_empty = set()
        
        for (gx, gy) in group:
            for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                nx, ny = gx + dx, gy + dy
                if board.is_valid_pos(nx, ny):
                    if board.get_piece(nx, ny) is None and (nx, ny) not in visited_empty:
                        liberties += 1
                        visited_empty.add((nx, ny))
        return liberties

    def _count_liberties(self, board: Board, x: int, y: int) -> int:
        """计算单个位置所在块的气"""
        return self._count_group_liberties(board, x, y)

    def check_win(self, board: Board, last_x: int, last_y: int) -> Optional[str]:
        # 第一阶段围棋不需要自动判胜负（由系统判或者双方虚着结束）
        # 这里可以返回 None，直到游戏显式结束
        return None 

