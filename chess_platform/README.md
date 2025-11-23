# 棋类对战平台设计文档 (第一阶段)

## 1. 设计思路

本项目采用 **MVC (Model-View-Controller)** 架构思想进行分层设计，将游戏逻辑（Model）、用户界面（View）和交互控制（Controller）分离，以满足“高内聚、低耦合”的面向对象设计原则。

### 架构分层
- **Core Layer (`core/`)**: 定义系统的核心抽象接口和通用设计模式基类。
- **Game Logic Layer (`games/`)**: 实现具体游戏（围棋、五子棋）的规则与状态管理。
- **UI Layer (`ui/`)**: 负责与用户交互，通过 CLI 显示游戏状态并接收指令。

## 2. 设计模式选用说明

为了满足作业中“体现较多设计模式”及“可扩展性”的要求，本项目应用了以下 6 种设计模式：

### 2.1 工厂模式 (Factory Method)
- **应用位置**: `games.logic.GameFactory`
- **目的**: 封装游戏的创建过程。客户端（UI）无需知道具体的 `GameContext` 初始化细节，只需请求 "Go" 或 "Gomoku"，工厂即可返回配置好的游戏实例。这也便于未来扩展其他棋类（如象棋）。

### 2.2 策略模式 (Strategy Pattern)
- **应用位置**: `games.rules.RuleStrategy` (接口) 以及 `GoRule`, `GomokuRule` (实现)
- **目的**: 将“游戏规则”从“游戏流程”中剥离。不同棋类的落子合法性判断、胜负判断算法完全不同。通过策略模式，`GameContext` 不需要写大量的 `if type == 'Go': ... else ...`，而是直接调用 `self.rule.check_win()`，极大提高了代码的可维护性。

### 2.3 享元模式 (Flyweight Pattern)
- **应用位置**: `core.patterns.PieceFactory` 和 `PieceType`
- **目的**: 作业要求“减少对象创建开销”。棋盘上可能存在数百个棋子，但它们只有颜色不同（黑/白）。我们通过享元工厂，确保内存中只有 2 个 `PieceType` 对象（Black 和 White），棋盘格子上存储的只是这两个对象的引用，而非重复创建新对象。

### 2.4 命令模式 (Command Pattern)
- **应用位置**: `games.logic.MoveCommand`
- **目的**: 将“落子”操作封装为对象。这使得我们可以轻松地管理操作历史。
- **体现**: `MoveCommand` 拥有 `execute()` 和 `undo()` 方法。当用户请求悔棋时，只需弹出栈顶命令并执行 `undo()`。

### 2.5 备忘录模式 (Memento Pattern)
- **应用位置**: `core.interfaces.Board.get_snapshot()`
- **目的**: 用于实现“悔棋”和“存档”功能。
- **实现**: 在执行每个 `MoveCommand` 之前，系统会保存一份 `Board` 的快照（Memento）。`undo` 操作通过恢复快照回到上一步状态，这比通过算法逆向推导（例如复杂的围棋提子恢复）要更安全、更通用。

### 2.6 观察者模式 (Observer Pattern)
- **应用位置**: `core.patterns.Observer` (UI 实现) 和 `Subject` (Board 继承)
- **目的**: 实现 Model 和 View 的解耦。
- **流程**: 当 `Board` 数据发生变化（落子、清空）时，自动调用 `notify()`。UI 层作为观察者收到通知后调用 `render()` 刷新界面。这样后端逻辑完全不需要知道 UI 是控制台还是图形界面。

## 3. 类图设计 (简述)

- `Game` (Base Class) -> 聚合 `Board`, `RuleStrategy`
- `GameContext` (Concrete Class) -> 继承 `Game`, 管理 `CommandHistory`
- `RuleStrategy` (Interface) <|-- `GoRule`, `GomokuRule`
- `Command` (Interface) <|-- `MoveCommand`
- `Observer` (Interface) <|-- `ConsoleUI`

## 4. 功能实现

### 基本需求
- [x] 五子棋/围棋双人对战
- [x] 交替落子
- [x] 围棋提子逻辑 (基于 DFS 气计算)
- [x] 五子棋胜负判断
- [x] 处理非法落子

### 交互功能
- [x] 开始/重新开始游戏
- [x] 自定义棋盘大小 (8-19)
- [x] 悔棋 (Undo)
- [x] 存档/读档 (Save/Load)
- [x] 围棋虚着 (Pass)

## 5. 运行说明

在项目根目录下运行：
```bash
python -m chess_platform.main
```

