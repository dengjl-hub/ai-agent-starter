# 也可以直接用官方 Python 镜像，这里用 uv 镜像加速依赖安装
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# 先拷贝依赖文件，利用 Docker 层缓存
COPY pyproject.toml ./
COPY README.md ./

# 安装依赖（不安装项目本身，先装依赖以利用缓存）
RUN uv pip install --system --no-cache-dir \
    "fastapi>=0.115.0" \
    "uvicorn[standard]>=0.30.0" \
    "pydantic>=2.9.0" \
    "pydantic-settings>=2.5.0" \
    "openai>=1.50.0" \
    "httpx>=0.27.0" \
    "python-dotenv>=1.0.0" \
    "rich>=13.8.0"

# 拷贝项目代码
COPY src/ ./src/
COPY tests/ ./tests/
COPY examples/ ./examples/

# 安装项目本身
RUN uv pip install --system --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "ai_agent_starter.main:app", "--host", "0.0.0.0", "--port", "8000"]
