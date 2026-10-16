# 需求、代码与验收追溯

基线：0.4.0 / `e2d33c335b7aface39e6c0eed29e61df5b5ff684`。目标：[PRD](../product/PRD.md)与[架构](ARCHITECTURE.md)中的现状说明可逐项核验。

## 1. 验证记录

- 环境：Windows，Python 3.11；项目 `.venv` 使用 system-site-packages，仅在该环境安装 markdown 3.11.1、mcp 2.3.0 等依赖；未修改全局依赖或仓库 requirements。
- 初次 `python -m pytest -q tests`：88 passed、6 failed、1 skipped。失败为 GBK 编解码与缺 markdown；MCP 未安装所以跳过。
- 补齐依赖后 `.\.venv\Scripts\python -X utf8 -m pytest -q tests`：**95 passed in 8.63s**；MCP 用例执行，无跳过。
- `python -m radar --help`：exit 0；在 GBK 终端可有符号显示问题，运行文件读写另需 UTF-8 模式。
- 没有执行付费 sources/daily/keywords/pains，没有发送邮件、OAuth 授权或发布包；外部真实数据/可用性/费用不在此测试结果内。
- CI 配置声明 Python 3.10/3.12，不能用本地 3.11 的结果替代远程 CI。文档链接/证据符号检查及审查轮次见[工作记录](../workflows/prd-architecture-control.md)。
- 用户追加的[异模型验证](../reviews/code-review-20261016-204502.md)：分别以gpt-6-astra、gpt-6.1-sol配置派发PRD/架构审查，4项文档偏差已修复，两路修订复核均PASS；独立测试各95 passed（4.06s / 3.53s）。这更新前序自审结论，不把额外离线探针混称为原有单元测试。

## 2. 功能矩阵

测试均位于 [tests/test_radar.py](../../tests/test_radar.py)，名称可直接搜索。每行列举代表用例，并不表示覆盖该功能全部分支。

