# 新词雷达用户手册

适用：当前分支的“仅文件配置 + Bash 启动器”。历史 README 中通过环境变量或 AIsa CLI 登录读取凭证的方式，在本分支已不再使用。PRD/架构中的0.4.0历史基线与本次启动扩展应分别理解。

本手册不要求设置环境变量、不读取 `.env`，也不会把 JSON 密钥转成环境变量。所有项目凭证和服务地址直接从本地 `config.json` 读取；MCP 路径用命令行参数传入。脚本使用 Bash，不使用 PowerShell。

## 1. 启动后会发生什么

这是命令行采集程序，没有网页、端口或后台服务。默认启动执行一轮 `daily`：采集配置的来源、研究关键词、复盘到期线索，写报告后退出。MCP 是供兼容客户端连接的 stdio 进程，与日报命令不同。

“完整模式”要求配置 AIsa Key，并执行所有当前配置且满足调度条件的步骤；未填写的可选服务不启用，周信号并非每次都运行。不绕过缺失凭证，也不自动换成免费模式。真实调用按供应商计费，费用依账号数、名字数和可选功能变化。

## 2. 依赖

| 依赖 | Linux | Windows |
|---|---|---|
| Bash | 系统 Bash | Git for Windows 的 **Git Bash** |
| Python | Python 3.10+，推荐3.11/3.12；含venv和pip | Python 3.10+，含pip；安装时启用系统命令搜索，Git Bash可执行 `py -3` 或 `python` |
| Python 包 | 启动脚本 `setup` 安装 | 同左 |
| 网络 | 可访问配置的数据服务和Python包源 | 同左 |

核心采集使用标准库；邮件需要 markdown，MCP需要mcp；`requirements-launcher.txt`统一安装这两项。Search Console首次授权额外需要google-auth-oauthlib，不启用GSC时不用安装。pytest仅用于开发测试，不是启动必需项。

Linux可按发行版安装Python、pip和venv。例如Ubuntu/Debian终端：

```bash
sudo apt-get update
sudo apt-get install -y bash python3 python3-venv python3-pip git
```

安装后确认实际Python≥3.10。其他Linux发行版使用其包管理器；这里不声称所有发行版都使用apt。

Windows安装Python和Git for Windows后，打开 **Git Bash**，检查：

```bash
bash --version
py -3 --version
# 如果没有py命令，检查python --version
```

Windows脚本使用Windows Python与`.venv/Scripts/python.exe`；不要在WSL里运行它。WSL按Linux使用`start-linux.sh`。切换平台时分别创建对应平台虚拟环境，不复用Windows与Linux的`.venv`。

## 3. 安装项目依赖

Linux：

```bash
cd /path/to/new-term-radar
bash scripts/start-linux.sh setup
```

Windows Git Bash（本机路径）：

```bash
cd /d/Workspace/Codex/new-term-radar
bash scripts/start-windows.sh setup
```

setup会创建缺失的`.venv`、安装启动依赖；若没有config.json才复制config.example.json，不覆盖已有配置或密钥。setup不会采集或验证API Key。启动脚本不会自动创建定时任务、激活shell环境或写全局配置。

## 4. 修改本地配置文件

使用编辑器打开仓库根目录的`config.json`，以UTF-8保存。支持编辑器写入的UTF-8 BOM；JSON不能有注释、尾逗号或未转义反斜杠。不要编辑成`.env`格式。

### 4.1 凭证与服务地址

在现有JSON对象中编辑以下字段，不要把整个示例重复粘贴成第二个JSON对象：

```json
{
  "lang": "zh",
  "credentials": {
    "aisa_api_key": "在本机填写真实AIsa Key",
    "goanyapi_api_key": "",
    "github_token": "",
    "trustmrr_api_key": "",
    "resend_api_key": "",
    "email_from": "",
    "email_to": []
  },
  "services": {
    "aisa_router_base_url": "https://tools.aisa.one",
    "aisa_api_base_url": "https://api.aisa.one",
    "goanyapi_base_url": "https://api.goanyapi.com"
  }
}
```

