# 评教自动化分发包

北师大研究生评教系统的批量填写工具。三层方案操作门槛不同，能填的内容一样：

> 默认：选择题全选「好」，三个填空依次「无」「无」「90」。三层都会先跟你确认，不会拿默认值直接提交。

| 你是谁 | 用哪个 | 你要做的 | 自动化程度 |
|--------|--------|----------|-----------|
| 会用 WorkBuddy / Codex 等 AI 工具 | `L1_Agent用户/` | 把仓库链接发给 AI 装一次，之后一句「帮我评教」 | 全程自动 |
| 会用命令行（Windows / macOS） | `L2_命令行用户/` | 双击一个文件，确认一次 | 一键批量 |
| 完全不懂技术 | `L3_小白/` | 设定内容 → 拖一次书签，之后每门课点一下 | 单门一键（内容可自定） |

分发时**只发对应那一层文件夹**，不用整套发。

> **用 AI 的人不用手动装**：把仓库链接发给 WorkBuddy / Codex，说一句
> 「把这个仓库里的 `L1_Agent用户/browser-form-automation` 装成 skill」，
> 它会自己 clone 到 `~/.workbuddy/skills/` 并校验。给 Agent 看的完整指令在 [`AGENTS.md`](AGENTS.md)。

---

## 怎么拿到代码

```bash
git clone https://github.com/wfcsilence/bnu-pjxt-auto.git
```

不想装 git：仓库页面右上角 **Code → Download ZIP**，解压即可。

> ZIP 下载会丢掉 `.command` 的可执行位（Windows 打 zip 的老问题），macOS 用户解压后要先 `chmod +x`，见下文 L2 / macOS 一节。用 `git clone` 则不会丢。

---

## 目录结构

```
评教自动化分发包/
├── README.md                         本文件（含给 Agent 的接口说明）
├── AGENTS.md                         给 AI Agent 的安装/执行说明（链接即安装）
│
├── L1_Agent用户/
│   ├── 安装与使用.md
│   └── browser-form-automation/      Skill 目录
│       ├── SKILL.md                  Agent 读取的入口说明
│       ├── scripts/
│       │   ├── engine.py             CDP 引擎（纯标准库，零依赖）
│       │   └── run.py                配方执行器
│       └── recipes/
│           └── bnu-pjxt.json         北师大评教配方（可改）
│
├── L2_命令行用户/
│   ├── README.md                     平台选择 + 共同说明
│   ├── Windows/
│   │   ├── 一键评教.bat              双击入口（纯 ASCII，免疫系统语言）
│   │   ├── launcher.py               中文提示 + 拉起浏览器 + 调用执行器
│   │   ├── run.py                    配方执行器
│   │   ├── engine.py                 CDP 引擎
│   │   ├── config.json               填写规则（可改）
│   │   └── 使用说明.md
│   └── macOS/
│       ├── 一键评教.command          双击入口
│       ├── launcher.py / run.py / engine.py / config.json
│       └── 使用说明.md
│
└── L3_小白/
    ├── 一键安装评教书签.html         浏览器打开，设定内容后拖出书签
    └── 使用说明.md
```

---

## 共同前提（三层都一样）

1. **必须自己登录评教系统**。登录态无法代劳，也不该代劳。
2. **填写内容由你拍板**。三层都会先问你要填什么（选项 + 三个填空），默认值只是省事，不是建议。
3. **提交后不可修改**。评教系统明确提示「一经提交无法修改」，请先确认评分口径。
4. **页面改版会失效**。L1/L2 改配方 JSON，L3 重新拖一次书签。
5. 只支持**桌面浏览器**。手机不行。

---

## L1 · 给 Agent 用户

**环境要求**：能加载 Skill 的 AI 工具（WorkBuddy / Codex 等）+ Python 3。

**安装方式 A · 让 AI 自己装（推荐，不用手碰文件夹）**

把仓库链接发给你用的 AI，附一句话：

> 把 https://github.com/wfcsilence/bnu-pjxt-auto 里的 `L1_Agent用户/browser-form-automation` 装成 skill，装完告诉我怎么验证。

它会 clone → 复制到 `~/.workbuddy/skills/browser-form-automation/` → 校验结构，你不必理解任何路径。给 Agent 的逐条指令写在 [`AGENTS.md`](AGENTS.md)，Codex 这类会读仓库根目录说明文件的工具通常不用你额外交代。

**安装方式 B · 手动复制**

把 `browser-form-automation/` 整个文件夹放到