| 需求 | 实现入口 / 真源 | 可核验行为与代表测试 | 未覆盖 / 限制 |
|---|---|---|---|
| F01 配置 | [config.py](../../radar/config.py)：DEFAULTS/load/known；[__main__.py](../../radar/__main__.py)：main | 双向覆盖匹配：`test_known_terms_match_either_way`；缺 GSC site：`test_gsc_is_off_without_a_site`；语言模板：`test_every_text_has_both_languages` | 配置缺失/非法范围主要静态核验；无完整 schema 校验 |
| F02 X/HF | [sources.py](../../radar/sources.py)：novel_names/x_new/hf_new/base_name；[terms.py](../../radar/terms.py)：names | `test_x_reports_a_new_name_two_accounts_used`、`test_x_skips_names_already_in_the_vocabulary`、`test_x_one_account_needs_likes_and_an_unmistakable_name`、`test_hf_reads_trending_models_and_spaces_and_merges_a_model_with_its_demo` | 单账号多帖点赞只取首次遇到项由源码及异模型离线反例确认，非原有测试覆盖；真实推文/API/HF和部分快照失败未线上验收 |
| F03 GitHub | [breakout.py](../../radar/breakout.py)：score/breakouts/variants | `test_breakout_flags_a_fast_repo_and_skips_a_slow_one`、`test_breakout_flags_a_jump_since_yesterday_even_when_the_average_is_low`、`test_breakout_variants_include_handle_and_display_name` | 作者异常仅兜底OSError；畸形响应在快照已写后失败、重跑缺首次线索由异模型及主agent mock反例确认，非原有测试覆盖；真实限额/查询截断/30天窗口未线上验收 |
| F04 sitemap/新站 | [sitemaps.py](../../radar/sitemaps.py)：diff/site_urls；[terms.py](../../radar/terms.py)：surges；[new_sites.py](../../radar/new_sites.py)：_calls/keep | `test_sitemap_diff_reports_a_word_new_urls_share`、`test_a_site_that_fails_keeps_its_snapshot`、`test_new_sites_query_needs_both_dates`、`test_new_sites_drop_domains_ranking_for_a_handful_of_terms` | robots 许可不自动检查；上游日期过滤与部分调用缺席未实测 |
| F05 收入/求助/教程 | [revenue.py](../../radar/revenue.py)：products；[asks.py](../../radar/asks.py)：asks；[pains.py](../../radar/pains.py)：tutorial_asks | `test_revenue_reports_growth_then_a_product_that_left_zero`、`test_revenue_without_a_key_says_it_is_off`、`test_asks_turns_reddit_requests_into_sized_jobs`、`test_tutorial_asks_only_for_leads_marked_one_click` | 第三方收入/帖子准确性、名称门槛与任务短语冲突不以 mock 证明；无持久化教程需求 |
| F06 合并/评分/保留 | [report.py](../../radar/report.py)：leads/named/to_record；[judge.py](../../radar/judge.py)：score；[opportunity.py](../../radar/opportunity.py)：tag | `test_leads_merge_a_term_seen_by_two_signals`、`test_names_lead_and_known_terms_are_not_recorded`、`test_judge_failure_leaves_rows_unscored`、`test_one_click_needs_a_tutorial_people_shared` | 模型评分/标记无生产准确率；同名实体冲突未解决；前 20 后排 known 的边界由源码确认 |
| F07 机会研究 | [usecases.py](../../radar/usecases.py)：names_to_read/due/run/parse/screen/relevant；[__main__.py](../../radar/__main__.py)：keyword_table | `test_only_things_are_read_for_generic_terms_not_words_that_surged`、`test_usecases_run_builds_one_table_and_reads_a_name_twice`、`test_screen_drops_loosely_related_keywords_and_keeps_all_when_the_call_fails`、`test_keywords_on_request_reads_every_name_now_and_leaves_the_record_alone` | per_day每次调用而非每日总额由源码及同日两次调用反例确认；重读repo上下文未保证；按需DR缓存副作用由调用链确认 |
| F08 趋势/估算 | [usecases.py](../../radar/usecases.py)：shape/own_per_day/bench_daily/measure/decide | `test_trends_last_two_days_are_not_a_rise`、`test_a_single_day_spike_on_a_small_term_is_not_a_rise`、`test_searches_a_day_follow_the_terms_own_volume_along_its_curve`、`test_decisions`、`test_names_and_big_generic_terms_take_their_shape_from_the_country` | 窗口锚点/含边界、旧序列仍rising、flat且日搜缺失→skip由源码及异模型离线反例确认；无新鲜度/排序/缺日校验；全球/国家规模口径不能互换，估算精度未证实 |
| F09 首页竞争 | [competition.py](../../radar/competition.py)：verdict/assess/ratings | `test_page_one_verdicts` 明确含 None/None→crowded；`test_a_crowded_rising_term_is_watched_not_prioritized` 验证降级/缓存/供给 | 部分 DR 缺失或空 SERP 并不必然报错；无真实排名可进入性的保证 |
| F10 GSC | [gsc.py](../../radar/gsc.py)：gsc_new/fresh_queries；[__main__.py](../../radar/__main__.py)：cmd_daily | `test_gsc_keeps_queries_the_earlier_window_never_saw`、`test_gsc_is_off_without_a_site` | OAuth、fresh data、25000 行截断未做真实验收；不入 leads 由独立调用链确认 |
| F11 历史/复盘 | [store.py](../../radar/store.py)：record/due/save_verdict/summary/leads；[review.py](../../radar/review.py)：plan_calls/rose/verdict/review | `test_store_upserts_and_merges`、`test_store_due_verdict_and_summary`、`test_review_sends_one_trends_task_per_call`、`test_review_stores_the_verdict`、`test_leads_command_lists_what_was_kept` | no_data 分母、负提前天数、终态不自动复盘、日期粒度由源码核验；未做并发写/损坏恢复测试 |
| F12 pains | [pains.py](../../radar/pains.py)：run/group/parse；[social.py](../../radar/social.py)：reddit/youtube_comments | `test_pains_groups_reviews_posts_and_comments_into_gaps` | 非代表性采样、重复索引、截断到前 120 条不等于市场频次；真实评论接口未验收 |
| F13 报告/邮件 | [__main__.py](../../radar/__main__.py)：cmd_sources/cmd_daily/_finish；[report.py](../../radar/report.py)：daily/sources/keyword_table；[notify.py](../../radar/notify.py)：send | `test_sources_run_writes_no_report_when_nothing_is_new`、`test_daily_run_writes_a_report_when_every_signal_is_down`、`test_daily_report_in_chinese`、`test_mail_html_renders_tables`、`test_mail_without_recipient_is_skipped` | 真投递/文件原子写/保留旧 out/部分入库错误未展示不由此保证 |
| F14 Skills/MCP | [mcp_server.py](../../radar/mcp_server.py)：recent_leads/keyword_table/run_radar；[skills](../../skills/new-term-radar/SKILL.md) | `test_mcp_tools_answer_and_never_print`、`test_skills_have_a_name_and_a_description`、`test_the_mcp_command_says_what_is_missing` | 客户端端到端、并发 redirect_stdout、线程取消和 1.x/2.x 版本矩阵未全面验收 |

