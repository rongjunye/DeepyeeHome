# ==========================================================================
# NeuroArchAI Platform —— 多阶段容器镜像
#
# 阶段一：用 Node 构建 React + TS + Tailwind 前端
# 阶段二：Python 运行时，托管后端 API 与前端构建产物
# ==========================================================================

# ---------------- 阶段一：构建前端 ----------------
FROM node:22-alpine AS frontend-builder

WORKDIR /web

# 先装依赖，利用镜像层缓存
COPY frontend/package.json frontend/package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --no-audit --no-fund; \
    else npm install --no-audit --no-fund; fi

# 拷贝源码并构建
COPY frontend/ ./
RUN npm run build


# ---------------- 阶段二：Python 运行时 ----------------
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 核心依赖
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 可选：多智能体编排（体积较大，默认不装）
# 需要时：docker build --build-arg INSTALL_OPTIONAL=true .
ARG INSTALL_OPTIONAL=false
COPY requirements-optional.txt ./
RUN if [ "$INSTALL_OPTIONAL" = "true" ]; then pip install -r requirements-optional.txt; fi

# 后端代码与启动脚本
COPY app ./app
COPY run.py ./
COPY .env.example ./

# 前端构建产物 + 免构建兜底页
COPY --from=frontend-builder /web/dist ./frontend/dist
COPY static ./static

# 运行期目录
RUN mkdir -p data uploads

EXPOSE 8000

# 容器内健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
