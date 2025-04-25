#!/bin/bash

echo "====== 开始打包明星脸相似度比对系统 ======"

# 确保停止所有运行中的服务
if [ -f "./stop.sh" ]; then
    echo "停止所有运行中的服务..."
    ./stop.sh
fi

# 创建临时目录
TEMP_DIR="facesim_package"
mkdir -p $TEMP_DIR

# 复制所有必要文件
echo "复制项目文件..."
cp -r backend $TEMP_DIR/
cp -r frontend $TEMP_DIR/
cp -r scripts $TEMP_DIR/
cp start.sh stop.sh README.md docker-compose.yml .env.example $TEMP_DIR/

# 清理不需要的文件
echo "清理不必要的文件..."
find $TEMP_DIR -name "__pycache__" -type d -exec rm -rf {} +
find $TEMP_DIR -name "*.pyc" -delete
find $TEMP_DIR -name ".DS_Store" -delete
find $TEMP_DIR -name "node_modules" -type d -exec rm -rf {} +
find $TEMP_DIR -name "dist" -type d -exec rm -rf {} +
find $TEMP_DIR -path "*/\.*" -delete

# 确保脚本有执行权限
chmod +x $TEMP_DIR/start.sh $TEMP_DIR/stop.sh

# 创建目录结构
mkdir -p $TEMP_DIR/data/media/celebrities
mkdir -p $TEMP_DIR/data/media/user_photos
mkdir -p $TEMP_DIR/data/static

# 创建日期标记用于版本号
DATE_TAG=$(date +"%Y%m%d")

# 创建ZIP包
echo "创建ZIP包..."
zip -r facesim_${DATE_TAG}.zip $TEMP_DIR

# 清理临时目录
echo "清理临时文件..."
rm -rf $TEMP_DIR

echo "====== 打包完成 ======"
echo "生成文件: facesim_${DATE_TAG}.zip"