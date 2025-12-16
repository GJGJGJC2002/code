# 第二阶段扩展说明（棋类对战平台）

## 1. 需求重述（新增）
- 新增游戏：黑白棋（Othello），默认 8x8，合法落子需翻转对手棋子，无合法步时跳过，满盘或双方无步判胜。
- AI 对弈：支持玩家-AI、AI-AI。对五子棋提供两级 AI（随机、启发式评分），黑白棋提供随机 AI。
- 录像与回放：行棋过程记录步序，存档中保存日志，支持回放模式逐步重放。
- 账户管理：本地注册/登录，记录战绩（场次、胜/负/平），对局结束自动更新，界面显示玩家/AI/游客身份，录像文件关联账户。
- 保持第一阶段功能兼容：五子棋、围棋对战、悔棋、存档/读档、CLI/GUI。
- 可选功能暂未实现：网络对战（已留扩展点）。

## 2. 设计与类结构
整体仍采用 MVC + 设计模式组合：Factory、Strategy、Command+Memento、Observer、Flyweight。对扩展点最小侵入：
- `GameFactory`：新增 `OthelloRule`，支持 `"othello"` 创建。
- `RuleStrategy` 扩展实现：`OthelloRule`（合法步计算 + 翻转 + 胜负判定），保持接口兼容。
- `GameContext`：新增控制器/账户/日志字段；Othello 初始布局；自动 AI 回合；保存/读档包含玩家信息与 move_log；`on_game_over` 更新账户战绩；`log_move` 记录步序。
- AI 模块 `games/ai.py`：`RandomAI`、`GomokuHeuristicAI`（进攻/防守简单评分），`legal_moves(game)` 复用各规则。
- 录像：`move_log` 内嵌在存档；CLI `replay <file>` 逐步重放。
- 账户：`utils/account.py` 本地 JSON（用户名、SHA256 密码、stats），提供注册/登录/战绩更新。
- 观察者/享元/命令模式保持不变，GUI/CLI 作为 Observer。

## 3. 关键代码与设计模式体现
- **策略模式**：`OthelloRule`/`GomokuRule`/`GoRule` 封装合法落子、胜负判定；AI 调用 `legal_moves` 统一获取。
- **命令+备忘录**：`MoveCommand` 在执行前保存棋盘快照，执行后写入 move_log，支持悔棋与回放日志。
- **工厂模式**：`GameFactory.create_game` 动态装配游戏与规则。
- **观察者模式**：`Board` 通知 CLI/GUI 重绘；`game_over` 事件触发 GUI 弹窗。
- **享元模式**：`PieceFactory` 仅持有黑/白两实例，棋盘存引用。
- **账户管理**：`utils/account` 隔离存储；`GameContext.on_game_over` 更新胜/负/平。
- **AI 控制器注入**：`GameContext.controllers` 允许人类/AI/游客混合，`_auto_play_if_ai` 轮转执行 AI。
- **回放**：存档中附带 `move_log`，CLI 重放时重建空盘并按步渲染。

## 4. 使用方式
### 4.1 运行
```bash
python -m chess_platform.main          # 启动 GUI（默认）
python -m chess_platform.main --cli    # 启动 CLI
```

### 4.2 CLI 入口
- 选择游戏：1 五子棋 / 2 围棋 / 3 黑白棋；输入棋盘大小（默认 15/19/8）。
- 为黑/白配置：人类 / AI-Random / AI-Pro（五子棋启发式，其它退化随机）；可选登录/注册账户。
- 指令：`place r c` 落子；`pass`（围棋）；`undo` 悔棋；`save <f>` 存档；`load <f>` 读档；`replay <f>` 回放存档步序；`restart` 重开；`quit` 退出。

### 4.3 GUI 入口
- 右侧按钮选择游戏：New Gomoku/Go/Othello。输入框设置 Black/White 名称，OptionMenu 选择 human/ai-rand/ai-pro（五子棋二级 AI）。
- 支持：落子点击、重开、悔棋、虚着（围棋）、存/读档。游戏结束自动弹窗并可重开。
- 回放：通过“Load Game”加载含 `move_log` 的存档后，自动从空盘按 1s/步重放，播放期间禁止人工落子。

## 5. 录像与回放
- 运行时自动记录 `move_log`；`save_game` 时随快照写入。
- CLI 回放：`replay savefile.dat` 将在当前终端逐步渲染历史步序。
- GUI 回放：加载存档即进入回放模式，从空盘按 1s/步播放 `move_log`，播放完毕结束回放。
- 存档兼容旧字段，新增 `move_log`、玩家信息字段。

## 6. 账户与战绩
- 本地文件：`utils/accounts.json`（自动创建）。字段：密码哈希，stats{games,win,draw,loss}。
- 登录/注册：CLI 启动时可选，GUI 当前默认游客/AI（可后续扩展登录框）。
- 对局结束自动更新胜负平；未登录视为游客不计入。
- 录像文件隐式关联玩家名（保存在存档的 players_name）。

## 7. 边缘与异常处理
- 非法落子：占位/自杀手/无翻转（黑白棋）判无效。
- 无合法步（黑白棋）：自动跳过当前回合。
- 悔棋：空历史保护。
- 存/读档：文件异常或类型不匹配将提示失败，不污染当前局。
- 棋盘大小：限定 8-19，非法输入回退默认。
- 指令容错：CLI 提示 Unknown/Usage error；GUI 弹窗提示。

## 8. 测试要点（建议）
- 五子棋：连续 5 子判胜；AI-Pro 能稳定压制随机 AI。
- 围棋：提子与自杀手判定。
- 黑白棋：合法步翻转、无步跳过、满盘计分。
- 回放：保存后使用 replay，步序与终局一致。
- 账户：注册后登录，对局结束胜负计数递增。

## 9. 目录与主要文件
- 核心逻辑：`games/logic.py` `games/rules.py` `games/ai.py`
- 账户：`utils/account.py`
- 界面：`ui/cli.py` `ui/gui.py`
- 文档：`docs/Doc2.md`（本文件）


