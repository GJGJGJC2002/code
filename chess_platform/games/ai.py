import random
from typing import Tuple, Optional, List, TYPE_CHECKING
from chess_platform.games.rules import GomokuRule, OthelloRule

if TYPE_CHECKING:
    from chess_platform.games.logic import GameContext  # type: ignore


class BaseAI:
    def __init__(self, name: str = "AI"):
        self.name = name

    def select_move(self, game: "GameContext") -> Optional[Tuple[int, int]]:
        raise NotImplementedError


class RandomAI(BaseAI):
    """一级 AI：合法位置随机落子"""
    def select_move(self, game: "GameContext") -> Optional[Tuple[int, int]]:
        moves = legal_moves(game)
        return random.choice(moves) if moves else None


class GomokuHeuristicAI(BaseAI):
    """二级 AI：基于简单评分（进攻+防守）的启发式"""
    def __init__(self, attack_weight: int = 2, defend_weight: int = 3, name: str = "AI-Pro"):
        super().__init__(name)
        self.attack_weight = attack_weight
        self.defend_weight = defend_weight

    def select_move(self, game: "GameContext") -> Optional[Tuple[int, int]]:
        moves = legal_moves(game)
        if not moves:
            return None
        best_score = -1
        best_moves: List[Tuple[int, int]] = []
        rule: GomokuRule = game.rule  # type: ignore
        me = game.current_player
        opponent = game.players[1 - game.current_player_idx]

        for x, y in moves:
            score = self._score_position(game, rule, x, y, me, opponent)
            if score > best_score:
                best_score = score
                best_moves = [(x, y)]
            elif score == best_score:
                best_moves.append((x, y))
        return random.choice(best_moves) if best_moves else None

    def _score_position(self, game: "GameContext", rule: GomokuRule, x: int, y: int, me, opp) -> int:
        board = game.board
        # 简单打分：以落点为中心，统计四个方向连续棋子数，进攻+防守
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        score = 0
        for dx, dy in directions:
            my_count = 1  # 包含当前落子
            opp_count = 0
            cx, cy = x + dx, y + dy
            while board.is_valid_pos(cx, cy) and board.get_piece(cx, cy) == me:
                my_count += 1
                cx += dx
                cy += dy
            cx, cy = x - dx, y - dy
            while board.is_valid_pos(cx, cy) and board.get_piece(cx, cy) == me:
                my_count += 1
                cx -= dx
                cy -= dy

            cx, cy = x + dx, y + dy
            while board.is_valid_pos(cx, cy) and board.get_piece(cx, cy) == opp:
                opp_count += 1
                cx += dx
                cy += dy
            cx, cy = x - dx, y - dy
            while board.is_valid_pos(cx, cy) and board.get_piece(cx, cy) == opp:
                opp_count += 1
                cx -= dx
                cy -= dy

            score += my_count * self.attack_weight + opp_count * self.defend_weight
        return score


def legal_moves(game: "GameContext") -> List[Tuple[int, int]]:
    """根据当前规则返回合法落子列表"""
    board = game.board
    rule = game.rule
    me = game.current_player
    moves = []
    # Othello 有专属的合法步计算
    if isinstance(rule, OthelloRule):
        return rule.legal_moves(board, me)
    # 其他规则：遍历空位 + is_valid_move
    for r in range(board.size):
        for c in range(board.size):
            if board.get_piece(r, c) is None:
                ok, _ = rule.is_valid_move(board, r, c, me)
                if ok:
                    moves.append((r, c))
    return moves

