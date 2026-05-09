# 🧾 Conventional Commits 规范
👉 commit 信息的目标不是“记录你做了什么”，而是“让别人一眼看懂这次改动的意义”。

## 1. 基本格式

```text
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

示例：

```text
feat(auth): support multi chat sessions
fix(upload): use book_file_url in books table
refactor(chat): split session state management
```

## 2. type 含义

- `feat`: 新功能
- `fix`: 修复 bug
- `refactor`: 重构（不新增功能、不修复 bug）
- `style`: 代码格式调整（不影响逻辑，如空格、缩进）
- `docs`: 文档改动
- `test`: 测试相关
- `chore`: 构建/工具/依赖等杂项

## 3. scope（推荐）

scope 用来说明影响模块，建议简短明确。

通用示例：

- `feat(auth): add JWT login`
- `fix(payment): handle timeout issue`
- `refactor(order): improve query performance`

结合本项目（NovelWeaver）推荐 scope：

- `auth`（登录注册、会话）
- `chat`（LLM 交互页、多会话）
- `upload`（上传与处理页）
- `books`（书籍数据读写）
- `oss`（对象存储）
- `api`（接口层）
- `ui`（样式与交互）
- `docs`（项目文档）

## 4. subject 编写建议

- 使用动词开头，简洁明确
- 尽量一句话说清改动价值
- 不要以句号结尾

推荐：

- `fix(chat): prevent page-level scrolling in chat view`
- `feat(chat): add conversation rename action`

不推荐：

- `fix bug`
- `update code`
- `一些修改`

## 5. 完整提交示例

```text
feat(upload): add OSS rollback on DB write failure

- rollback uploaded object when books insert fails
- return clear error message for rollback failure

Closes #123
```

## 6. 常用模板（可直接复制）

### 新功能

```text
feat(<scope>): <subject>

- <change 1>
- <change 2>
```

### 修复

```text
fix(<scope>): <subject>

- root cause: <reason>
- solution: <what changed>
```

### 重构

```text
refactor(<scope>): <subject>

- improve structure without behavior change
- simplify maintenance
```

## 7. 本仓库近期改动可参考写法

```text
feat(chat): support multi-session switching and rename
fix(auth): align users table key from id to user_id
fix(upload): remove source_files dependency and use books.book_file_url
style(chat): tighten topbar vertical spacing
docs(readme): update project structure and API module notes
```