# KidPlan 儿童周日程管理系统 - 设计文档

## 1. 项目概述

- **项目代号**: kidplan
- **使用场景**: 个人私有使用，单管理员账号
- **功能定位**: 孩子的每周日程规划与提醒
- **部署方式**: Docker Compose，线上服务器运行

---

## 2. 技术架构

### 2.1 后端

| 组件 | 技术 | 版本 |
|------|------|------|
| 语言 | Python | 3.11 |
| Web框架 | FastAPI | latest |
| ORM | SQLAlchemy | 2.0 |
| 调度 | APScheduler | latest |
| 认证 | PyJWT | latest |
| 数据库 | SQLite | - |

### 2.2 前端

| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | Vue | 3.x |
| 构建工具 | Vite | latest |
| UI库 | Element Plus | latest |
| 状态管理 | Pinia | latest |
| HTTP客户端 | Axios | latest |
| 路由 | Vue Router | 4.x |

### 2.3 部署

- Docker Compose 编排
- 前端: Nginx 托管静态资源 + 反向代理
- 后端: Python 3.11-slim 镜像
- 配置: 全环境变量驱动

---

## 3. 目录结构

```
kidplan/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── dependencies.py
│   └── routers/
│       ├── __init__.py
│       ├── auth.py
│       ├── schedules.py
│       └── settings.py
│   └── services/
│       ├── __init__.py
│       └── reminder.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api.js
│       ├── router/
│       │   └── index.js
│       ├── stores/
│       │   ├── auth.js
│       │   └── schedule.js
│       ├── views/
│       │   ├── Login.vue
│       │   ├── WeekView.vue
│       │   ├── Settings.vue
│       │   └── Logs.vue
│       └── components/
│           ├── ScheduleModal.vue
│           └── ScheduleBlock.vue
└── nginx.conf
```

---

## 4. 数据模型

### 4.1 Schedule（日程）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| title | String(100) | 日程标题，必填 |
| start_time | Time | 开始时间，必填 |
| end_time | Time | 结束时间，必填 |
| weekday | Integer | 星期几（1-7，周一为1），必填 |
| remark | String(500) | 备注，可选 |
| reminder_enabled | Boolean | 是否启用提醒，默认True |
| reminder_minutes | Integer | 提前提醒分钟数，默认10 |
| created_at | DateTime | 创建时间，自动填充 |
| updated_at | DateTime | 更新时间，自动填充 |

**约束**:
- `end_time` 必须晚于 `start_time`
- `weekday` 范围为 1-7

### 4.2 ReminderLog（提醒日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| schedule_id | Integer | 关联日程ID，外键 |
| schedule_title | String(100) | 日程标题（冗余，便于查询） |
| scheduled_time | DateTime | 计划发送时间 |
| sent_at | DateTime | 实际发送时间 |
| status | String(20) | 状态: pending/sent/failed |
| channel | String(20) | 发送渠道: dingtalk/lark |
| response | String(500) | 接口返回结果 |

### 4.3 SystemConfig（系统配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键，自增 |
| key | String(50) | 配置键，唯一 |
| value | String(500) | 配置值 |
| updated_at | DateTime | 更新时间 |

**默认配置项**:
- `default_reminder_minutes`: 默认提前提醒分钟数（默认10）
- `dingtalk_webhook`: 钉钉机器人Webhook地址
- `lark_webhook`: 飞书机器人Webhook地址

---

## 5. API 接口设计

### 5.1 认证接口

#### POST /api/auth/login
- **描述**: 管理员登录
- **请求体**:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "access_token": "string",
      "token_type": "bearer"
    }
  }
  ```
- **错误码**: 401（认证失败）

### 5.2 日程接口

#### GET /api/schedules
- **描述**: 获取指定周的所有日程
- **查询参数**:
  - `week_offset`: 周偏移量（0=本周，1=下周，-1=上周）
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": [
      {
        "id": 1,
        "title": "数学课",
        "start_time": "09:00",
        "end_time": "10:30",
        "weekday": 1,
        "remark": "带作业本",
        "reminder_enabled": true,
        "reminder_minutes": 10,
        "created_at": "2025-01-09T10:00:00",
        "updated_at": "2025-01-09T10:00:00"
      }
    ]
  }
  ```

#### POST /api/schedules
- **描述**: 创建日程
- **请求体**: ScheduleCreate schema
- **响应**: 创建的日程对象

#### PUT /api/schedules/{id}
- **描述**: 更新日程
- **路径参数**: id
- **请求体**: ScheduleUpdate schema
- **响应**: 更新后的日程对象

#### DELETE /api/schedules/{id}
- **描述**: 删除日程
- **路径参数**: id
- **响应**: 空对象

#### POST /api/schedules/copy-to-next-week
- **描述**: 复制当前周所有日程到下周
- **请求体**:
  ```json
  {
    "source_week_offset": 0,
    "target_week_offset": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "copied_count": 5
    }
  }
  ```

### 5.3 配置接口

