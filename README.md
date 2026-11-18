# NeuroArchAI Platform

> AI 驱动的户型图装修设计助手 —— 上传一张户型图，自动生成空间布局、风格方案、配色、材料清单、预算报告，并实时渲染可交互的 **3D 户型预览**。

---

## 一、项目目标

用一句话概括：**让普通业主不请设计师也能快速拿到一份可落地、可分享、可导出的装修设计方案。**

用户上传户型图并填写面积、房间构成与风格偏好后，平台会调用 AI（或内置算法）
输出完整方案：空间动线建议、风格落地要点、配色方案、材料清单、预算构成图表，
并据此生成 **三维户型预览**；方案可保存、可导出 PDF、可设为公开后生成分享链接。

---

## 二、核心功能

1. **用户注册 / 登录** —— JWT 认证，密码 PBKDF2 加盐哈希存储。
2. **项目管理** —— 一个用户可管理多个项目（多套房），支持增删改查。
3. **户型图上传** —— 支持 PNG / JPG / WEBP，服务端校验类型与体积（默认 ≤ 10MB）。
4. **AI 方案生成** —— 四档引擎自动择优（详见第三节），产出完整方案与 Plotly 图表。
5. **3D 户型预览** —— 后端生成布局数据，前端 Three.js 实时挤压成三维户型，可拖拽旋转查看。
6. **PDF 报告导出** —— 一键导出含方案正文、配色、预算图表、材料清单与户型图的完整报告。
7. **保存与分享** —— 方案永久保存，可切换公开/私密，公开后生成只读分享链接（分享页同样支持导出 PDF）。

---

## 三、技术栈

| 层次 | 选型 |
| --- | --- |
| 后端 | Python 3.10+ · FastAPI · Uvicorn |
| 数据库 | SQLite（默认）· SQLAlchemy 2.x（可无缝切换 PostgreSQL） |
| 安全 | PyJWT · hashlib PBKDF2 |
| AI 编排 | LangGraph · CrewAI · 内置算法回退引擎 |
| 图表 | Plotly（服务端生成 JSON，前端 Plotly.js 渲染） |
| 3D | Three.js（前端实时建模，非预渲染） |
| PDF | ReportLab（中文用内置 CID 字体 STSong-Light） |
| 前端 | **React 18 + TypeScript + Tailwind CSS v4 + Vite** |
| 前端兜底 | 另保留一套免构建的原生 HTML/CSS/JS 页面 |
| 部署 | 本地运行 / Docker（多阶段构建）/ docker-compose |

### 双前端设计（兼顾灵活与省心）

后端会自动择优托管前端：

| 形态 | 触发条件 | 说明 |
| --- | --- | --- |
| **React（推荐）** | `frontend/dist` 存在 | 完整图形化界面：3D 预览、图表联动、PDF 下载 |
| **原生静态页** | 无 `frontend/dist` | 免 Node 构建，`python run.py` 即可跑通全部核心流程（含 3D 预览，Three.js 走 CDN） |

也就是说：**不装 Node 也能用**；想体验完整图形界面，构建一次 `frontend/` 即可。

---

## 四、四档 AI 引擎（稳健设计）

平台会**先用算法引擎算出确定性的骨架**（预算、材料、配色、图表、3D 布局），
再视配置决定是否用大模型来**增强方案文本**：

| 引擎 | 触发条件 | 说明 |
| --- | --- | --- |
| 🧠 LangGraph 多智能体 | 已装 `langgraph` 且配置了大模型 | `分析 → 设计 → 评审` 三阶段工作流 |
| 👥 CrewAI 多智能体 | 已装 `crewai` 且配置了大模型 | 空间规划师 / 室内设计师 / 造价顾问协作 |
| 🤖 单次大模型 | 配置了 Groq 或 Ollama | 直接调用一次生成 JSON |
| ⚙️ 算法回退引擎 | 上面都不可用，或 `LLM_PROVIDER=none` | 内置规则引擎，**零配置也能跑通** |

任何一步失败都会**静默降级**，绝不会因为没有模型而报错。

---

## 五、目录结构

