#!/bin/bash

echo "====== 停止明星脸相似度比对系统 ======"

# 停止Django服务
if [ -f "django.pid" ]; then
    DJANGO_PID=$(cat django.pid)
    if ps -p $DJANGO_PID > /dev/null; then
        echo "停止Django服务器 (PID: $DJANGO_PID)..."
        kill $DJANGO_PID
        # 等待进程结束
        sleep 2
        if ps -p $DJANGO_PID > /dev/null; then
            echo "Django服务未正常退出，强制终止..."
            kill -9 $DJANGO_PID
        fi
    else
        echo "Django服务器已不再运行"
    fi
    rm django.pid
else
    echo "未找到Django PID文件"
fi

# 停止Vue服务
if [ -f "vue.pid" ]; then
    VUE_PID=$(cat vue.pid)
    
    # 检查主进程是否在运行
    if ps -p $VUE_PID > /dev/null; then
        echo "停止Vue主进程 (PID: $VUE_PID)..."
        kill $VUE_PID
        # 等待进程结束
        sleep 2
        # 如果进程仍在，强制终止
        if ps -p $VUE_PID > /dev/null; then
            echo "Vue服务未正常退出，强制终止..."
            kill -9 $VUE_PID
        fi
    else
        echo "Vue主进程已不再运行"
    fi
    
    # 查找并终止所有相关的node/npm进程
    echo "检查并终止所有相关的Vue子进程..."
    # 查找包含"node" 和 "vue-cli-service"的进程
    VUE_PIDS=$(ps aux | grep "[n]ode.*vue-cli-service" | awk '{print $2}')
    if [ ! -z "$VUE_PIDS" ]; then
        echo "发现Vue相关子进程，正在终止: $VUE_PIDS"
        for pid in $VUE_PIDS; do
            echo "终止进程 $pid..."
            kill $pid 2>/dev/null
            sleep 1
            # 如果进程仍然存在，强制终止
            if ps -p $pid > /dev/null; then
                echo "进程 $pid 未响应，强制终止..."
                kill -9 $pid 2>/dev/null
            fi
        done
    fi
    
    # 额外查找可能的webpack dev server进程
    WEBPACK_PIDS=$(ps aux | grep "[n]ode.*webpack" | awk '{print $2}')
    if [ ! -z "$WEBPACK_PIDS" ]; then
        echo "发现webpack相关进程，正在终止: $WEBPACK_PIDS"
        for pid in $WEBPACK_PIDS; do
            echo "终止进程 $pid..."
            kill $pid 2>/dev/null
            sleep 1
            if ps -p $pid > /dev/null; then
                echo "进程 $pid 未响应，强制终止..."
                kill -9 $pid 2>/dev/null
            fi
        done
    fi
    
    rm vue.pid
else
    echo "未找到Vue PID文件"
    
    # 即使没有PID文件，也检查是否有残留的Vue进程
    echo "检查是否存在残留的Vue进程..."
    VUE_PIDS=$(ps aux | grep "[n]ode.*vue-cli-service" | awk '{print $2}')
    WEBPACK_PIDS=$(ps aux | grep "[n]ode.*webpack" | awk '{print $2}')
    
    if [ ! -z "$VUE_PIDS" ] || [ ! -z "$WEBPACK_PIDS" ]; then
        ALL_PIDS="$VUE_PIDS $WEBPACK_PIDS"
        echo "发现残留的前端相关进程，正在终止: $ALL_PIDS"
        for pid in $ALL_PIDS; do
            echo "终止进程 $pid..."
            kill $pid 2>/dev/null
            sleep 1
            if ps -p $pid > /dev/null; then
                echo "进程 $pid 未响应，强制终止..."
                kill -9 $pid 2>/dev/null
            fi
        done
    fi
fi

# 检查是否有端口占用情况
VUE_PORT=$(grep "port:" frontend/vue.config.js | head -n 1 | grep -o "[0-9]*")
if [ -z "$VUE_PORT" ]; then
    VUE_PORT=8080  # 默认Vue端口
fi

DJANGO_PORT=$(grep "PORT" .env 2>/dev/null | cut -d= -f2 || echo "8000")
if [ -z "$DJANGO_PORT" ]; then
    DJANGO_PORT=8000  # 默认Django端口
fi

# 检查端口占用
VUE_PORT_PID=$(lsof -ti:$VUE_PORT 2>/dev/null)
if [ ! -z "$VUE_PORT_PID" ]; then
    echo "发现端口 $VUE_PORT 仍被进程 $VUE_PORT_PID 占用，正在释放..."
    kill -9 $VUE_PORT_PID 2>/dev/null
fi

DJANGO_PORT_PID=$(lsof -ti:$DJANGO_PORT 2>/dev/null)
if [ ! -z "$DJANGO_PORT_PID" ]; then
    echo "发现端口 $DJANGO_PORT 仍被进程 $DJANGO_PORT_PID 占用，正在释放..."
    kill -9 $DJANGO_PORT_PID 2>/dev/null
fi

echo "====== 系统已停止 ======"