### 7. characters（角色总表，每一行 = 一个角色）
- id (PK) # 角色唯一 ID
- user_id (FK → users) # 所属用户
- book_id (FK → books) # 所属书籍
- name # 角色名（展示用）
- appearance_count INT # 出场次数
- first_appearance_chapter_id (FK → chapters) # 首次登场章节
- avatar_url # 头像
- status # 状态（未生成角色卡/静态全局角色卡/完整动态角色卡）
- created_at # 记录第一次生成角色卡的时间
- updated_at

### 8. character_versions（角色卡表）
- id（PK）# 版本ID
- user_id（FK → users）# 所属用户
- character_id（FK → characters）# 所属角色
- book_id（FK → books）# 所属书籍
- version_no # 版本号
- chapter_range # 适用章节范围
- profile_json（JSONB）# 该版本人设
- prompt_text # 生成用提示词
- is_default # 是否默认版本

### 9. items（物品表）
- id（PK）# 物品ID
- user_id（FK → users）# 所属用户
- book_id（FK → books）# 所属书籍
- name # 物品名称
- description # 描述
- owner_character_id（FK → characters）# 持有者
- first_appearance_chapter_id # 首次登场章节
- item_json（JSONB）# 物品详情

### 10. storyline_events（剧情时间线）
- id（PK）# 剧情事件ID
- user_id（FK → users）# 所属用户
- book_id（FK → books）# 所属书籍
- chapter_id（FK → chapters）# 所属章节
- event_title # 事件标题
- event_summary # 事件摘要
- participants_json（JSONB）# 参与角色列表
- location_id # 发生地点
- event_time # 事件时间

### 11. world_locations（世界观/地点表）
- id（PK）# 地点ID
- user_id（FK → users）# 所属用户
- book_id（FK → books）# 所属书籍
- name # 地点名称
- description # 描述
- related_chapter_ids（JSONB）# 关联章节
- location_type # 地点类型：城市/建筑/场景