```
NeuroArchAI-Platform/
├── app/                          # 后端
│   ├── main.py                   # FastAPI 入口：CORS / 路由 / 前端托管
│   ├── config.py                 # 全局配置（读取 .env）
│   ├── database.py               # 数据库引擎与会话
│   ├── models.py                 # ORM：User / Project / Design
│   ├── schemas.py                # Pydantic 请求响应模型
│   ├── security.py               # 密码哈希 + JWT
│   ├── deps.py                   # 依赖注入
│   ├── routers/
│   │   ├── auth.py               # 注册 / 登录 / 我的信息
│   │   ├── projects.py           # 项目 CRUD + 户型图上传
│   │   ├── designs.py            # 方案生成 / 查询 / 分享 / PDF 导出
│   │   └── admin.py              # 管理后台：用户列表 / 启停 / 统计
│   ├── ai/
│   │   ├── pipeline.py           # 生成编排器（核心入口）
│   │   ├── llm_provider.py       # LLM 抽象：Groq / Ollama / none
│   │   ├── fallback.py           # 算法引擎 + 风格预设库
│   │   ├── layout3d.py           # 3D 户型布局生成（kd-tree 切分）
│   │   ├── graph.py              # LangGraph 工作流（可选）
│   │   ├── agents.py             # CrewAI 多智能体（可选）
│   │   └── prompts.py            # 提示词模板
│   └── services/
│       ├── visualization.py      # Plotly 图表生成
│       ├── report.py             # PDF 报告生成
│       └── storage.py            # 上传文件存储
├── frontend/                     # React + TS + Tailwind 前端（Vite）
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── dist/                     # 构建产物（由后端托管）
│   └── src/
│       ├── main.tsx / App.tsx
│       ├── api.ts                # API 客户端 + 登录态 + PDF 下载
│       ├── types.ts              # 与后端模型对应的类型
│       ├── toast.ts              # 轻量提示条
│       ├── components/
│       │   ├── Layout.tsx        # 全站布局与导航
│       │   ├── DesignView.tsx    # 方案正文（详情页/分享页共用）
│       │   ├── Room3D.tsx        # Three.js 3D 户型预览
│       │   ├── PlotlyChart.tsx   # 图表渲染
│       │   └── Toaster.tsx
│       └── pages/                # Home / Login / Studio / Design / Share / Admin
├── static/                       # 免构建原生前端（兜底）
│   ├── css/style.css
│   ├── index.html / login.html / studio.html / design.html / share.html
│   └── js/
│       ├── common.js             # API 封装 / 导航 / PDF 下载
│       ├── studio.js / design.js / login.js / share.js
│       └── room3d.js             # 3D 户型预览（ES Module + importmap）
├── scripts/
│   ├── create_admin.py           # 创建 / 提升管理员账号
│   ├── verify_docker.ps1         # 本地 Docker 构建 / 运行校验脚本
│   └── push_to_github.ps1        # 一键推送本项目到 GitHub
├── start.bat / start.ps1         # 启动脚本（自动定位 Python，绕过 PATH 问题）
├── .github/workflows/ci.yml      # CI：pytest + 前端构建 + Docker 冒烟
├── tests/                        # 测试
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_admin.py
│   └── test_ai_multiagent.py
├── uploads/                      # 户型图存储
├── data/                         # SQLite 数据库
├── requirements.txt
├── requirements-optional.txt     # LangGraph / CrewAI（可选）
├── .env.example
├── Dockerfile                    # 多阶段构建
├── docker-compose.yml
├── .dockerignore
└── run.py
```

---

## 六、快速开始

### 0. 环境准备

- Python **3.10 或更高**（本项目在 3.13 上验证通过）
- Node.js **18+**（仅在需要构建 React 前端时；不装也能用原生页）
- Docker（仅在需要容器化部署时）

### 1. 进入项目目录

```bash
cd NeuroArchAI-Platform
```

### 2. 创建并激活虚拟环境

**Windows（PowerShell / CMD）**

```bat
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装后端依赖

```bash
pip install -r requirements.txt

# 可选：多智能体编排（体积较大；装不上可跳过，平台会自动降级）
pip install -r requirements-optional.txt
```

### 4. 配置环境变量

```bash
copy .env.example .env      # Windows
cp .env.example .env        # macOS / Linux
```

然后在三种方式中选一种（详见 `.env.example` 注释）：

**选项一：Groq（推荐新手，免费且快）**

```env
LLM_PROVIDER=groq
GROQ_API_KEY=你的_Groq_API_Key
```

**选项二：Ollama（完全本地，隐私最佳）**

```bash
ollama run llama2
```

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**选项三：算法回退（零配置）**

```env
LLM_PROVIDER=none
```

### 5. 构建前端界面（可选但推荐）

```bash
cd frontend
npm install
npm run build      # 产物输出到 frontend/dist，后端会自动托管
cd ..
```

> 跳过这一步也能运行，页面会回退到 `static/` 里的免构建版本。

### 6. 验证依赖

```bash
python -c "import fastapi, sqlalchemy, plotly, jwt, httpx, reportlab; print('✅ 核心依赖均已就绪！')"