- WorkBuddy 用户级：`%USERPROFILE%\.workbuddy\skills\`（Windows）或 `~/.workbuddy/skills/`（macOS）
- 或项目级：`{项目目录}\.workbuddy\skills\`

两种方式都要**重启 AI 工具**才识别。确认装好：对 AI 说「你有哪些 skill」，应能看到 `browser-form-automation`。

**使用**：浏览器用独立配置目录开好调试端口（见下），登录后对 AI 说「帮我评教」。**Agent 会先问你四项内容**——选择题选哪一项、三个填空分别写什么——你回答后它才动手，最后报告填写内容与提交数。

> 这一问是刻意的：评教一经提交不能修改，内容不能由 Agent 替你拍板。

---

## L2 · 给命令行用户

### Windows

双击 `Windows\一键评教.bat`。首次会在独立配置目录拉起一个浏览器窗口，在里面登录一次即可。

### macOS

**首次必须先赋予执行权限**（Windows 拷过来、或从网页下 ZIP，都会丢可执行位；`git clone` 不会）：

```bash
cd 你解压的目录/L2_命令行用户/macOS
chmod +x 一键评教.command
```

然后双击 `一键评教.command`。若提示「无法打开，因为来自身份不明的开发者」，右键 →「打开」→ 再点「打开」。

### 两个平台都一样的行为

1. 检测 9222 调试端口，未就绪则用**独立配置目录**启动 Chrome / Edge
2. 等你登录、等端口就绪
3. **逐项问你要填什么**：选择题选项（好/较好/一般/较差/差）→ 三个填空（需要改进的地方 / 突出优点 / 打分）
4. 打印预览，问你一次 `Y` 确认
5. 逐门填写提交，报告提交数与剩余数

输入规则很简单：选择题输编号或直接输文字，填空直接打字，**直接回车 = 用括号里的默认值**，填空想留空输 `-`。

详见各平台的 `使用说明.md`。

---

## L3 · 给完全不懂技术的人

1. 双击 `一键安装评教书签.html`
2. 在页面上**设定要填的内容**：五个选项里选一个（好/较好/一般/较差/差）、三个填空分别写什么（需要改进的地方？/ 突出优点是什么？/ 打多少分？）、要不要自动提交，然后点「生成书签」
3. 按 `Ctrl+Shift+B` 显示书签栏，把蓝色按钮拖上去
4. 以后：进入某门课的填写页 → 点一下书签 → 按你的设定填好（并提交）

设定想改随时回来改，但**改完必须重新点「生成书签」再拖一次**——已经装好的旧书签不会自动跟着变。

详见 `L3_小白/使用说明.md`。

---

## 给 Agent / 自动化脚本的接口说明

> 这一节是给 AI Agent 或想自己写脚本封装的人看的。人可以直接跳过。

### 运行时依赖

- Python **3.8+**，只用标准库（`socket` / `json` / `subprocess` / `urllib`），**无需 pip install**
- 不需要 Node、不需要 Selenium、不需要 Playwright

### 三层共用的执行链

```
入口（bat / command / Skill 指令）
      ↓
launcher.py   检测端口 → 拉起浏览器 → 等就绪 → 交互设定内容 → 确认
      ↓
run.py        读 config.json + 参数，循环：探测列表 → 点击 → 填写提交 → 回到列表
      ↓
