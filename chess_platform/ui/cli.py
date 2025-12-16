import sys
import os
from typing import Any
from chess_platform.core.interfaces import Board
from chess_platform.core.patterns import Observer
from chess_platform.games.logic import GameContext, GameFactory
from chess_platform.games.ai import RandomAI, GomokuHeuristicAI, GomokuMCTS
from chess_platform.utils import account

class ScreenBuilder:
    """
    Builder 模式：构建界面组件
    """
    def __init__(self):
        self.parts = []

    def add_header(self, game: GameContext):
        player_name = game.current_player.color_name
        self.parts.append(f"=== {game.game_type} Game ===")
        self.parts.append(f"Current Player: {player_name} ({game.current_player.symbol})")
        if game.is_game_over:
            winner = game.winner if game.winner else "Draw"
            self.parts.append(f"\n!!! GAME OVER - Winner: {winner} !!!\n")
        self.parts.append("-" * 30)
    
    def add_board(self, board: Board):
        # 构建坐标轴
        size = board.size
        # 列号 (0-9, A-Z...)
        col_header = "   " + " ".join([f"{i:<2}" for i in range(size)])
        self.parts.append(col_header)
        
        for r in range(size):
            row_str = f"{r:<2} "
            for c in range(size):
                piece = board.get_piece(r, c)
                symbol = piece.symbol if piece else "."
                
                # 标记最后落子位置
                if board.last_move == (r, c):
                    row_str += f"[{symbol}]"[:2] # 简单高亮
                else:
                    row_str += f" {symbol} "
            self.parts.append(row_str)
        self.parts.append("-" * 30)

    def add_instructions(self, show_help: bool):
        if show_help:
            self.parts.append("Commands:")
            self.parts.append("  place <row> <col>  : Place a piece (e.g., place 3 4)")
            self.parts.append("  pass               : Pass turn (Go only)")
            self.parts.append("  undo               : Undo last move")
            self.parts.append("  save <filename>    : Save game")
            self.parts.append("  load <filename>    : Load game")
            self.parts.append("  replay <filename>  : Replay a saved game")
            self.parts.append("  restart            : Restart game")
            self.parts.append("  quit               : Exit")
            self.parts.append("  help               : Toggle help")
    
    def build(self) -> str:
        return "\n".join(self.parts)