上面是字段说明，不是可以直接使用的密钥。把AIsa字段的中文提示替换为真实Key；其他字段不用就留空。

| 字段 | 用途 | 是否必填 |
|---|---|---|
| credentials.aisa_api_key | X、名称判断、用途提词、搜索量/趋势/复盘等 | 本手册完整模式必填 |
| credentials.goanyapi_api_key | 相关查询、国家走势、域名评分、供给、扩展评论、教程搜索 | 可选 |
| credentials.github_token | GitHub查询/README访问 | 可选；不填仍可访问公开接口，但限额更低 |
| credentials.trustmrr_api_key | 收入信号 | 可选；不填该信号不启用 |
| credentials.resend_api_key | Resend邮件 | 仅使用`--mail`时必填 |
| credentials.email_from | 已在邮件服务验证的发件地址 | 仅邮件必填 |
| credentials.email_to | 收件人字符串数组，例如`["reader@example.com"]` | 仅邮件必填 |

服务地址通常保持默认。需要使用兼容服务时，只修改对应`services`字段；必须HTTPS，不接受URL内用户名/密码、查询参数或fragment。不要把Key放在URL里。修改地址不代表所有供应商的协议/工具路由都兼容。

`credentials`与`services`会检查未知字段和类型；其他业务配置仍主要采用既有默认值/浅合并规则，并没有完整schema校验。后续重新加载不含凭证的配置会清空旧凭证，不沿用之前的Key。

config.json已被gitignore排除，但它包含明文密钥，仍需限制本机权限、单独安全备份，不要提交、截图、分享或把报告连同整个目录打包公开。自定义配置文件名不会自动被现有gitignore覆盖；建议存于已忽略的`state/`下或自行添加忽略规则。

Linux可执行`chmod 600 config.json`限制为当前用户读写；Windows应使用文件属性中的安全权限限制访问，Git Bash的chmod不能替代Windows ACL检查。

### 4.2 监控账号、网站与输出语言

```json
{
  "lang": "zh",
  "x_accounts": {
    "labs": ["AnthropicAI", "OpenAI"],
    "bloggers": []
  },
  "sitemaps": {},
  "topics": {},
  "known_terms": ["你已经覆盖的词"],
  "stop_words": []
}
```

示例config包含较多账号和网站；不代表必须监控全部。初次建议选自己关注的少量账号，删除无关sitemap项，减少耗时与调用。`known_terms`用于已覆盖标记和部分入库过滤，不是全局删除规则；`stop_words`扩展领域常用词过滤。中文报告不等于完整中文关键词识别能力。

如要监控网站，将sitemaps改为例如：

```json
{
  "sitemaps": {
    "my-directory": {
      "index": "https://example.com/sitemap.xml",
      "pause": 3,
      "strip_locale": true
    }
  }
}
```

这里example.com仅演示结构，务必换成真实允许访问的sitemap；索引文件可用`shards`正则筛子文件。应自行检查站点访问规则并设置请求间隔，程序不自动完成许可判断。`sitemaps:{}`可关闭该项。

### 4.3 模型、研究量与周信号

```json
{
  "judge": {"model": "gpt-4.1-mini", "min_score": 0.5},
  "usecases": {
    "per_day": 5,
    "model": "claude-sonnet-4-6",
    "recheck_days": 3,
    "benchmark": "gpts",
    "min_volume": 50,
    "min_daily": 300
  },
  "revenue": {"weekday": 0},
  "asks": {"weekday": 0},
  "new_sites": {"weekday": 0}
}
```

模型名称是当前示例值，不保证你的服务账号支持；调用失败时按实际服务文档改成兼容模型。`per_day`限制每次daily研究的名字数，没有每天累计额度；同日重复运行仍可能增加调用。周信号weekday中0表示周一，按运行机器日期判断；用`--revenue`、`--asks`、`--new-sites`可强制本次运行相应信号。

