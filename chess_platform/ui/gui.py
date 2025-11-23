import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import math
from typing import Any

from chess_platform.core.patterns import Observer
from chess_platform.games.logic import GameFactory, GameContext

class ChessGUI(Observer):
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python Chess Platform (OOD Assignment)")
        self.root.geometry("800x640")
        self.root.resizable(False, False)

        self.game: GameContext = None
        self.cell_size = 30
        self.margin = 30
        self.piece_radius = 12

        # 初始化 UI 组件
        self._init_ui()
        
        # 默认启动一个五子棋游戏
        self.start_game("Gomoku", 15)

    def _init_ui(self):
        # === 左侧：棋盘区域 ===
        self.canvas = tk.Canvas(self.root, width=600, height=600, bg="#E3C699") # 木纹色背景
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        # 绑定鼠标点击事件
        self.canvas.bind("<Button-1>", self.on_board_click)

        # === 右侧：控制面板 ===
        self.control_panel = tk.Frame(self.root)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        # 状态标签
        self.lbl_info = tk.Label(self.control_panel, text="Welcome", font=("Arial", 12, "bold"))
        self.lbl_info.pack(pady=20)

        self.lbl_player = tk.Label(self.control_panel, text="", font=("Arial", 10))
        self.lbl_player.pack(pady=5)

        # 按钮群
        btn_width = 15
        
        tk.Button(self.control_panel, text="New Gomoku (15)", width=btn_width, 
                 command=lambda: self.ask_new_game("Gomoku")).pack(pady=5)
        
        tk.Button(self.control_panel, text="New Go (19)", width=btn_width, 
                 command=lambda: self.ask_new_game("Go")).pack(pady=5)

        tk.Button(self.control_panel, text="Restart (重开)", width=btn_width, 
                 command=self.on_restart).pack(pady=5)

        tk.Frame(self.control_panel, height=20).pack() # Spacer

        tk.Button(self.control_panel, text="Undo (悔棋)", width=btn_width, 
                 command=self.on_undo).pack(pady=5)
        
        tk.Button(self.control_panel, text="Pass (虚着)", width=btn_width, 
                 command=self.on_pass).pack(pady=5)

        tk.Frame(self.control_panel, height=20).pack() # Spacer

        tk.Button(self.control_panel, text="Save Game", width=btn_width, 
                 command=self.on_save).pack(pady=5)
        
        tk.Button(self.control_panel, text="Load Game", width=btn_width, 
                 command=self.on_load).pack(pady=5)

    def ask_new_game(self, game_type: str):
        # 弹窗询问棋盘大小
        default_size = 19 if game_type == "Go" else 15
        size = simpledialog.askinteger("Board Size", f"Enter size for {game_type} (8-19):", 
                                     parent=self.root, minvalue=8, maxvalue=19, initialvalue=default_size)
        if size:
            self.start_game(game_type, size)

    def start_game(self, game_type: str, size: int):
        # 工厂模式创建游戏
        self.game = GameFactory.create_game(game_type, size)
        # 观察者模式：注册自己监听棋盘变化
        self.game.board.attach(self)
        self.game.start()
        
        # 初始绘制
        self.update_status()
        self.draw_board()

    # ==========================================
    # Observer 接口实现
    # ==========================================
    def update(self, subject: Any, *args, **kwargs):
        """当后端 Board 发生变化时，此方法被自动调用"""
        self.draw_pieces()
        self.update_status()
        
        # 检查是否收到 game_over 事件
        if kwargs.get("event") == "game_over":
            # 延迟 100ms 弹窗，确保界面已经重绘（棋子落子动画完成）
            self.root.after(100, self.show_winner_alert)

    def show_winner_alert(self):
        winner = self.game.winner if self.game.winner else "Draw"
        if messagebox.askyesno("Game Over", f"Game Over! Winner: {winner}\nDo you want to restart?"):
            self.on_restart()

    # ==========================================
    # 绘图逻辑 (View)
    # ==========================================
    def draw_board(self):
        self.canvas.delete("all")
        size = self.game.board.size
        
        # 动态计算网格大小以适应 Canvas
        # 预留 margin
        available_w = 600 - 2 * self.margin
        self.cell_size = available_w / (size - 1)

        # 画线
        for i in range(size):
            pos = self.margin + i * self.cell_size
            # 横线
            self.canvas.create_line(self.margin, pos, self.margin + available_w, pos)
            # 竖线
            self.canvas.create_line(pos, self.margin, pos, self.margin + available_w)
        
        # 画星位 (仅针对 19路和15路简单处理，可选)
        if size in [15, 19]:
            self._draw_star_points(size)
            
        # 重绘棋子
        self.draw_pieces()

    def _draw_star_points(self, size):
        points = []
        if size == 19:
            points = [(3,3), (3,9), (3,15), (9,3), (9,9), (9,15), (15,3), (15,9), (15,15)]
        elif size == 15:
            points = [(3,3), (3,11), (7,7), (11,3), (11,11)]
            
        for r, c in points:
            x = self.margin + c * self.cell_size
            y = self.margin + r * self.cell_size
            r_dot = 3
            self.canvas.create_oval(x-r_dot, y-r_dot, x+r_dot, y+r_dot, fill="black")

    def draw_pieces(self):
        # 清除旧棋子 (为了简单，这里清除所有棋子标签的对象)
        self.canvas.delete("piece")
        self.canvas.delete("marker") # 最后一手的高亮标记
        
        board = self.game.board
        for r in range(board.size):
            for c in range(board.size):
                piece = board.get_piece(r, c)
                if piece:
                    x = self.margin + c * self.cell_size
                    y = self.margin + r * self.cell_size
                    
                    color = "black" if piece.color_name == "Black" else "white"
                    outline = "black" # 白棋也需要黑边框
                    
                    self.canvas.create_oval(x - self.piece_radius, y - self.piece_radius,
                                          x + self.piece_radius, y + self.piece_radius,
                                          fill=color, outline=outline, tags="piece")

        # 标记最后落子位置
        if board.last_move:
            lr, lc = board.last_move
            x = self.margin + lc * self.cell_size
            y = self.margin + lr * self.cell_size
            # 画一个小红点或十字
            self.canvas.create_line(x-5, y, x+5, y, fill="red", width=2, tags="marker")
            self.canvas.create_line(x, y-5, x, y+5, fill="red", width=2, tags="marker")

    def update_status(self):
        if self.game.is_game_over:
            self.lbl_info.config(text="Game Over", fg="red")
        else:
            self.lbl_info.config(text=f"Playing: {self.game.game_type}", fg="black")
            
        p = self.game.current_player
        self.lbl_player.config(text=f"Current Turn: {p.color_name}")

    # ==========================================
    # 事件处理 (Controller)
    # ==========================================
    def on_board_click(self, event):
        if self.game.is_game_over:
            return

        # 将屏幕坐标转换为网格坐标
        # x = margin + col * cell_size  =>  col = (x - margin) / cell_size
        # 使用 round 来寻找最近的交叉点
        col = int(round((event.x - self.margin) / self.cell_size))
        row = int(round((event.y - self.margin) / self.cell_size))

        # 范围检查
        if 0 <= row < self.game.board.size and 0 <= col < self.game.board.size:
            # 调用后端逻辑
            # 注意：如果落子无效（例如已有子），make_move 会返回 False，
            # 但具体的错误提示我们可以让 game 逻辑返回，或者这里简单忽略
            # 由于后端逻辑里 print 了错误，这里我们可以选择捕获或者在 UI 层再校验一次
            # 为了简单，我们直接调用，如果没成功（比如非法位置），界面就不会刷新（因为 observer 不会被 notify）
            
            # 我们可以先预判一下是否为空，给用户更好的反馈
            if self.game.board.get_piece(row, col) is not None:
                 messagebox.showwarning("Invalid Move", "Position already occupied!")
                 return

            success = self.game.make_move(row, col)
            if not success:
                # 可能是围棋的自杀手或者其他规则限制
                messagebox.showwarning("Invalid Move", "Move not allowed by rules (e.g. suicide or Ko).")

    def on_undo(self):
        if not self.game.undo_move():
            messagebox.showinfo("Info", "Cannot undo.")

    def on_pass(self):
        if self.game.game_type != "Go":
            messagebox.showinfo("Info", "Pass is only available in Go.")
            return
        self.game.pass_turn()
        self.update_status()

    def on_save(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".dat")
        if filepath:
            if self.game.save_game(filepath):
                messagebox.showinfo("Success", "Game saved.")
            else:
                messagebox.showerror("Error", "Failed to save game.")

    def on_load(self):
        filepath = filedialog.askopenfilename()
        if filepath:
            # 加载需要重新绑定 observer ?
            # 我们的 load_game 实现是原位恢复数据，不需要重新 new game，所以 observer 关系还在
            if self.game.load_game(filepath):
                self.draw_board() # 强制重绘一次，以防万一
                self.update_status()
                messagebox.showinfo("Success", "Game loaded.")
            else:
                messagebox.showerror("Error", "Failed to load game.")

    def on_restart(self):
        self.game.start()
        # start() 内部会调用 board.clear() -> notify() -> update() -> render()
        # 所以界面会自动刷新

