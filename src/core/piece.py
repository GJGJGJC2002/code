from src.core.enums import PieceType

class Piece:
    """
    享元模式：抽象享元角色
    棋子本身只包含颜色信息，不包含位置信息（位置是外部状态）
    """
    def __init__(self, piece_type: PieceType):
        self._type = piece_type

    @property
    def type(self) -> PieceType:
        return self._type

    def get_symbol(self) -> str:
        raise NotImplementedError

class BlackPiece(Piece):
    def __init__(self):
        super().__init__(PieceType.BLACK)
    
    def get_symbol(self) -> str:
        return "●"

class WhitePiece(Piece):
    def __init__(self):
        super().__init__(PieceType.WHITE)
    
    def get_symbol(self) -> str:
        return "○"

class PieceFactory:
    """
    享元工厂：确保黑白棋子全局各只有一个实例
    """
    _pieces = {}

    @staticmethod
    def get_piece(piece_type: PieceType) -> Piece:
        if piece_type not in PieceFactory._pieces:
            if piece_type == PieceType.BLACK:
                PieceFactory._pieces[piece_type] = BlackPiece()
            elif piece_type == PieceType.WHITE:
                PieceFactory._pieces[piece_type] = WhitePiece()
            else:
                return None
        return PieceFactory._pieces[piece_type]