不希望自动研究时将usecases.per_day设0；这仍不等于其他付费调用全部关闭。完整参数和精确判断规则见[PRD](product/PRD.md)及[架构设计](architecture/ARCHITECTURE.md)。

### 4.4 可选Search Console与邮件

GSC：

```json
{"gsc": {"site": "sc-domain:your-domain.example", "token_file": "gsc_token.json"}}
```

token_file相对config.json所在目录。按[授权脚本](../scripts/gsc_auth.py)用自己的Google Desktop OAuth客户端生成只读token，放入该路径。授权脚本可在对应虚拟环境中执行：

```bash
# Linux
.venv/bin/python -E -X utf8 -m pip install google-auth-oauthlib
.venv/bin/python -E -X utf8 scripts/gsc_auth.py gsc_client.json
# Windows Git Bash：把上述解释器换成 .venv/Scripts/python.exe
```

脚本把gsc_token.json写当前目录；应从仓库根目录运行，或自行放到配置指定位置。未启用时保持`gsc:{}`。当前不从环境变量读取token。

邮件：填好三个邮件字段，并仅在确实希望发送时加`--mail`。完整模式默认不会发送邮件。

## 5. 预检与正式启动

Windows Git Bash：

```bash
cd /d/Workspace/Codex/new-term-radar
bash scripts/start-windows.sh check
bash scripts/start-windows.sh
```

Linux：

```bash
cd /path/to/new-term-radar
bash scripts/start-linux.sh check
bash scripts/start-linux.sh
```

`check`只检查配置、完整模式必填Key及配置的GSC token文件是否存在，不发网络请求；它不保证Key有效、余额充足或远程服务可用。Key缺失时直接退出，不伪造完整模式运行成功。MCP包在选择mcp时检查，邮件依赖与字段在传`--mail`时检查。

无参数等价于daily；报告默认`reports/report.md`和`reports/report.json`，状态默认`state/`。首次运行X/HF/sitemap建立基线，结果偏少不能当作市场平静。运行可能需要数分钟至数十分钟，多站点及大sitemap的首次采集可能更久，取决于配置、请求间隔、重试与网络，不能保证固定完成时长。采集中通常直到日报组装结束才集中输出，日志长时间不刷新不等于进程已退出。程序结束后Bash返回提示符，不是服务崩溃。

其他命令（Linux将脚本名换成start-linux.sh）：

```bash
bash scripts/start-windows.sh sources
bash scripts/start-windows.sh daily --skip x,hf
bash scripts/start-windows.sh keywords "a product name" --json
bash scripts/start-windows.sh pains "ai headshot" --json
bash scripts/start-windows.sh leads --days 7
bash scripts/start-windows.sh daily --out "reports/my report.md"
bash scripts/start-windows.sh daily --mail
bash scripts/start-windows.sh --help
```

脚本会切换到仓库根目录，默认路径都相对此目录；也可从任意目录用脚本绝对路径启动。参数含空格时必须加双引号。自定义`--out`的父目录应提前存在；默认reports目录会自动创建。已有报告会覆盖，需保存历史时使用不同文件名。sources无新词时不会写新报告，也不会删除旧报告。

使用独立配置/状态目录：

```bash
bash scripts/start-windows.sh daily --config "state/my config.json" --state "state/my-run"
```

`--config`也支持绝对路径；GSC相对配置文件目录，`--state/--out`相对仓库根目录。不要同时让多个写入进程使用同一state。

MCP客户端可以运行：

```bash
bash scripts/start-windows.sh mcp --config config.json --state state
```

它使用stdio，与兼容客户端连接，不会打开网页。手工在终端运行可能持续等待协议消息；用Ctrl+C退出。客户端应配置解释器/脚本参数和工作目录，不能通过环境变量传凭证。本启动器的mcp预检同样要求AIsa Key。

