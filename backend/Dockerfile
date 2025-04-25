FROM python:3.10-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目
COPY . .

# 创建媒体文件夹
RUN mkdir -p media/celebrities media/user_photos

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 对外暴露端口
EXPOSE 8000

# 运行服务
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "facesim.wsgi:application"]