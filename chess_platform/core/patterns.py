from abc import ABC, abstractmethod
from typing import List, Dict, Any

# ==========================================
# Pattern 1: Observer (观察者模式)
# 用途：解耦 Model (游戏逻辑) 和 View (界面显示)
# ==========================================

class Observer(ABC):
    """观察者接口"""
    @abstractmethod
    def update(self, subject: Any, *args, **kwargs):
        pass

class Subject:
    """被观察者基类"""
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: Observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, *args, **kwargs):
        for observer in self._observers:
            observer.update(self, *args, **kwargs)


# ==========================================
# Pattern 2: Command (命令模式)
# 用途：支持悔棋 (Undo) 和操作历史记录
# ==========================================

class Command(ABC):
    """命令接口"""
    @abstractmethod
    def execute(self) -> bool:
        """执行命令"""
        pass

    @abstractmethod
    def undo(self):
        """撤销命令"""
        pass


# ==========================================
# Pattern 3: Flyweight (享元模式)
# 用途：减少对象创建，全场复用黑白棋子对象
# ==========================================

class PieceType(ABC):
    """享元接口：棋子类型"""
    def __init__(self, color_name: str, symbol: str):
        self.color_name = color_name
        self.symbol = symbol # 例如 "X" 或 "O"

    def __str__(self):
        return self.symbol

class PieceFactory:
    """享元工厂：管理棋子实例"""
    _piece_types: Dict[str, PieceType] = {}

    @staticmethod
    def get_piece_type(color_name: str, symbol: str) -> PieceType:
        key = color_name
        if key not in PieceFactory._piece_types:
            PieceFactory._piece_types[key] = PieceType(color_name, symbol)
        return PieceFactory._piece_types[key]

