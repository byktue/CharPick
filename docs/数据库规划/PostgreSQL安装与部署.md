# PostgreSQL 安装与部署说明

## 1. 推荐方式
本项目建议使用 Docker 部署 PostgreSQL。原因很直接：

1. 环境一致，Windows、macOS、Linux 的启动方式都统一。
2. 不需要手动安装数据库服务，也不需要额外处理服务自启动。
3. 方便和 Alembic 迁移一起使用，后续换机器时只要迁移配置文件即可。

当前仓库已经提供了 [docker-compose.yml](../../docker-compose.yml) ，默认会启动一个 PostgreSQL 16 容器。

## 2. 启动 PostgreSQL
在项目根目录执行：
```bash
docker compose up -d postgres
```

默认账号信息如下：
- 数据库名：`charpick`
- 用户名：`charpick`
- 密码：`charpick`
- 端口：`5432`

如果本机 5432 已经被占用，可以修改 [docker-compose.yml](../../docker-compose.yml) 里的端口映射，例如改成 `5433:5432`。

## 3. 配置连接串
复制 [.env.example](../../.env.example) 为 `.env`，然后确认下面这行存在：
```bash
DATABASE_URL=postgresql+psycopg2://charpick:charpick@localhost:5432/charpick
```
如果你改了用户名、密码或端口，这里也要一起改。

## 4. 安装后端依赖
进入 Python 环境后安装依赖：
```bash
pip install -r requirements.txt
```

项目里已经加入了 `sqlalchemy`、`psycopg2-binary` 和 `alembic`，所以安装后就可以直接连 PostgreSQL 并执行迁移。

## 5. 执行 Alembic 迁移

首次部署或数据库空库时，执行：

```bash
alembic upgrade head
```

这会根据 [backend/database/alembic/versions/0001_initial_schema.py](../../backend/database/alembic/versions/0001_initial_schema.py) 创建全部基础表。

如果以后你修改了 ORM 模型，建议按下面流程更新：

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## 6. 启动后端

数据库起来以后，启动 FastAPI：

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

应用启动时会执行一次 `alembic upgrade head`，所以只要 `DATABASE_URL` 正确，表结构会自动保持最新。

## 7. 是否必须使用 Docker

不是必须，但建议使用。

你也可以在本机手动安装 PostgreSQL，然后把 `DATABASE_URL` 指向本机服务，例如：

```bash
postgresql+psycopg2://用户名:密码@127.0.0.1:5432/charpick
```

不过对于当前项目，Docker 更省事，也更适合和后续的 MinIO、Redis 一起做统一部署。

## 8. 最小部署流程

1. 启动 PostgreSQL 容器。
2. 配置 `.env` 里的 `DATABASE_URL`。
3. 安装 Python 依赖。
4. 执行 `alembic upgrade head`。
5. 启动 `uvicorn backend.main:app`。

## 9. 常见问题

### 9.1 连接失败

检查三件事：

1. 容器是否已经启动。
2. 5432 端口是否被占用或改动。
3. `DATABASE_URL` 是否和实际账号密码一致。

### 9.2 迁移失败

通常是数据库没有创建好，或者权限不够。先确认容器正常，再重试 `alembic upgrade head`。

### 9.3 想换成云数据库

把 `DATABASE_URL` 改成云厂商给你的 PostgreSQL 地址即可，Alembic 和后端代码不需要改。