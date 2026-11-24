# 给 AI Agent 的安装说明

这个仓库里有一个可直接安装的 Agent Skill：`L1_Agent用户/browser-form-automation/`。

用户把仓库链接发给你、并说「装上」「用这个帮我评教」时，**自己完成安装，不要让用户手动复制文件夹**。按下面三步做。

## 1. 安装到 Skill 目录

Windows（PowerShell）：

```powershell
$tmp = Join-Path $env:TEMP "pjxt-skill"
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
git clone --depth 1 https://github.com/wfcsilence/bnu-pjxt-auto.git $tmp
New-Item -ItemType Directory -Force "$env:USERPROFILE\.workbuddy\skills" | Out-Null
Copy-Item -Recurse -Force "$tmp\L1_Agent*\browser-form-automation" "$env:USERPROFILE\.workbuddy\skills\"
```

macOS / Linux：

```bash
tmp="$(mktemp -d)"
git clone --depth 1 https://github.com/wfcsilence/bnu-pjxt-auto.git "$tmp/repo"
mkdir -p ~/.workbuddy/skills
cp -R "$tmp/repo"/L1_Agent*/browser-form-automation ~/.workbuddy/skills/
```

> 用 `L1_Agent*` 通配符而不是写全目录名：那个目录里有中文，命令若被存成 UTF-8 的 `.ps1` 再由 Windows PowerShell 5.1 按 GBK 读取会变乱码、路径直接失效。本段所有命令均为 ASCII，可安全写进脚本。
>
> 重复执行是安全的：覆盖安装，不会嵌套出第二层同名目录，也不会动到别的 skill。

目标目录按工具替换：

| 工具 | 用户级目录 |
|------|-----------|
| WorkBuddy | `~/.workbuddy/skills/`（Windows 为 `%USERPROFILE%\.workbuddy\skills\`） |
| Codex / 其他 | 该工具自己的 skill 目录，或项目内 `.workbuddy/skills/` |

没有 `git` 时：下载 ZIP（`https://github.com/wfcsilence/bnu-pjxt-auto/archive/refs/heads/main.zip`）解压，再把其中的 `L1_Agent用户/browser-form-automation` 整个文件夹复制过去。

## 2. 校验

安装结果是 `.../skills/browser-form-automation/SKILL.md` 存在，**不要多套一层同名文件夹**：

```
skills/
└── browser-form-automation/
    ├── SKILL.md
    ├── scripts/{engine.py, run.py}
    └── recipes/bnu-pjxt.json
```

装完重载 skill 列表（WorkBuddy 需重启），确认能看到 `browser-form-automation`。

## 3. 使用

装好后按 `SKILL.md` 执行。三条硬约束：

1. **运行前先问用户四项内容**——选择题选项（好/较好/一般/较差/差）+ 三个填空（需要改进的地方 / 突出优点 / 打分），复述确认后才动手；
2. 浏览器必须用**独立 user-data-dir** 开 `--remote-debugging-port=9222`，登录由用户自己完成；
3. 不要用截图或坐标定位，全部走 CDP `Runtime.evaluate`。

## 环境要求

- Python 3.8+，**只用标准库**，不需要 pip 安装任何依赖
- Edge 或 Chrome
- 仅支持桌面系统
