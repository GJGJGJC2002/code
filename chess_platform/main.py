import sys
import tkinter as tk
from chess_platform.ui.cli import ConsoleUI
from chess_platform.ui.gui import ChessGUI

def main():
    # 可以通过命令行参数控制启动模式，这里默认启动 GUI
    # 如果想用 CLI: python -m chess_platform.main --cli
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        try:
            app = ConsoleUI()
            app.start()
        except KeyboardInterrupt:
            print("\nBye!")
            sys.exit(0)
    else:
        # GUI 模式
        root = tk.Tk()
        app = ChessGUI(root)
        root.mainloop()

if __name__ == "__main__":
    main()
