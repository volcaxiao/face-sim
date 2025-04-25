# 明星脸相似度比对系统

这是一个基于Face++ API的明星脸相似度比对系统，用户可以上传自己的照片，系统会分析并返回最相似的三位明星及相似度。

## 功能特点

- 用户可以上传照片进行明星脸比对
- 系统返回相似度最高的三位明星及其相似度百分比
- 包含明星照片爬虫功能，支持从新浪娱乐明星库获取明星数据
- 提供管理员后台，可管理明星数据和比对结果
- 完整的前后端分离架构
- 支持Docker化部署和独立部署两种方式
- 用户会话管理，确保结果隐私安全
- 结果分享功能，可生成公开访问链接

## 技术栈

- **后端**: Django 5.2, Django REST Framework 3.15
- **前端**: Vue 3, Element Plus UI库
- **爬虫**: Beautiful Soup 4, Requests
- **人脸识别**: Face++ API，支持全面的人脸特征配置
- **部署**: Docker, Nginx, Gunicorn

## 快速开始

### 前置条件

- Python 3.8+ 和 Node.js 16+（独立部署）
- Docker 与 Docker Compose（使用Docker部署）
- Face++ API 账号和密钥（必须）
- 利用爬虫获取明星数据（必选）

### 独立部署

#### 后端部署

1. 进入后端目录并创建虚拟环境
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # 或 venv\Scripts\activate  # Windows
   ```

2. 安装Python依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 创建并配置.env文件
   ```bash
   cp ../.env.example .env
   # 编辑.env文件，填入必要配置
   ```

4. 初始化数据库
   ```bash
   python manage.py migrate
   ```

5. 创建超级用户
   ```bash
   python manage.py createsuperuser
   ```

6. 启动开发服务器
   ```bash
   python manage.py runserver
   ```

#### 前端部署

1. 进入前端目录并安装依赖
   ```bash
   cd frontend
   npm install
   ```

2. 配置API地址（开发模式下）
   - 创建`.env.development`文件:
   ```
   VUE_APP_API_URL=http://localhost:8000
   ```

3. 启动开发服务器
   ```bash
   npm run serve
   ```

4. 构建生产版本（可选）
   ```bash
   npm run build
   ```

5. 访问系统
   - 开发模式：http://localhost:8080
   - 生产模式需配合服务器部署dist目录

### 使用Docker部署

1. 克隆或解压代码仓库

2. 复制环境变量模板文件并修改
   ```bash
   cp .env.example .env
   ```

3. 编辑.env文件，设置必要的配置：
   - 设置`FACE_PLUS_PLUS_API_KEY`和`FACE_PLUS_PLUS_API_SECRET`（必填）
   - 可选：调整其他Face++ API参数，如特征返回类型、关键点检测级别等
   - 可选：调整端口、数据库等其他配置

4. 使用docker-compose构建并启动服务
   ```bash
   docker-compose up -d --build
   ```

5. 创建管理员账号（首次部署）
   ```bash
   docker-compose exec backend python manage.py createsuperuser
   ```

6. 访问系统
   - 前台应用：http://localhost (或您配置的其他端口)
   - 管理后台：http://localhost/admin


## 爬取明星数据

系统提供了命令行爬虫脚本，可以通过以下方式运行：

```bash
# Docker环境下
docker-compose exec backend python scripts/celebrity_crawler.py --page_count 5 --max_count 50

# 独立环境下
cd scripts
python celebrity_crawler.py --page_count 10 --max_count 100
```

爬虫参数说明：
- `--page_count`: 要爬取的页数，默认为5页
- `--max_count`: 最多爬取的明星数量，默认为50个

## Face++ API配置

系统使用Face++ API进行人脸检测和比对，需要在[Face++官网](https://www.faceplusplus.com/)注册账号并获取API密钥，然后在`.env`文件中配置以下参数：

```
# 必须参数
FACE_PLUS_PLUS_API_KEY=your_api_key
FACE_PLUS_PLUS_API_SECRET=your_api_secret