engine.py     CDP：HTTP /json 拿 webSocketDebuggerUrl → 手写 WebSocket 握手 → Runtime.evaluate
```

### 入口与调用方式

| 场景 | 命令 | 说明 |
|------|------|------|
| 完全托管（推荐给人类用） | `python launcher.py` | 自己管浏览器、自己问内容、自己问确认 |
| Agent 自己管浏览器 | `python run.py config.json --pick 好 --fill 无 --fill 无 --fill 90` | 前置：9222 端口已就绪且已登录 |
| macOS | `python3 launcher.py` | 同上 |

Agent 建议走第二条：自己用 `--remote-debugging-port=9222 --user-data-dir=<独立目录>` 启动浏览器，登录确认后直接调 `run.py`，避免交互式 `input()` 卡住。

### 填写内容参数（--pick / --fill）

```bash
python run.py config.json --pick 较好 --fill 无 --fill 多讲案例 --fill 95
```

| 参数 | 含义 | 缺省 |
|------|------|------|
| `--pick <文字>` | 选择题选哪一项，须与页面上的选项文字一致 | 配方 `answer.pick` |
| `--fill <文字>` | 填空内容，**按顺序重复传**，有几个空传几次；单个 `-` 表示这一空留白 | 配方 `answer.fills[].default` |

`--fill` 少于空数时，缺的用配方默认值补齐；多于空数时截断。`run.py` 会把这两个值用 `json.dumps` 转成 JS 字面量，替换进 `js.fill_submit` 的 `__PICK__` / `__FILLS__`，因此**引号、反斜杠、中文都不需要转义**。

### 浏览器启动参数（关键）

```
msedge.exe --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\PJAuto\EdgeProfile"
chrome 同理，macOS 用 ~/Library/Application Support/PJAuto/ChromeProfile
```

**不要指向浏览器的默认 User Data 目录**：新版 Chromium 系（Edge/Chrome 136+）会拒绝在默认 profile 上开启调试端口，端口永远起不来。独立目录的代价是首次需登录一次，之后长期保留。

### 退出码

| 码 | 含义 | 处理建议 |
|----|------|---------|
| 0 | 正常结束（含用户主动取消） | 读 stdout 判断实际提交数 |
| 2 | 执行出错（未登录 / 列表加载超时 / CDP 异常） | 看 stderr/stdout 的「错误：」行 |
| 3 | 未找到 Chrome / Edge | 装浏览器，或手动指定路径 |
| 4 | 浏览器启动失败 | 检查权限、策略 |
| 5 | 30 秒内端口未就绪 | 安全软件拦截或企业策略禁用远程调试 |

### 配方（config.json / bnu-pjxt.json）字段

| 字段 | 作用 |
|------|------|
| `site_key` | URL 子串，用于在多个标签页里挑目标页 |
| `list_url` | 列表页地址，每轮回到这里 |
| `port` | 调试端口，默认 9222 |
| `answer.pick` | 选择题默认选项 |
| `answer.pick_options` | 可选清单，供 launcher 打编号菜单、供 Agent 提问时列出 |
| `answer.fills` | 填空默认值，`[{label, default}]`，**数组顺序 = 页面上的填空顺序**，也是 launcher 的提问文案 |
| `js.ready` | 返回 `{hasList, login}`，用于区分「未登录」和「加载慢」 |
| `js.list` | 返回 `{n: 待办数, names: [名称]}` |
| `js.click` | 点击第 `__INDEX__` 个待办 |
| `js.check` | 返回 `{forms: 表单数}`，0 表示无可填项（已评过） |
| `js.fill_submit` | 一次性填完并提交；`__PICK__` / `__FILLS__` 由 `run.py` 替换，用 `window.confirm=()=>true` 绕过确认弹窗 |
| `wait_after_*_sec` | 各步骤等待秒数 |
| `max_iterations` | 循环上限，防死循环 |

`js` 里的每段都是**完整可执行表达式**，`run.py` 原样传给 `Runtime.evaluate`（替换占位符后）。

### 成功判定逻辑

提交会触发页面跳转，JS 返回值不可靠。所以 `run.py` 用**待办数量是否减少**判断成功：

```
提交前 n=10 → 提交 → 回到列表 → 提交后 n=9 → 计 1 次成功
```

若数量未减少，会再导航一次复检；仍不减少则停止并报告，不会盲目继续。

### 并发与幂等

- **同一时间只能跑一份**，否则两个进程抢同一个页面上下文
- 重复运行是安全的：已评过的课 `forms=0`，会被自动跳过并记入 `skipped`
- 中途失败可直接重跑，已提交的不会重复提交

---

## 故障速查

| 现象 | 原因 | 解决 |
|------|------|------|
| bat 双击一闪消失 | 老版本编码问题（现已改为纯 ASCII） | 确认用的是新版 bat |
| 端口 30 秒起不来 | 默认 profile 不支持调试端口 / 安全软件拦截 | 确认用的是独立目录；访问 `http://127.0.0.1:9222/json/version` 自查 |
| 提示「没有登录态」 | 专用窗口里未登录 | 在该窗口登录一次即可 |
| macOS 双击打不开 | 没有可执行权限 | `chmod +x 一键评教.command` |
| macOS 提示身份不明的开发者 | Gatekeeper | 右键 →「打开」→ 再点「打开」 |
| 数量不再减少但还有课 | 剩余的都是已评过/异常项 | 看输出的「跳过」计数，正常现象 |
| 书签点了没反应 | 停在列表页而非填写页 | 先点进「立即评价」再点书签 |

---

## 已知边界

- 只适配北师大研究生评教系统（`ss.bnu.edu.cn/www/dd/vue/spa/pjxt`）。换站点要改配方的 5 段 JS。
- 校外通过 WebVPN 访问时 URL 被网关改写，L1/L2 的 `list_url` 会失配；**L3 书签不受影响**，因为它只在页面上下文执行。
- 调试端口开着时，本机任何程序都能控制那个浏览器实例。用完可以关掉专用窗口。

---

## 协作与致谢

| 角色 | 谁 |
|------|-----|
| 需求、验收口径、页面真实行为（「评完自动刷新回首页」的循环规律）、填写内容与最终提交 | wfcsilence |
| 引擎实现、配方 JS、三层封装、文档 | WorkBuddy Agent（模型 DeepSeek-V4.1-Flash） |