class ConsoleUI(Observer):
    """
    控制台界面
    作为 Observer 监听 Board 的变化
    """
    def __init__(self):
        self.game: GameContext = None
        self.show_help = True

    def start(self):
        print("Welcome to Python Chess Platform")
        print("1. Gomoku (五子棋)")
        print("2. Go (围棋)")
        print("3. Othello (黑白棋)")
        
        choice = input("Select Game (1/2/3): ").strip()
        if choice not in ["1","2","3"]:
            choice = "1"
        if choice == "1":
            game_type = "Gomoku"
            default_size = 15
        elif choice == "2":
            game_type = "Go"
            default_size = 19
        else:
            game_type = "Othello"
            default_size = 8

        size_str = input(f"Enter board size (8-19, default {default_size}): ").strip()
        try:
            size = int(size_str)
            if not (8 <= size <= 19): raise ValueError
        except:
            size = default_size

        # 使用工厂创建游戏
        self.game = GameFactory.create_game(game_type, size)
        self._setup_players()
        
        # 注册观察者
        self.game.board.attach(self)
        
        self.game.start()
        # 如果先手是 AI，立即执行
        self.game._auto_play_if_ai()
        self.render()
        self.input_loop()

    def _setup_players(self):
        # 玩家身份与 AI 难度
        for idx, color in enumerate(["Black","White"]):
            print(f"\n配置 {color} 方：")
            print("1. 人类玩家")
            print("2. AI-随机（一级）")
            print("3. AI-规则（五子棋二级，其他随机）")
            print("4. AI-MCTS（五子棋三级，其他随机）")
            role = input("选择(1/2/3): ").strip()
            if role == "2":
                ai = RandomAI(name=f"AI-Random-{color}")
                self.game.controllers[idx] = ai
                self.game.players_name[idx] = ai.name
                self.game.players_role[idx] = "ai"
            elif role == "3":
                if self.game.game_type.lower() == "gomoku":
                    ai = GomokuHeuristicAI(name=f"AI-Pro-{color}")
                else:
                    ai = RandomAI(name=f"AI-Random-{color}")
                self.game.controllers[idx] = ai
                self.game.players_name[idx] = ai.name
                self.game.players_role[idx] = "ai"
            elif role == "4":
                if self.game.game_type.lower() == "gomoku":
                    ai = GomokuMCTS(name=f"AI-MCTS-{color}")
                else:
                    ai = RandomAI(name=f"AI-Random-{color}")
                self.game.controllers[idx] = ai
                self.game.players_name[idx] = ai.name
                self.game.players_role[idx] = "ai"
            else:
                self.game.controllers[idx] = None
                self.game.players_role[idx] = "human"
                self._handle_login(idx)

    def _handle_login(self, idx: int):
        need_login = input("登录账户? (y/N): ").strip().lower() == "y"
        if not need_login:
            self.game.players_name[idx] = f"Player{idx+1}"
            self.game.players_account[idx] = None
            return
        username = input("用户名: ").strip()
        if username == "":
            username = f"Player{idx+1}"
        has_account = input("已有账户? (y/N): ").strip().lower() == "y"
        if has_account:
            pwd = input("密码: ").strip()
            if account.login(username,pwd):
                self.game.players_name[idx] = username
                self.game.players_account[idx] = username
                self.game.players_role[idx] = "login"
                print("登录成功")
            else:
                print("登录失败，使用游客")
                self.game.players_name[idx] = f"Guest{idx+1}"
                self.game.players_account[idx] = None
        else:
            pwd = input("设置密码: ").strip()
            if account.register(username,pwd):
                print("注册成功并自动登录")
                self.game.players_name[idx] = username
                self.game.players_account[idx] = username
                self.game.players_role[idx] = "login"
            else:
                print("注册失败，可能已存在。使用游客")
                self.game.players_name[idx] = f"Guest{idx+1}"
                self.game.players_account[idx] = None

    def update(self, subject: Any, *args, **kwargs):
        # 收到 Board 通知时重绘
        self.render()
        if kwargs.get("event") == "place":
            # 可以在这里播放音效或打印特定日志
            pass

    def render(self):
        # 清屏 (可选)
        # os.system('cls' if os.name == 'nt' else 'clear')
        
        builder = ScreenBuilder()
        builder.add_header(self.game)
        builder.add_board(self.game.board)
        builder.add_instructions(self.show_help)
        print(builder.build())

    def input_loop(self):
        while True:
            try:
                cmd_str = input("\n>>> ").strip().lower()
                parts = cmd_str.split()
                if not parts: continue

                action = parts[0]

                if action == "quit":
                    break
                
                elif action == "help":
                    self.show_help = not self.show_help
                    self.render()

                elif action == "restart":
                    self.game.start()
                    self.render()

                elif action == "undo":
                    if self.game.undo_move():
                        print("Undid last move.")
                    else:
                        print("Cannot undo.")

                elif action == "place":
                    if len(parts) < 3:
                        print("Usage: place <row> <col>")
                        continue
                    r, c = int(parts[1]), int(parts[2])
                    if not self.game.make_move(r, c):
                        # make_move 内部会打印错误
                        pass

                elif action == "pass":
                    if self.game.game_type == "Go":
                        self.game.pass_turn()
                        print("Player passed.")
                        self.render()
                    else:
                        print("Pass is only allowed in Go.")

                elif action == "save":
                    fname = parts[1] if len(parts) > 1 else "savegame.dat"
                    if self.game.save_game(fname):
                        print(f"Game saved to {fname}")

                elif action == "load":
                    fname = parts[1] if len(parts) > 1 else "savegame.dat"
                    if self.game.load_game(fname):
                        print(f"Game loaded from {fname}")
                        self.render()

                elif action == "replay":
                    fname = parts[1] if len(parts) > 1 else "savegame.dat"
                    self.replay(fname)

                else:
                    print("Unknown command.")

            except Exception as e:
                print(f"Error: {e}")

    def replay(self, filepath: str):
        import pickle, time
        try:
            with open(filepath, "rb") as f:
                data = pickle.load(f)
            snapshot = data["snapshot"]
            moves = data.get("move_log", [])
            size = snapshot["size"]
            game_type = data.get("type","Gomoku")
            temp_game = GameFactory.create_game(game_type, size)
            temp_game.board.restore_snapshot({"size":size,"grid":[[None for _ in range(size)] for _ in range(size)],"last_move":None})
            temp_game.board.attach(self)
            print(f"Replaying {filepath}, moves={len(moves)}")
            for step in moves:
                color = step["color"]
                piece = temp_game.players[0] if color=="Black" else temp_game.players[1]
                temp_game.board.place_piece(step["x"], step["y"], piece)
                temp_game.board.last_move = (step["x"], step["y"])
                self.render()
                time.sleep(0.3)
            print("Replay finished.")
        except Exception as e:
            print(f"Replay failed: {e}")

