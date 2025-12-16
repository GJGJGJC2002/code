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


class GomokuMCTS(BaseAI):
    """
    三级 AI：简化版 MCTS，适用于五子棋。
    - 使用 UCT 选点
    - 限定模拟次数以保证实时性
    - rollout 随机落子
    """
    def __init__(self, simulations: int = 400, c_param: float = 1.4, name: str = "AI-MCTS"):
        super().__init__(name)
        self.simulations = simulations
        self.c = c_param

    def select_move(self, game: "GameContext") -> Optional[Tuple[int, int]]:
        if not isinstance(game.rule, GomokuRule):
            # 仅在五子棋启用，其他规则退化为随机
            return RandomAI(name=self.name + "-Fallback").select_move(game)
        moves = legal_moves(game)
        if not moves:
            return None
        # 节点结构
        class Node:
            __slots__ = ("parent","move","wins","visits","children","player_idx")
            def __init__(self, parent, move, player_idx):
                self.parent = parent
                self.move = move
                self.wins = 0
                self.visits = 0
                self.children: List["Node"] = []
                self.player_idx = player_idx  # 谁在该节点落子

        root = Node(None, None, game.current_player_idx)

        import math, copy
        board0 = game.board

        def uct(child: Node, total_visits: int):
            if child.visits == 0:
                return float("inf")
            return child.wins / child.visits + self.c * (math.sqrt(math.log(total_visits) / child.visits))

        def expand(node: Node, board_copy, player_idx):
            avail = []
            me = game.players[player_idx]
            for x,y in legal_moves_board(board_copy, game.rule, me):
                avail.append((x,y))
            for mv in avail:
                node.children.append(Node(node, mv, player_idx))

        def legal_moves_board(board, rule, me):
            res=[]
            for r in range(board.size):
                for c in range(board.size):
                    if board.get_piece(r,c) is None:
                        ok,_ = rule.is_valid_move(board,r,c,me)
                        if ok:
                            res.append((r,c))
            return res

        def simulate(board_copy, next_player_idx):
            # 随机落子直到胜负或无空
            rule: GomokuRule = game.rule  # type: ignore
            cur_idx = next_player_idx
            last_move = (-1,-1)
            while True:
                me = game.players[cur_idx]
                avail = legal_moves_board(board_copy, rule, me)
                if not avail:
                    return "Draw"
                mv = random.choice(avail)
                board_copy.place_piece(mv[0], mv[1], me)
                last_move = mv
                winner = rule.check_win(board_copy, mv[0], mv[1])
                if winner:
                    return winner
                cur_idx = 1 - cur_idx

        for _ in range(self.simulations):
            # 拷贝棋盘
            bcopy = copy_board(board0)
            path = [root]
            node = root
            cur_player_idx = game.current_player_idx
            # selection
            while node.children:
                total = sum(ch.visits for ch in node.children)
                node = max(node.children, key=lambda ch: uct(ch, total if total>0 else 1))
                # 落子
                me = game.players[cur_player_idx]
                bcopy.place_piece(node.move[0], node.move[1], me)
                cur_player_idx = 1 - cur_player_idx
                path.append(node)
                winner = game.rule.check_win(bcopy, node.move[0], node.move[1])
                if winner:
                    result = winner
                    break
            else:
                # expand
                expand(node, bcopy, cur_player_idx)
                # rollout
                result = simulate(bcopy, cur_player_idx)

            # backprop
            for n in path:
                n.visits += 1
                if result == "Draw":
                    n.wins += 0.5
                else:
                    win_color = result
                    if game.players[n.player_idx].color_name == win_color:
                        n.wins += 1

        # 选择访问最多的子节点
        if not root.children:
            return random.choice(moves)
        best = max(root.children, key=lambda ch: ch.visits)
        return best.move


def copy_board(board):
    from chess_platform.core.interfaces import Board
    size = board.size
    new_board = Board(size)
    new_board._grid = [row[:] for row in board._grid]  # shallow copy ok because flyweight
    return new_board


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

