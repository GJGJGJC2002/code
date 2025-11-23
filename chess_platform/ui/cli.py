import sys
import os
from typing import Any
from chess_platform.core.interfaces import Board
from chess_platform.core.patterns import Observer
from chess_platform.games.logic import GameContext, GameFactory

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
        print("1. Gomoku (Five-in-a-row)")
        print("2. Go (Weiqi)")
        
        choice = input("Select Game (1 or 2): ").strip()
        size_str = input("Enter board size (8-19, default 15): ").strip()
        try:
            size = int(size_str)
            if not (8 <= size <= 19): raise ValueError
        except:
            size = 15

        game_type = "Gomoku" if choice == "1" else "Go"
        
        # 使用工厂创建游戏
        self.game = GameFactory.create_game(game_type, size)
        
        # 注册观察者
        self.game.board.attach(self)
        
        self.game.start()
        self.render()
        self.input_loop()

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

                else:
                    print("Unknown command.")

            except Exception as e:
                print(f"Error: {e}")