# 若装了可选依赖（LangGraph / CrewAI）
python -c "import langgraph, crewai; print('✅ 多智能体依赖已就绪！')"
```

### 7. 启动服务

```bash
python run.py
# 或： uvicorn app.main:app --reload
```

浏览器打开 **http://127.0.0.1:8000** 即可。

- 接口文档（自动生成）：`/docs`
- 健康检查：`/api/health`（会返回当前 AI 引擎与前端形态）

### 前端开发模式（热更新）

```bash
cd frontend
npm run dev        # http://127.0.0.1:5173，已配置代理到后端 8000 端口
```

---

## 七、Docker 部署

```bash
# 一键构建并启动（多阶段：Node 构建前端 → Python 运行）
docker compose up -d --build

# 查看日志 / 停止
docker compose logs -f web
docker compose down
```

或使用原生 Docker：

```bash
docker build -t neuroarchai .

# 需要容器内也支持多智能体编排时：
docker build --build-arg INSTALL_OPTIONAL=true -t neuroarchai .

docker run -d -p 8000:8000 \
  -e LLM_PROVIDER=none \
  -v "%cd%/data:/app/data" \
  -v "%cd%/uploads:/app/uploads" \
  --name neuroarchai neuroarchai
```

访问 http://127.0.0.1:8000 。

> 说明：compose 文件中的环境变量采用 `${VAR:-default}` 形式，
> 会读取同目录 `.env`（存在则生效，不存在则用默认值），因此**没有 `.env` 也能启动**。

### 校验 Docker 构建

本机未装 Docker 时，有两种方式完成「真实构建验证」：

**方式一：本地脚本（已装 Docker 时）**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_docker.ps1
```

脚本会依次：检查 Docker 是否就绪 → 校验 `docker-compose.yml` →
构建镜像 → 启动容器并做健康检查，任一步失败都会给出明确原因。

**方式二：推到 GitHub，交给 CI（无需本地 Docker）**

仓库内置 `.github/workflows/ci.yml`，在 push / PR 时自动执行：

1. `pytest -q` 后端测试 + 前端 `npm ci && npm run build`（含类型检查）
2. `docker compose config` 校验
3. `docker/build-push-action` 真实构建镜像
4. 启动容器并轮询 `/api/health` 做冒烟测试

也就是说：**只要把仓库推到 GitHub，就能在云端得到一次真实的 Docker 构建结果。**

---

## 八、运行测试

```bash
pytest -q
```

覆盖内容：

- 健康检查、注册登录、鉴权失败
- 完整业务闭环：建项目 → 生成方案 → 分享 → 公开访问
- 算法引擎预算计算、未知风格回退
- 3D 布局结构（房间落在户型范围内）
- PDF 报告导出（私有接口 + 公开接口）
- LangGraph 工作流接线（用假 provider 验证，无需 API Key）

---

## 九、主要 API 一览

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| GET | `/api/health` | 健康检查（含引擎与前端形态） | 否 |
| POST | `/api/auth/register` | 注册 | 否 |
| POST | `/api/auth/login` | 登录 | 否 |
| GET | `/api/auth/me` | 当前用户 | 是 |
| GET | `/api/projects` | 项目列表 | 是 |
| POST | `/api/projects` | 新建项目 | 是 |
| GET | `/api/projects/{id}` | 项目详情 | 是 |
| PATCH | `/api/projects/{id}` | 更新项目 | 是 |
| DELETE | `/api/projects/{id}` | 删除项目 | 是 |
| POST | `/api/projects/{id}/floorplan` | 上传户型图 | 是 |
| POST | `/api/projects/{id}/designs` | 生成方案 | 是 |
| GET | `/api/projects/{id}/designs` | 方案列表 | 是 |
| GET | `/api/designs/{id}` | 方案详情 | 是 |
| PATCH | `/api/designs/{id}/share` | 切换公开 / 私密 | 是 |
| DELETE | `/api/designs/{id}` | 删除方案 | 是 |
| GET | `/api/designs/{id}/report` | 导出 PDF 报告 | 是 |
| GET | `/api/share/{token}` | 公开分享页数据 | 否 |
| GET | `/api/share/{token}/report` | 公开方案的 PDF 报告 | 否 |
| POST | `/api/auth/change-password` | 修改当前用户密码 | 是 |
| GET | `/api/admin/stats` | 全局统计（用户/项目/方案数） | 管理员 |
| GET | `/api/admin/users` | 用户列表（含项目/方案数） | 管理员 |
| PATCH | `/api/admin/users/{id}` | 启用/停用、授予/取消管理员 | 管理员 |