#### GET /api/settings
- **描述**: 获取系统配置
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "default_reminder_minutes": 10,
      "dingtalk_webhook": "https://oapi.dingtalk.com/robot/send?...",
      "lark_webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    }
  }
  ```

#### PUT /api/settings
- **描述**: 更新系统配置
- **请求体**:
  ```json
  {
    "default_reminder_minutes": 15,
    "dingtalk_webhook": "string",
    "lark_webhook": "string"
  }
  ```
- **响应**: 更新后的配置

### 5.4 日志接口

#### GET /api/reminder-logs
- **描述**: 获取提醒日志列表
- **查询参数**:
  - `limit`: 返回条数（默认20，最大100）
  - `offset`: 偏移量（默认0）
- **响应**:
  ```json
  {
    "code": 200,
    "message": "success",
    "data": {
      "total": 50,
      "items": [
        {
          "id": 1,
          "schedule_id": 5,
          "schedule_title": "数学课",
          "scheduled_time": "2025-01-09T08:50:00",
          "sent_at": "2025-01-09T08:50:01",
          "status": "sent",
          "channel": "dingtalk",
          "response": "{\"errcode\":0}"
        }
      ]
    }
  }
  ```

---

## 6. 前端页面设计

### 6.1 登录页 (/login)

- 简洁的登录表单
- 用户名、密码输入框
- 登录按钮
- 错误提示（红色文字）
- 登录成功跳转到首页

### 6.2 周视图主页 (/)

#### 布局
- **顶部操作栏**:
  - 左侧: "上周" / "本周" / "下周" 切换按钮，当前周日期显示
  - 右侧: "复制本周到下周" 按钮，"设置" 按钮

- **主体区域**:
  - 横向表头: 周一至周日（显示日期如"周一\n01/13"）
  - 纵向时间轴: 6:00 - 22:00，每小时一格
  - 日程块: 按时间位置渲染在对应日期列
    - 启用提醒: 蓝色背景 `#409EFF`
    - 禁用提醒: 灰色背景 `#909399`
    - 显示标题和时间段

- **交互**:
  - 点击空白时间格: 弹出新增日程弹窗，预选对应时间和日期
  - 点击日程块: 弹出编辑弹窗
  - 弹窗内可删除日程

### 6.3 全局设置弹窗

- 钉钉Webhook地址输入框
- 飞书Webhook地址输入框
- 默认提前提醒分钟数（数字输入框，范围1-60）
- 保存按钮（即时生效）

### 6.4 提醒日志页面 (/logs)

- 列表展示近期提醒记录
- 列: 发送时间、日程标题、计划时间、发送状态、渠道
- 分页或加载更多
- 返回按钮回到周视图

---

## 7. 提醒服务设计

### 7.1 调度器配置

- 使用 APScheduler BackgroundScheduler
- 每分钟执行一次检查任务
- 启动时自动恢复未发送的待提醒

### 7.2 提醒检测逻辑

```
每分钟执行:
  1. 获取当前时间 now
  2. 计算提醒检测窗口: [now, now + 1分钟]
  3. 查询今天所有 enabled 的日程
  4. 对每个日程:
     - 计算 remind_at = schedule.start_time - reminder_minutes
     - 如果 remind_at 在检测窗口内:
       - 创建 ReminderLog (pending)
       - 发送通知
       - 更新 ReminderLog 状态
```

### 7.3 通知发送

支持两种渠道，可同时配置:

#### 钉钉机器人
- URL: `https://oapi.dingtalk.com/robot/send?access_token=xxx`
- 请求体:
  ```json
  {
    "msgtype": "text",
    "text": {
      "content": "【日程提醒】数学课\n开始时间: 09:00\n备注: 带作业本"
    }
  }
  ```

#### 飞书机器人
- URL: `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`
- 请求体:
  ```json
  {
    "msg_type": "text",
    "content": {
      "text": "【日程提醒】数学课\n开始时间: 09:00\n备注: 带作业本"
    }
  }
  ```

---

## 8. 环境变量配置

### 8.1 后端环境变量

| 变量名 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| `ADMIN_USERNAME` | 是 | - | 管理员用户名 |
| `ADMIN_PASSWORD` | 是 | - | 管理员密码 |
| `JWT_SECRET` | 是 | - | JWT密钥 |
| `DATABASE_PATH` | 否 | `./data/kidplan.db` | SQLite数据库路径 |
| `DEFAULT_REMINDER_MINUTES` | 否 | 10 | 默认提前提醒分钟数 |

### 8.2 前端构建时变量

| 变量名 | 说明 |
|--------|------|
| `VITE_API_BASE_URL` | API基础URL（生产环境为相对路径 `/api`） |

---

## 9. Docker 部署

### 9.1 服务架构

```yaml
services:
  backend:
    build: ./backend
    volumes:
      - ./data:/app/data
    environment:
      - ADMIN_USERNAME
      - ADMIN_PASSWORD
      - JWT_SECRET
      - DATABASE_PATH=/app/data/kidplan.db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
```

### 9.2 Nginx 配置

- 托管前端静态资源（`/`）
- 反向代理API请求（`/api` → `backend:8000`）
- 单页面应用路由回退（`try_files $uri $uri/ /index.html`）

---

## 10. 安全考虑

1. **认证**: 所有业务接口需携带有效JWT Token
2. **密码**: 环境变量传入，不存储明文
3. **CORS**: 后端配置允许的 origins
4. **数据**: SQLite文件持久化挂载，避免容器销毁丢失
5. **Webhook**: 敏感信息存储在服务端，不暴露给前端

---

## 11. 验收标准

- [ ] 可通过 docker-compose up -d 一键启动
- [ ] 登录后可进入周视图
- [ ] 可创建、编辑、删除日程
- [ ] 可切换周视图
- [ ] 可复本周日程到下周
- [ ] 可配置钉钉/飞书Webhook
- [ ] 定时提醒按配置正确触发
- [ ] 提醒日志正确记录
- [ ] 响应式设计，移动端可正常使用
