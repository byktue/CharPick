改动已完成并通过语法检查；我也补了文档说明。现在我准备把你关心的“状态流转、任务日志、L2合并上传、summary落库”逐项对应给你，并附上本次验证结果和一个可直接执行的完整命令。

已按你的状态机和任务日志要求，把后端链路补齐到可执行状态，核心是“点击开始后先写 running，再在章节提取与 summary 入库完成后写 parsed + completed”。

**本次已完成**
1. 任务状态与 parse_status 流转
2. 在 [workflow_runner.py:16](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html) 增加了完整控制流：
3. 远程模式启动时先调用初始化，写入 source_files.parse_status=running，并创建 chapter_extraction 任务
4. 章节提取中更新任务进度（40 -> 70 -> 100）
5. 失败时统一写 source_files/books/task 为 failed
6. 逐章成功后可自动跑 summary，并写 summary 任务（running -> completed）
7. 对应实现入口在 [remote_persistence.py:214](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html) 和 [remote_persistence.py:285](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
8. extraction_tasks 任务表写入
9. 新增了通用任务创建/更新方法：
10. [remote_persistence.py:127](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
11. [remote_persistence.py:154](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
12. chapter_extractions 按书+类型合并并上传 OSS
13. 已把 L2 从“逐章单条”改为“按 extractor_type 合并整书 JSON 后上传 OSS，再写库”
14. 目前支持 character、plot、item、location、full 五类聚合
15. 写入字段是 book_extraction_json_local_url 和 book_extraction_json_oss_url
16. 逻辑在 [remote_persistence.py:435](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
17. summary 入库与 OSS 目录写入
18. summary_json 与 summary_md 同步上传 OSS
19. summary.content_local_url 写本地 summary 目录
20. summary.content_oss_url 写 OSS 对应维度目录
21. 逻辑在 [remote_persistence.py:579](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
22. 依赖与文档
23. 新增 OSS SDK 依赖： [requirements.txt:16](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
24. README 已同步你现在的真实行为（状态流转、任务类型、OSS 变量）： [README.md:39](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html), [README.md:172](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)

**你关心的状态机对应关系**
1. 未提取：对应 source_files.parse_status=pending（数据库默认）
2. 提取中：点击开始后立即写 running（初始化阶段已实现）
3. 提取完成：章节提取聚合上传成功后写 parsed（已实现）
4. 失败兜底：任一异常写 failed（已实现）

**验证结果**

1. 语法检查通过：remote_persistence/workflow_runner 可正常编译
2. 运行了测试命令 pytest [test_llm_dispatcher.py](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html) -q，出现 1 个失败，但失败点在 llm_dispatcher 的 card 过滤逻辑（现有基线问题），不在本次改动文件

**可直接执行的完整链路命令（远程上传 + summary）**

1. 先安装新增依赖：pip install -r [requirements.txt](vscode-file://vscode-app/e:/Microsoft%20VS%20Code/560a9dba96/resources/app/out/vs/code/electron-browser/workbench/workbench.html)
2. 执行：  
    python -c "from backend.workflow_runner import run_l0_to_l2_pipeline; import json; r = run_l0_to_l2_pipeline(source_path='data/神游.txt', source_type='txt', source_file_id='sf_demo_sync_001', file_name='神游.txt', filter_noise=True, upload_chapters_to_remote=True, upload_summary_to_remote=True, run_summary=True, user_id='u_demo_001', username='demo_user', book_id='b_demo_001', book_title='神游'); print(json.dumps(r.get('remote_persist'), ensure_ascii=False, indent=2))"

后续你如果愿意，我可以继续做两件事：

1. 把 card 任务也接进同一套 extraction_tasks 进度链路（summary 后按角色名触发，模拟前端传输了“石野”这个名字）
2. 修复当前 llm_dispatcher 的 card 测试失败点（避免无关章节标题进入角色上下文）