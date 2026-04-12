# Supabase 使用文档（CharPick）

本文面向 CharPick 项目，覆盖以下内容：
- 项目连接信息识别
- 数据库连接方式
- SQL 执行与验证
- 接口层集成建议
- 安全与运维建议

---

## 1. Supabase 组成说明

在本项目里，主要会用到：
1. PostgreSQL 数据库（核心存储）
2. API Key（前后端访问策略控制）
3. SQL Editor（执行建表与维护脚本）
4. 可选：Storage、Auth、Edge Functions

当前阶段（L0/L1/L2）重点只需要 PostgreSQL + SQL Editor。

---

## 2. 连接数据库的两种常见方式

### 方式 A：应用后端直连 PostgreSQL

适合 FastAPI 后端服务。
建议使用连接串：

```env
SUPABASE_DB_URL=postgresql://postgres:<db_password>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require
```

说明：
- 使用 SSL 必须带上 sslmode=require
- 建议只在后端环境中使用该连接串

### 方式 B：使用 Supabase Python SDK

适合调用 Supabase 平台能力（如 REST、Storage 等）。
安装：

```bash
pip install supabase
```

示例：

```python
from supabase import create_client

url = "https://<project-ref>.supabase.co"
key = "<service_or_anon_key>"
supabase = create_client(url, key)

resp = supabase.table("books").select("id,title,status").limit(10).execute()
print(resp.data)
```

注意：
- 服务端优先使用 service role key（仅后端保存）
- 前端只使用受限的 anon/publishable key，并结合 RLS

---

## 3. CharPick 一期库表说明

已落地文件：
- `database/001_init_auth_l0_l2.sql`

一期已建表：
1. users
2. auth_sessions
3. books
4. source_files
5. chapters
6. chapter_extractions

暂不包含：
- L3 汇总结果表（characters / items / storyline 等）

---

## 4. 执行 SQL 的推荐流程

1. 先在测试 Supabase 项目执行。
2. 打开 SQL Editor 执行 `database/001_init_auth_l0_l2.sql`。
3. 在 Table Editor 校验表结构。
4. 通过简单查询验证外键关系。

验证示例：

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```

---

## 5. 与 FastAPI 的集成建议

1. 将数据库连接串放在 `.env`，不硬编码。
2. 用户认证建议流程：
   - 注册：写入 users（password_hash）
   - 登录：校验密码后写入 auth_sessions
   - 接口鉴权：根据 access_token_jti 查询会话有效性
3. 任务处理建议：
   - 上传后先落 books / source_files
   - 切章落 chapters
   - 抽取结果落 chapter_extractions

---

## 6. 安全建议

1. 不在仓库提交真实密钥、数据库密码。
2. 若密钥曾暴露，立刻在 Supabase 控制台轮换。
3. 生产环境与测试环境分离，不共用数据库。
4. 后续启用 RLS 时，按 user_id 做严格隔离。

---

## 7. 常见故障排查

### 1) 连接超时
- 检查网络与防火墙
- 检查 host 是否为 db.<project-ref>.supabase.co
- 检查 SSL 参数是否带上

### 2) 认证失败
- 检查用户是否为 postgres
- 检查数据库密码是否最新

### 3) SQL 执行失败
- 先确认扩展已启用：pgcrypto、vector
- 再确认当前用户有创建表权限

---

## 8. 后续扩展建议

1. 新增 L3 表时，按迁移文件递增管理（002/003...）。
2. 引入 Alembic 管理迁移历史。
3. 增加初始化数据脚本（测试账号、测试书籍、测试章节）。