## 3. 跨章节一致性规则

| ID | 不变量 / 描述限制 | 证据 |
|---|---|---|
| C01 | daily 有报告不等于每个数据源成功；通常 exit 0 不能作为健康断言 | __main__.run/cmd_daily；report._status_lines |
| C02 | 快照、DB、JSON、Markdown、邮件不共享事务 | snap.save、store.record/save_verdict、cmd_daily、_finish |
| C03 | keywords 不改 leads/重读记录，但可改缓存 | keyword_table→usecases.run(on_request=True)→competition.ratings |
| C04 | GSC 与教程需求不走名称入库；daily 的 usecase/cosearch 另行入库 | cmd_daily→report.to_record 与 report.usecase_leads |
| C05 | 待复盘用 reviewed_at IS NULL，日期资格由 SELECT 计算 | store.due/save_verdict |
| C06 | DB signals 是 kinds，DB notes 是报告 signals；name_score 是查询投影名 | store.record/leads |
| C07 | shape 与 review.rose 有不同时间/持续门槛，不能共用一套产品解释 | usecases.WORLD/COUNTRY/shape；review.rose |
| C08 | incomplete 与报告 cost 不是全链路健康/完整账单 | usecases.degraded；mcp_server._keyword_table；report._cost |
| C09 | cache/artifact 不是持久服务；artifact 未包含全部快照 | .github/workflows/radar.yml |
| C10 | fork 路径不代表 Registry 身份已迁移；UA 与版本号也不是同一字段 | pyproject.toml、server.json、.claude-plugin/plugin.json、radar.__init__ |

## 4. 差异、风险与责任归属

以下均为现有事实/限制的记录，不是本轮待修复的代码 finding。

| 风险 | 说明 | 分类 / owner / 去向 |
|---|---|---|
| R1 外部数据与费用 | README 历史示例/价格非当前验收；API 响应、模型判断和计费可能变化 | assigned to later work unit；项目维护者；接入与数据质量验收 |
| R2 写入/并发/恢复 | 快照非原子、缺全局锁、MCP 全局状态、部分入库错误未展示、no_data 终态 | assigned to later work unit；项目维护者；运行可靠性评估 |
| R3 本机环境 | 默认 GBK 和缺可选依赖会使测试/运行失败；本轮验证已用 UTF-8 + .venv 解决环境前置 | 验证前置 fixed in current slice；默认编码实现改进 assigned to later work unit；项目维护者；Windows 兼容性 |
| R4 发布与归属 | publish 构建依赖不同，fork 中 Registry/元数据仍指上游 | assigned to later work unit；项目维护者；发布核验 |

后续代码变更时，先更新实际规则及用例，再同步修改对应 F/C 行；禁止单改文档使其看似已实现。若要以未来 PRD 规划新功能，应另建目标文档并走新的目标确认。
