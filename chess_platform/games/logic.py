import pickle
from typing import List, Optional, Tuple, Callable
from chess_platform.core.interfaces import Game, RuleStrategy, Board
from chess_platform.core.patterns import Command, PieceType
from chess_platform.games.rules import GomokuRule, GoRule, OthelloRule
import random
from chess_platform.games import ai

class MoveCommand(Command):
    """
    落子命令
    包含了 Memento (备忘录) 的应用：在执行前保存快照，用于 Undo
    """
    def __init__(self, game: 'GameContext', x: int, y: int):
        self.game = game
        self.x = x
        self.y = y
        self.player = game.current_player
        self.captured_stones: List[Tuple[int, int]] = []
        self._backup_snapshot = None

    def execute(self) -> bool:
        # 1. 校验合法性
        is_valid, msg = self.game.rule.is_valid_move(self.game.board, self.x, self.y, self.player)
        if not is_valid:
            print(f"Invalid move: {msg}") # 简单反馈，实际应抛出异常或返回状态
            return False

        # 2. 保存状态 (Memento) 用于悔棋
        self._backup_snapshot = self.game.board.get_snapshot()

        # 3. 执行落子
        self.game.board.place_piece(self.x, self.y, self.player)

        # 4. 执行落子后的规则动作 (如围棋提子)
        self.captured_stones = self.game.rule.post_move_action(self.game.board, self.x, self.y, self.player)
        self.game.log_move(self.x, self.y, self.player.color_name)

        # 5. 检查胜负
        winner = self.game.rule.check_win(self.game.board, self.x, self.y)
        if winner:
            self.game.winner = winner
            self.game.is_game_over = True
            # 先更新战绩，再通知 UI（保证 UI 刷新到最新战绩）
            self.game.on_game_over(winner)
            # 显式通知 UI 游戏结束，以便弹出提示
            self.game.board.notify(event="game_over", winner=winner)
        
        # 6. 切换执子
        self.game.switch_player()
        return True

    def undo(self):
        if self._backup_snapshot:
            self.game.board.restore_snapshot(self._backup_snapshot)
            # 恢复当前执子者 (因为 execute 里切换了)
            self.game.switch_player() 
            self.game.is_game_over = False
            self.game.winner = None


class GameContext(Game):
    """具体游戏控制类"""
    def __init__(self, size: int, rule: RuleStrategy, game_type: str):
        super().__init__(size, rule)
        self.game_type = game_type
        self.history: List[Command] = []
        # 控制器：None 表示人工输入；否则应提供 select_move(game)->(x,y)
        self.controllers: List[Optional[Callable]] = [None, None]
        self.players_name: List[str] = ["Player1", "Player2"]
        self.players_role: List[str] = ["human", "human"]  # human / ai / visitor / login
        self.players_account: List[Optional[str]] = [None, None]
        self.move_log: List[dict] = []
        
    def start(self):
        self.board.clear()
        # Othello 初始布局
        if self.game_type.lower() == "othello":
            mid = self.board.size // 2
            black = self.players[0]
            white = self.players[1]
            self.board.place_piece(mid-1, mid-1, white)
            self.board.place_piece(mid, mid, white)
            self.board.place_piece(mid-1, mid, black)
            self.board.place_piece(mid, mid-1, black)
        self.history.clear()
        self.is_game_over = False
        self.winner = None
        self.current_player_idx = 0 # 黑棋先
        self.move_log.clear()

    def make_move(self, x: int, y: int) -> bool:
        if self.is_game_over:
            print("Game is over.")
            return False
        # Othello 场景：如果当前无合法步，自动换手
        if self.game_type.lower() == "othello" and not ai.legal_moves(self):
            self.switch_player()
            return False
            
        cmd = MoveCommand(self, x, y)
        if cmd.execute():
            self.history.append(cmd)
            # 自动触发 AI 回合
            self._auto_play_if_ai()
            return True
        return False

    def _auto_play_if_ai(self):
        # 连续执行 AI 回合直到轮到人工或游戏结束
        loop_guard = 0
        while not self.is_game_over and loop_guard < 200:
            loop_guard += 1
            ctrl = self.controllers[self.current_player_idx]
            if ctrl is None:
                break
            # 若无合法步，自动跳过
            if self.game_type.lower() == "othello" and not ai.legal_moves(self):
                self.switch_player()
                continue
            move = ctrl.select_move(self)
            if move is None:
                break
            x,y = move
            cmd = MoveCommand(self, x, y)
            if cmd.execute():
                self.history.append(cmd)
                continue
            else:
                break

    def undo_move(self) -> bool:
        if not self.history:
            return False
        cmd = self.history.pop()
        cmd.undo()
        return True

    def pass_turn(self):
        """围棋虚着"""
        self.switch_player()
        # 也可以记录一个 PassCommand 进历史，以便悔棋

    def save_game(self, filepath: str):
        """序列化保存"""
        try:
            data = {
                "type": self.game_type,
                "size": self.board.size,
                "snapshot": self.board.get_snapshot(),
                "current_player": self.current_player_idx,
                "history_len": len(self.history),
                "players_name": self.players_name,
                "players_role": self.players_role,
                "players_account": self.players_account,
                "move_log": self.move_log
                # 完整保存 history 比较复杂因为包含对象引用，简化版只保存棋盘状态
                # 作业要求若需完整还原步骤，需要 pickle 整个 history，或者只保存 board 状态
            }
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            print(f"Save failed: {e}")
            return False

    def load_game(self, filepath: str) -> bool:
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            # 简单校验
            if data["type"] != self.game_type:
                print("Game type mismatch")
                return False
            
            self.board.restore_snapshot(data["snapshot"])
            self.current_player_idx = data["current_player"]
            self.players_name = data.get("players_name", self.players_name)
            self.players_role = data.get("players_role", self.players_role)
            self.players_account = data.get("players_account", self.players_account)
            self.move_log = data.get("move_log", [])
            self.history.clear() # 读档后清空历史，或需要更复杂的逻辑恢复历史
            self.is_game_over = False # 假设读档后游戏未结束
            return True
        except Exception as e:
            print(f"Load failed: {e}")
            return False

    # --------- 结果记录 ---------
    def on_game_over(self, winner: str):
        from chess_platform.utils import account
        # winner: "Black"/"White"/"Draw"
        if winner == "Draw":
            for acc in self.players_account:
                if acc:
                    account.update_result(acc, "draw")
            return
        win_idx = 0 if winner == "Black" else 1
        lose_idx = 1 - win_idx
        if self.players_account[win_idx]:
            account.update_result(self.players_account[win_idx], "win")
        if self.players_account[lose_idx]:
            account.update_result(self.players_account[lose_idx], "loss")

    # --------- 录像数据 ---------
    def log_move(self, x:int, y:int, color:str):
        self.move_log.append({"x":x,"y":y,"color":color,"move_idx":len(self.move_log)+1})


class GameFactory:
    """工厂模式：创建游戏"""
    @staticmethod
    def create_game(game_type: str, size: int = 15) -> GameContext:
        if game_type.lower() == "gomoku":
            return GameContext(size, GomokuRule(), "Gomoku")
        elif game_type.lower() == "go":
            return GameContext(size, GoRule(), "Go")
        elif game_type.lower() == "othello":
            return GameContext(size, OthelloRule(), "Othello")
        else:
            raise ValueError("Unknown game type")