## 6. 输出与退出码

| 输出 | 说明 |
|---|---|
| reports/report.md | 日报，可用编辑器或Markdown阅读器打开 |
| reports/report.json | 结构化结果，先检查各来源error及keywords等字段 |
| reports/sources.md | 有新名称或错误时才生成的来源报告 |
| state/radar.db | 线索、首次/最近记录、复盘结论 |
| state/*.json.gz / state/sitemaps | 增量基线、研究记录和缓存 |

启动器退出码：0表示本命令正常完成；2表示预检或启动输入/文件错误；3表示daily已生成结果但结构化块有error/errors，属于不完整结果。底层CLI/依赖安装/中断也可能返回其自身非零码，不只这三个值。daily JSON并未暴露全部内部步骤，所以0也不是全链路数据完整证明。

没有GoAnyAPI或TrustMRR时会提示可选集成未启用，不把它们冒称为已采集。报告中flat、缺失估算、crowded、no_data的限制见PRD，不应只凭退出码或一列建议直接做商业决策。

## 7. 常见问题与维护

### X 监听返回 HTTP 504

504 是上游网关超时，调高本地 Python 超时不能延长上游网关期限。
X 采集现在每个账号单独请求，避免上游串行处理多个账号时整批超时，并实时输出账号进度。
真实单账号诊断曾用时44.1秒并成功返回20条帖子，接口报告费用为$0.003；这是一次观察，不保证其他账号耗时或价格相同。
本修复不自动重试；账号请求失败会停止本轮信号、保留完整旧词汇快照，并报告已成功账号数和已知费用。
失败HTTP请求是否已在上游产生费用无法由客户端确认，不能将本地记录的费用当作完整账单。
单账号仍可能因上游拥堵或数据服务故障返回504，届时需稍后手动重跑或向AIsa提供发生时间与工具名排查。
减少账号数可缩短整轮运行时间；每次一个账号主要降低单次请求的超时风险，不代表整轮一定更快。

- **找不到bash**：Windows请打开Git Bash；安装Git for Windows后重开终端。不要用PowerShell执行`.sh`。
- **Python版本太低/找不到Python**：安装3.10+，在Git Bash中确认py或python命令；Linux检查python3/venv包。
- **Virtual environment missing**：先执行对应脚本的setup。脚本不会静默安装或切换Python版本。
- **credentials.aisa_api_key缺失**：编辑本地config.json并保存真实Key，不要在聊天、命令行或环境变量里粘贴。check通过只代表非空，不代表有效。
- **HTTP401/403/余额不足/模型不存在**：按报告或终端错误检查服务账号、余额、模型与地址；不要把带隐私的数据整段公开。
- **JSON格式/字段错误**：使用双引号、删除注释和尾逗号，检查credentials/services拼写；合法完整示例见config.example.json。
- **中文乱码**：脚本固定传`-E -X utf8`，不依赖设置Python编码环境变量；Git Bash/编辑器也应使用UTF-8。
- **依赖下载失败**：先修复本机网络/证书再运行setup；脚本不会把安装失败当成启动成功。pip用隔离模式忽略用户配置及PIP环境覆盖。
- **Ctrl+C或网络失败后重跑**：部分快照可能已写入，不能保证恢复上一份报告；重跑也可能再次产生费用。
- **备份**：停止写入后备份整个state和配置；单独备份radar.db无法恢复所有来源基线。密钥与OAuth文件按私密数据保管。

本次脚本、仅文件配置实现及验证记录见[启动扩展验证记录](workflows/file-config-launchers-validation.md)。

迁移注意：仓库原有Skills与GitHub Actions示例包含历史环境变量配置，不能直接沿用其凭证注入方式；先以本手册完成本地文件配置。GitHub Actions模板需要单独迁移为安全生成配置文件后调用Linux启动脚本，本轮未启用或验证远程调度。
