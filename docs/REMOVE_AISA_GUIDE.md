# remove-aisa 配置与启动

## 推荐：原业务配置与新供应商配置共存

无需迁移或改写原 `config.json`。使用项目根目录独立的 `config.providers.json` 保存新供应商的 providers、credentials 和 limits；它已加入 Git 忽略名单。业务账号、阈值、主题等继续从原文件读取。显式指定时，新供应商配置覆盖同名分组中的字段；旧 AIsa 凭据与地址只留在原文件，不传给新接口。模型任务使用新供应商文件中的 providers.llm.model。配置相对资源路径仍以原业务文件所在目录为准。

```bash
bash scripts/start-windows.sh check --config config.json --providers-config config.providers.json
bash scripts/start-windows.sh daily --config config.json --providers-config config.providers.json --state state/remove-aisa/run --out reports/remove-aisa/report.md
```

Linux 改用 start-linux.sh。MCP 同样支持 --providers-config 参数。文件不会自动加载，必须显式指定，避免悄悄改变旧配置行为。

下面的迁移方式是可选方案。此前创建的 state/remove-aisa/config.json 不会在上述命令中使用。原配置文件可以继续供旧版本代码使用；本分支已移除 AIsa 实现，未提供在同一分支切换回 AIsa 的运行模式。

本分支已接入独立供应商，离线回归通过；真实服务质量、覆盖率和账单尚未验收，不能据此宣布完整替代成功。原 `config.json` 不会自动迁移。旧版手册中的 AIsa 配置不适用于本分支。

## 1. 安装

需要 Python 3.10+。Windows 使用 Git Bash，在项目根目录执行：

```bash
bash scripts/start-windows.sh setup
```

Linux 安装 Python 及 venv 后执行：

```bash
bash scripts/start-linux.sh setup
```

setup 安装依赖；已有 config.json 不会被覆盖。开发测试另需安装 pytest。

## 2. 创建独立配置

Windows 的以下命令在 CMD 中执行；Linux 将 `.venv\Scripts\python.exe` 换成 `.venv/bin/python`。

```bat
.venv\Scripts\python.exe -m radar migrate-config --input config.json --out state/remove-aisa/config.json
```

迁移仅写新文件，不覆盖原文件、不复制 AIsa 凭据、不开网络。目标已存在时拒绝覆盖。也可复制 `config.remove-aisa.example.json` 为自己的配置。

编辑新文件的 credentials：

- deepseek_api_key：DeepSeek 官方模型密钥。providers.llm.model 设置账号实际支持的模型名；任务中的 model 可独立覆盖，迁移默认值需自行核对供应商支持情况。
- twitterapis_api_key：默认 X 时间线与搜索供应商。若选 TwitterAPI.io，将 providers.x.name 改为 twitterapi_io，并填 twitterapi_io_api_key。必须保留 X 监听与搜索。
- dataforseo_login、dataforseo_password：DataForSEO API 登录信息，承担搜索量、趋势、SERP、难度、新网站发现。
- reddit_client_id、reddit_client_secret：Reddit 官方应用凭据，需符合平台申请与授权要求。
- youtube_api_key：Google Cloud 启用 YouTube Data API v3 后创建的密钥。
- goanyapi_api_key、github_token、trustmrr_api_key：原独立来源的可选配置。邮件凭据仅在主动使用 --mail 时需要。

所有密钥只读 JSON。不要提交配置或把密钥发到聊天。适配器已实现不代表供应商有永久免费额度；X、SEO 和模型应以供应商账单为准。Reddit 的访问资格与限制也需独立确认。

## 3. 启动前检查与正式采集

Windows Git Bash：

```bash
bash scripts/start-windows.sh check --config state/remove-aisa/config.json
bash scripts/start-windows.sh daily --config state/remove-aisa/config.json --state state/remove-aisa/run --out reports/remove-aisa/report.md
```

Linux 将脚本替换为 `scripts/start-linux.sh`。check 只检查本地配置，不发网络请求。首次真实采集前，核对监控账号、模型和供应商额度，然后将 limits.network_enabled 改为 true。

limits.daily_requests / monthly_requests 是持久化的供应商请求次数上限，**不是金额硬上限**；分页和 OAuth 请求也可能占用次数。cache_ttl_seconds 控制成功结果缓存，有效期内相同查询可能读取旧数据；实时验收可设为 0。不能删除计费数据库来规避限制。

state 下保存 provider-usage.sqlite3、历史快照和运行锁。同一 state 不可并发；验收用独立 state，生产任务先不切换。供应商请求默认不自动重试，以免重复收费。失败和未验证数据不能当成零需求。

输出 Markdown 和同名 JSON。provider_usage 中未知费用保持未知；部分费用为供应商估计，不能当完整账单。DeepSeek token、YouTube 配额和已知费用分别记录，最终需要与供应商账单核对。

## 4. 可复现的离线验收

Windows CMD：

```bat
.venv\Scripts\python.exe -m radar.acceptance inventory
.venv\Scripts\python.exe -m radar.acceptance contracts
.venv\Scripts\python.exe -m radar.acceptance no-aisa
.venv\Scripts\python.exe -m radar.acceptance report
```

证据位于 state/acceptance/latest，包含日志、JUnit XML、摘要和验收报告。必须在含 tests 的源码仓库执行。模拟测试不会调用真实供应商，不能证明真实新鲜度、召回率、模型准确率或供应商底层来源。

完整验收按 [验收标准](plans/aisa-replacement-acceptance.md) 执行：13 类能力逐项真实验证、人工标注模型对照、7天14轮采集、真实14天复盘和费用对账。没有完成的项目必须保持 NOT_RUN；smoke/compare 自动化尚待后续实现。

## 5. 常见问题

- Legacy gateway configuration：仍使用旧配置，请迁移到独立文件。
- Network disabled：新配置默认禁止付费请求，确认额度后手动启用。
- Missing credential：填写对应 credentials 字段，check 不会显示密钥。
- 请求上限或分页不完整：记录待补采；核对预算与 max_pages，不把残缺结果当完整数据。
- HTTP 504/429：保留失败记录，核对供应商状态与限额；不自动循环重试。
- 服务商无数据：搜索量未知与 0 有区别，不能用模型编造补齐。

本轮未修改正式定时任务、未启用真实付费请求、未覆盖原配置。