---

## 十、常见问题

**Q：没有 API Key 能用吗？**
能。保持 `LLM_PROVIDER=none`，平台用内置算法引擎生成方案；数据、图表、
3D 预览与 PDF 导出全部不受影响。

**Q：不装 Node 能用吗？**
能。跳过「构建前端界面」这一步即可，后端会自动回退到 `static/` 的免构建版本。

**Q：`pip install -r requirements-optional.txt` 失败？**
多智能体库依赖较多。可跳过，平台会自动降级到单模型 / 算法引擎。
（本项目已在 Python 3.13 上验证 `langgraph` 与 `crewai` 均可安装。）

**Q：3D 预览看不到？**
两套前端都支持 3D。请确认：① 浏览器支持 WebGL（现代浏览器默认支持）；
② 若使用免构建的原生页，3D 依赖通过 CDN 加载（three.js 与 Plotly），需能联网。

**Q：想换成 PostgreSQL？**
把 `.env` 里的 `DATABASE_URL` 改成
`postgresql+psycopg://user:pass@host:5432/dbname` 并安装对应驱动即可，其余代码无需改动。

**Q：从旧版本升级后报「no such column」？**
用户表的 `is_admin` / `is_active` 会在启动时**自动补列**；但更早版本新增的
`designs.layout3d` 不会自动补。最省事的做法是删除 `data/*.db` 让数据库重建（会清空数据）。

---

## 十一、安全与边界说明

- 密码仅存储 PBKDF2 加盐哈希，永不落库明文。
- 上传文件做 MIME + 扩展名 + 体积三重校验，并用随机文件名避免路径猜测。
- 所有项目 / 方案接口均做归属校验，越权访问一律返回 404。
- 分享链接仅在方案被显式设为公开后生效；公开报告接口同样校验公开状态。
- 生产环境请务必修改 `.env` 中的 `SECRET_KEY`。

---

## 十二、账号与权限管理

### 角色模型

| 角色 | 说明 |
| --- | --- |
| 普通用户 | 注册即获得，只能管理自己的项目与方案 |
| 管理员 | 额外拥有后台权限：查看全部用户、启用/停用账号、授予/取消管理员、查看全局统计 |

`users` 表新增两个字段：

- `is_admin`：是否为管理员（默认 `false`）
- `is_active`：账号是否启用（默认 `true`；停用后**登录与已有令牌都会失效**）

> 升级旧数据库时会自动补齐这两个字段（见 `app/database.py` 的轻量迁移），无需手动改表。

### 创建 / 提升管理员

```bash
# 创建管理员（邮箱已存在时会直接提升，并可选重置密码）
python scripts/create_admin.py --email you@example.com --username 你的名字 --password 'YourPass123'

# 只把已有用户提升为管理员（不改密码）
python scripts/create_admin.py --promote you@example.com

# 查看所有用户
python scripts/create_admin.py --list
```

### 管理后台页面

管理员登录后，顶部导航会出现「管理」入口，地址 `/admin`，可以：

- **全局统计**：总用户 / 启用中 / 管理员 / 项目数 / 方案数
- **用户管理**：启用或停用账号、授予或取消管理员
  （**不能停用或降级自己**，避免把自己锁在门外）
- **修改密码**：校验原密码后更新

### 修改密码（所有用户）

`POST /api/auth/change-password`，需提供 `old_password` 与 `new_password`（≥6 位）。

### 安全约定

- 所有 `/api/admin/*` 接口都经过 `get_current_admin` 依赖，非管理员一律 `403`。
- 账号被停用后，登录接口与携带旧令牌的请求都会被拒绝（`403`）。
- **不提供「删除用户」接口**，避免误删导致其项目与方案一并消失；需要时用「停用」代替。
