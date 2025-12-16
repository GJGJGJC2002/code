import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import math
from typing import Any

from chess_platform.core.patterns import Observer
from chess_platform.games.logic import GameFactory, GameContext
from chess_platform.games.ai import RandomAI, GomokuHeuristicAI
from chess_platform.utils import account

class ChessGUI(Observer):
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Python Chess Platform (OOD Assignment)")
        self.root.geometry("800x750")
        self.root.resizable(False, False)

        self.game: GameContext = None
        self.cell_size = 30
        self.margin = 30
        self.piece_radius = 12
        self.mode_vars = {
            "Black": tk.StringVar(value="human"),
            "White": tk.StringVar(value="human")
        }
        self.name_vars = {
            "Black": tk.StringVar(value="Black"),
            "White": tk.StringVar(value="White")
        }
        # 账户信息：None 表示游客
        self.login_accounts = {"Black": None, "White": None}
        self.stats_vars = {"Black": tk.StringVar(value="战绩: -"),
                           "White": tk.StringVar(value="战绩: -")}
        self.is_replaying = False
        self.replay_moves = []
        self.replay_idx = 0
        self.replay_after_id = None
        self.ai_after_id = None
        self.ai_delay_ms = 1000

        # 初始化 UI 组件
        self._init_ui()
        
        # 启动时登录/注册
        self.show_login_dialog()

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

        tk.Button(self.control_panel, text="New Othello (8)", width=btn_width, 
                 command=lambda: self.start_game("Othello", 8)).pack(pady=5)

        tk.Button(self.control_panel, text="Restart (重开)", width=btn_width, 
                 command=self.on_restart).pack(pady=5)

        # 玩家模式选择
        tk.Label(self.control_panel, text="Black 角色").pack()
        tk.OptionMenu(self.control_panel, self.mode_vars["Black"], "human", "ai-rand", "ai-pro", "ai-mcts").pack()
        tk.Entry(self.control_panel, textvariable=self.name_vars["Black"]).pack()
        tk.Label(self.control_panel, textvariable=self.stats_vars["Black"], font=("Arial", 9)).pack()
        tk.Label(self.control_panel, text="White 角色").pack()
        tk.OptionMenu(self.control_panel, self.mode_vars["White"], "human", "ai-rand", "ai-pro", "ai-mcts").pack()
        tk.Entry(self.control_panel, textvariable=self.name_vars["White"]).pack()
        tk.Label(self.control_panel, textvariable=self.stats_vars["White"], font=("Arial", 9)).pack()

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
        # 配置玩家名称与 AI
        for idx, color in enumerate(["Black","White"]):
            mode = self.mode_vars[color].get()
            # human 时使用登录信息；AI 时显示 AI
            if mode == "human":
                acc = self.login_accounts.get(color)
                if acc:
                    self.game.players_name[idx] = acc
                    self.game.players_account[idx] = acc
                    self.game.players_role[idx] = "login"
                    self.name_vars[color].set(acc)
                else:
                    guest = f"Guest-{color}"
                    self.game.players_name[idx] = guest
                    self.game.players_account[idx] = None
                    self.game.players_role[idx] = "visitor"
                    self.name_vars[color].set(guest)
            if mode == "ai-rand":
                ai = RandomAI(name=f"AI-Rand-{color}")
                self.game.controllers[idx] = ai
                self.game.players_role[idx] = "ai"
                self.game.players_name[idx] = "AI"
                self.game.players_account[idx] = None
            elif mode == "ai-pro":
                if game_type.lower() == "gomoku":
                    ai = GomokuHeuristicAI(name=f"AI-Pro-{color}")
                else:
                    ai = RandomAI(name=f"AI-Rand-{color}")
                self.game.controllers[idx] = ai
                self.game.players_role[idx] = "ai"
                self.game.players_name[idx] = "AI"
                self.game.players_account[idx] = None
            elif mode == "ai-mcts":
                from chess_platform.games.ai import GomokuMCTS
                if game_type.lower() == "gomoku":
                    ai = GomokuMCTS(name=f"AI-MCTS-{color}")
                else:
                    ai = RandomAI(name=f"AI-Rand-{color}")
                self.game.controllers[idx] = ai
                self.game.players_role[idx] = "ai"
                self.game.players_name[idx] = "AI"
                self.game.players_account[idx] = None
            elif mode == "human":
                self.game.controllers[idx] = None
            else:
                # 兜底
                self.game.controllers[idx] = None
                self.game.players_role[idx] = "visitor"
        self.game.start()
        
        # 初始绘制
        self.update_status()
        self.draw_board()
        # 若先手为 AI，立即执行
        self.schedule_ai()

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
        name = self.game.players_name[self.game.current_player_idx]
        self.lbl_player.config(text=f"Current Turn: {name} ({p.color_name})")

        # 刷新双方战绩展示
        self.stats_vars["Black"].set(self._format_stats(0))
        self.stats_vars["White"].set(self._format_stats(1))

    # ==========================================
    # 事件处理 (Controller)
    # ==========================================
    def on_board_click(self, event):
        if self.game.is_game_over:
            return
        if self.is_replaying:
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
            else:
                self.schedule_ai()

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
            import pickle
            try:
                with open(filepath,"rb") as f:
                    data = pickle.load(f)
                moves = data.get("move_log", [])
                game_type = data.get("type","Gomoku")
                size = data.get("size",15)
                # 关联账户/名称（用于右侧展示与回放标注）
                loaded_names = data.get("players_name", ["Black", "White"])
                loaded_accounts = data.get("players_account", [None, None])
                # 终止正在进行的 AI/回放
                if self.ai_after_id:
                    self.root.after_cancel(self.ai_after_id)
                    self.ai_after_id = None
                if self.replay_after_id:
                    self.root.after_cancel(self.replay_after_id)
                    self.replay_after_id = None
                # 使用新实例，空盘开始回放
                self.game = GameFactory.create_game(game_type, size)
                self.game.board.attach(self)
                self.game.players_name = loaded_names
                self.game.players_account = loaded_accounts
                self.game.start()
                self.is_replaying = True
                self.replay_moves = moves
                self.replay_idx = 0
                self.update_status()
                self.draw_board()
                self._replay_step()
            except Exception as e:
                messagebox.showerror("Error", f"Load/Replay failed: {e}")

    # ============ 登录/注册 ============
    def show_login_dialog(self):
        dlg = tk.Toplevel(self.root)
        dlg.title("用户登录/注册")
        dlg.geometry("420x260")
        dlg.resizable(False, False)
        dlg.grab_set()

        mode_var_b = tk.StringVar(value="guest")
        mode_var_w = tk.StringVar(value="guest")
        user_b = tk.StringVar(value="")
        pwd_b = tk.StringVar(value="")
        user_w = tk.StringVar(value="")
        pwd_w = tk.StringVar(value="")

        def build_block(parent, title, mode_var, user_var, pwd_var):
            frame = tk.LabelFrame(parent, text=title)
            frame.pack(fill=tk.X, padx=10, pady=6)
            row1 = tk.Frame(frame); row1.pack(anchor="w")
            tk.Radiobutton(row1, text="游客", variable=mode_var, value="guest").pack(side=tk.LEFT)
            tk.Radiobutton(row1, text="登录", variable=mode_var, value="login").pack(side=tk.LEFT)
            tk.Radiobutton(row1, text="注册", variable=mode_var, value="register").pack(side=tk.LEFT)
            row2 = tk.Frame(frame); row2.pack(fill=tk.X, pady=2)
            tk.Label(row2, text="用户名").pack(side=tk.LEFT)
            tk.Entry(row2, textvariable=user_var, width=18).pack(side=tk.LEFT, padx=5)
            row3 = tk.Frame(frame); row3.pack(fill=tk.X, pady=2)
            tk.Label(row3, text="密码  ").pack(side=tk.LEFT)
            tk.Entry(row3, textvariable=pwd_var, show="*", width=18).pack(side=tk.LEFT, padx=5)

        build_block(dlg, "Black 玩家", mode_var_b, user_b, pwd_b)
        build_block(dlg, "White 玩家", mode_var_w, user_w, pwd_w)

        def apply_one(color, mode_var, user_var, pwd_var):
            mode = mode_var.get()
            u = user_var.get().strip()
            p = pwd_var.get().strip()
            if mode == "guest":
                self.login_accounts[color] = None
                return True
            if u == "" or p == "":
                messagebox.showerror("错误", f"{color} 选择登录/注册时用户名和密码不能为空")
                return False
            if mode == "login":
                if not account.login(u, p):
                    messagebox.showerror("错误", f"{color} 登录失败：用户名或密码错误")
                    return False
                self.login_accounts[color] = u
                return True
            if mode == "register":
                if not account.register(u, p):
                    messagebox.showerror("错误", f"{color} 注册失败：用户名已存在")
                    return False
                self.login_accounts[color] = u
                return True
            return True

        def on_ok():
            if not apply_one("Black", mode_var_b, user_b, pwd_b):
                return
            if not apply_one("White", mode_var_w, user_w, pwd_w):
                return
            # 回填显示名称
            if self.login_accounts["Black"]:
                self.name_vars["Black"].set(self.login_accounts["Black"])
            else:
                self.name_vars["Black"].set("Guest-Black")
            if self.login_accounts["White"]:
                self.name_vars["White"].set(self.login_accounts["White"])
            else:
                self.name_vars["White"].set("Guest-White")
            dlg.destroy()

        btn_row = tk.Frame(dlg)
        btn_row.pack(pady=10)
        tk.Button(btn_row, text="确定", width=10, command=on_ok).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_row, text="跳过(游客)", width=12, command=lambda: dlg.destroy()).pack(side=tk.LEFT, padx=6)

        self.root.wait_window(dlg)

    def _format_stats(self, idx: int) -> str:
        # idx 0=Black, 1=White
        if not hasattr(self, "game") or self.game is None:
            return "战绩: -"
        role = self.game.players_role[idx] if idx < len(self.game.players_role) else "visitor"
        acc = self.game.players_account[idx] if idx < len(self.game.players_account) else None
        if role == "ai":
            return "战绩: AI"
        if not acc:
            return "战绩: 游客"
        st = account.get_stats(acc) or {}
        return f"战绩: 场次{st.get('games',0)} 胜{st.get('win',0)} 平{st.get('draw',0)} 负{st.get('loss',0)}"

    def _replay_step(self):
        if not self.is_replaying:
            return
        if self.replay_idx >= len(self.replay_moves):
            self.is_replaying = False
            return
        step = self.replay_moves[self.replay_idx]
        color = step["color"]
        piece = self.game.players[0] if color == "Black" else self.game.players[1]
        x, y = step["x"], step["y"]
        self.game.board.place_piece(x, y, piece)
        self.game.board.last_move = (x, y)
        self.replay_idx += 1
        self.update_status()
        self.draw_board()
        # 1s 间隔
        self.replay_after_id = self.root.after(1000, self._replay_step)

    # ============ AI 演示（非阻塞） ============
    def schedule_ai(self):
        # 若当前轮到 AI，则安排一步后再继续
        if self.ai_after_id:
            self.root.after_cancel(self.ai_after_id)
            self.ai_after_id = None
        if self.is_replaying:
            return
        ctrl = self.game.controllers[self.game.current_player_idx]
        if ctrl is None:
            return
        # 安排一步
        self.ai_after_id = self.root.after(self.ai_delay_ms, self._ai_step)

    def _ai_step(self):
        self.ai_after_id = None
        if self.is_replaying or self.game.is_game_over:
            return
        ctrl = self.game.controllers[self.game.current_player_idx]
        if ctrl is None:
            return
        # Othello 无合法步则跳过
        from chess_platform.games import ai as ai_mod
        if self.game.game_type.lower() == "othello" and not ai_mod.legal_moves(self.game):
            self.game.switch_player()
            self.update_status()
            self.draw_board()
            self.schedule_ai()
            return
        move = ctrl.select_move(self.game)
        if move is None:
            return
        x,y = move
        if self.game.make_move(x, y):
            self.schedule_ai()

    def on_restart(self):
        self.game.start()
        # start() 内部会调用 board.clear() -> notify() -> update() -> render()
        # 所以界面会自动刷新

