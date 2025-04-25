#!/bin/bash

# 检查是否安装了必要的工具
command -v python3 >/dev/null 2>&1 || { echo "需要安装 Python3 但未找到，请先安装。"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "需要安装 npm 但未找到，请先安装。"; exit 1; }

# 使脚本在任何命令失败时退出
set -e

echo "====== 明星脸相似度比对系统启动脚本 ======"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "正在创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活Python虚拟环境..."
source venv/bin/activate

# 安装后端依赖
echo "安装后端依赖..."
pip install -r backend/requirements.txt

# 检查是否存在.env文件
if [ ! -f ".env" ]; then
    echo "创建.env文件..."
    cp .env.example .env
    echo "请编辑.env文件并配置您的Face++ API密钥和其他设置"
else
    echo "已检测到.env文件"
fi

# 确保.env文件被正确加载
echo "确保安装python-dotenv库..."
source venv/bin/activate
pip install python-dotenv

# 创建或修改.env文件加载代码
echo "检查Django设置文件中的.env加载代码..."
SETTINGS_FILE="backend/facesim/settings.py"

if ! grep -q "import dotenv" $SETTINGS_FILE; then
    echo "添加dotenv加载代码到Django设置文件..."
    TMP_FILE=$(mktemp)
    cat > $TMP_FILE << 'EOL'
import os
from pathlib import Path
import dotenv

# 加载.env文件
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)

EOL
    sed -i '1s/^/from pathlib import Path\nimport os\n/' $SETTINGS_FILE
    sed -i '/^import os/d' $SETTINGS_FILE
    sed -i '/^from pathlib import Path/d' $SETTINGS_FILE
    cat $TMP_FILE > tmp_settings && cat $SETTINGS_FILE >> tmp_settings && mv tmp_settings $SETTINGS_FILE
    rm $TMP_FILE
fi

# 初始化数据库并创建超级用户
echo "初始化数据库..."
cd backend
python manage.py migrate

# 检查是否已有超级用户
echo "检查超级用户..."
USER_EXISTS=$(python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'facesim.settings')
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print(User.objects.filter(is_superuser=True).exists())
")

if [ "$USER_EXISTS" = "False" ]; then
    echo "创建超级用户..."
    python manage.py createsuperuser
fi

# 在后台启动Django服务器
echo "启动Django后端服务器..."
python manage.py runserver 0.0.0.0:8000 > ../django.log 2>&1 &
DJANGO_PID=$!
echo "Django服务器已在端口8000上启动 (PID: $DJANGO_PID)"
echo $DJANGO_PID > ../django.pid

# 返回到项目根目录
cd ..

# 安装前端依赖并启动
echo "安装前端依赖..."
cd frontend
npm install

echo "启动Vue前端开发服务器..."
npm run serve > ../vue.log 2>&1 &
VUE_PID=$!
echo "Vue服务器已在端口8080上启动 (PID: $VUE_PID)"
echo $VUE_PID > ../vue.pid

cd ..

echo "====== 系统启动完成 ======"
echo "后端API运行于: http://localhost:8000/api/"
echo "前端页面运行于: http://localhost:8080/"
echo "管理后台地址: http://localhost:8000/admin/"
echo ""
echo "提示: 日志文件保存在 django.log 和 vue.log"
echo "要停止服务，请运行 ./stop.sh"