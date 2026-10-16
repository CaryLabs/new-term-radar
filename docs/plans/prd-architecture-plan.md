# PRD 与架构文档整理计划

## Gate 与目标确认

- Work unit：`prd-architecture`；gate：plan；状态：待 plan review。
- 仓库：CaryLabs/new-term-radar；基线：`e2d33c335b7aface39e6c0eed29e61df5b5ff684`（0.4.0）。
- 分支：`docs/prd-architecture`；base：`main`。
- 用户确认：2026-10-16，用户在确认分支、范围、验收和完整 Gateflow 路径的提案后回复“好的”。这是本轮 binding scope contract。
- 目标：为接手者提供可追溯到现有代码的中文产品 PRD、架构设计及证据索引。
- 动机：README 主要介绍使用方式；缺少集中说明业务规则、数据契约、状态生命周期和能力限制的设计基线。
- 成功信号：读者能从需求查到实现/测试，从架构图定位真实入口、数据流、存储和失败行为；不会把未来设想、README 宣传或测试模拟结果当作生产承诺。
- 非目标：修改业务代码、修复现存缺陷、接入新服务、引入 Web/SaaS 架构、定义未经用户确认的增长目标、运行付费采集、合并 PR。

## 直接证据与设计判断

- `radar/__main__.py` 定义 sources/daily/keywords/leads/pains 及 mcp 分发，编排同步采集和报告。
- `radar/config.py` 是默认配置真源；`config.example.json` 仅为示例。
- `radar/store.py` 定义 SQLite leads 表，`radar/snap.py` 实现 gzip JSON 快照。
- `radar/usecases.py`、`competition.py`、`review.py` 定义机会判断与复盘规则；不得用 README 的简化叙述覆盖实际条件。
- `radar/mcp_server.py` 复用 CLI，stdio 传输；`.github/workflows/radar.yml` 定义共享状态的定时运行。
- 第一性原理：这是文档逆向建模，不是产品重构。最小方案是在现有 docs 中增加 Markdown 与 Mermaid，不引入文档框架、渲染依赖或运行时抽象。

## 唯一实施 slice：S1 可追溯的现状文档基线

- 结果：PRD、架构和证据索引互相链接，完整描述一个从信号到复盘的使用闭环。
- 允许文件：`docs/README.md`、`docs/product/PRD.md`、`docs/architecture/ARCHITECTURE.md`、`docs/architecture/TRACEABILITY.md`；流程证据限 `docs/plans/`、`docs/reviews/`、`docs/workflows/`。不改现有源代码/测试/配置/README。
- 前置：plan review、必要 fix/re-review、accepted plan commit 完成。
- 内容：用户/场景、功能编号、优先级含义、业务规则、失败与空状态、验收映射、质量与成本边界；入口/模块/依赖图、同步调用顺序、字段/状态/缓存/调度/凭证/恢复说明。
- 规则精度：区分报告可见候选和入库线索、首次快照与绝对无结果、跳过与失败、报告成功与信号成功、按需 keywords 与 daily 的持久化差异、全球与国家 Trends、no_data 与 miss、多信号复盘统计。
- 关键链：CLI/MCP → config → signal modules → report.leads/judge → store.record → usecases/competition → review → report/notify；pains 是单独路径，不假设会写 leads。
- 接口/schema/state machine：本轮无变更；文档必须复述现存字段、状态转换、所有者和未保证行为。
- 输出原则：代码事实标为“现状”，文档推导标为“推导”，未验证项明确标注；不复制密钥或私有采集数据；代码证据使用仓库相对链接及符号名，减少行号漂移。
- 配置证据覆盖：DEFAULTS 与示例差异、环境变量/凭证来源、最终消费点及未校验参数边界。
- 验收：每条功能需求至少一个实现入口和可用测试或“未覆盖”说明；图与源码一致；相对链接全部可解析；无业务文件改动。
- 单 slice 原因：三个核心文档共同构成一个可验证的追溯闭环；拆成按文件实施的多个 gate 没有独立用户价值。
- 停止条件：代码/文档冲突无法在证据中澄清、需要扩大已确认范围、出现无关改动或远程权限阻断。

## 验证与审查

1. 阅读所有 runtime 模块、相关测试和工作流；记录关键规则与实际失败路径。
2. 运行 `python -m radar --help`、`python -m pytest -q tests`（环境可用时）；不调用真实收费 API。不为了文档新增镜像实现的单元测试。
3. 使用临时标准库脚本核验 Markdown 链接、功能编号和证据符号；运行 `git diff --check`，检查新增文件范围。
4. 按 planreview 做假设反证和目标对齐；按 deepreview 完成 slice、aggregate 和 PR 三轮审查，各有独立 artifact。修复仅限文档与本轮流程记录。
5. 验证重点：sources/daily 差异、模型失败、外部源缺失、快照部分写入、日期粒度、费用统计范围、MCP 并发与 stdout 边界、Actions cache 非持久存储。
6. 每轮审查记录 findings 裁决、fix/re-review 最终状态、未覆盖区域和 residual risk owner/destination。

## 风险与去向

- R1：真实 API 质量、延迟、当前价格和服务条款不通过本轮付费调用或网页核验；owner：项目维护者；分类：assigned to later work unit（接入验收）。文档只解释代码依赖与静态计费局限。
- R2：已有并发、部分写入、配置校验和统计语义限制仅描述，不修复；owner：项目维护者；分类：assigned to later work unit（运行可靠性评估）。
- R3：Windows/Python/MCP 依赖可能阻止测试；先检查环境并记录实际结果；若缺失，使用可用 runtime 或安装测试依赖后验证，不能声称通过未执行检查。
- 无 blocking open questions。不会把上述风险升级为新的产品目标或代码修复 slice。

## 提交与关闭

按 Gateflow 顺序创建 accepted plan、slice、aggregate review、PR review 的本地 commit；显式 stage 本轮文件。推送该工作分支并创建针对 main 的 draft PR，完成 PR 审查和最终 push 后记录 final closeout。
最终报告：文档路径、验证结果、findings 状态、剩余风险、draft PR URL、next entry point；不自动 merge。