# 可选参数（已有默认值）
FACE_PLUS_PLUS_API_URL=https://api-cn.faceplusplus.com/facepp/v3
FACE_PLUS_PLUS_RETURN_ATTRIBUTES=gender,age,beauty,facequality,blur,eyestatus,emotion,mouthstatus,eyegaze,skinstatus,nose_occlusion,chin_occlusion,face_occlusion
FACE_PLUS_PLUS_RETURN_LANDMARK=1
```

可配置的主要参数说明：
- `API_KEY`和`API_SECRET`: Face++ API访问凭证
- `API_URL`: API基础URL，可选择国内/国际版
- `FACE_PLUS_PLUS_RETURN_ATTRIBUTES`: 希望API返回的人脸属性，多个值用逗号分隔
- `FACE_PLUS_PLUS_RETURN_LANDMARK`: 是否检测人脸关键点，2表示返回106个关键点，1表示返回83个关键点，0表示不检测

## 项目结构

```
face-sim/
├── backend/             # Django后端
│   ├── celebrity_compare/  # 主应用目录
│   │   ├── migrations/     # 数据库迁移文件
│   │   ├── serializers/    # API序列化器
│   │   ├── admin.py        # 管理后台配置
│   │   ├── facepp_utils.py # Face++ API工具类
│   │   ├── models.py       # 数据模型
│   │   ├── urls.py         # URL路由配置
│   │   └── views.py        # 视图和API端点
│   ├── facesim/          # Django项目配置
│   ├── media/            # 上传的媒体文件
│   │   ├── celebrities/  # 明星照片
│   │   └── user_photos/  # 用户上传的照片
│   └── requirements.txt  # Python依赖列表
├── frontend/            # Vue 3前端
│   ├── public/          # 静态资源
│   ├── src/             # 源代码
│   │   ├── assets/      # 资源文件
│   │   ├── components/  # 组件
│   │   ├── services/    # API服务
│   │   └── views/       # 页面视图
│   ├── Dockerfile       # 前端Docker配置
│   └── package.json     # Node.js依赖列表
├── scripts/             # 爬虫脚本
│   └── celebrity_crawler.py # 明星数据爬虫
├── data/                # 数据文件目录
│   └── sina_celebrities.json   # 新浪明星库缓存
├── docker-compose.yml   # Docker配置
├── .env.example         # 环境变量模板
├── start.sh             # 启动脚本
├── stop.sh              # 停止脚本
└── README.md            # 项目文档
```

## 系统功能说明

### 用户功能

1. **上传照片**：用户可上传自己的照片进行明星脸比对
2. **查看结果**：系统返回相似度最高的三位明星及其相似度
3. **分享结果**：可生成公开分享链接并获取二维码
4. **历史记录**：可查看当前会话的历史比对记录

### 管理员功能

1. **明星管理**：查看/添加/编辑/删除明星数据
2. **爬虫控制**：通过管理界面触发明星数据爬取
3. **比对结果管理**：查看用户比对记录
4. **系统配置**：管理系统关键参数

## 注意事项

- 本项目需要Face++ API支持，请确保配置了有效的API密钥
- Face++ API可能需要付费使用，请关注官方定价策略
- 爬虫脚本会从新浪娱乐明星库获取明星数据。
- 用户上传的照片存储在服务器端，请妥善处理用户隐私
- 系统启动/停止脚本会正确处理所有相关进程，包括前端子进程

## 常见问题解决

1. **无法检测到人脸**：确保上传的照片中有清晰可见的正面人脸
2. **明星数据不足**：通过管理后台运行爬虫获取更多明星数据
3. **Face++ API错误**：检查API密钥配置是否正确，额度是否充足
4. **服务启动失败**：检查日志文件`django.log`和`vue.log`排查问题
