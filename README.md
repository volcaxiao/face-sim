# 明星脸相似度比对系统

这是一个基于Face++ API的明星脸相似度比对系统，用户可以上传自己的照片，系统会分析并返回最相似的三位明星及相似度。

## 功能特点

- 用户可以上传照片进行明星脸比对
- 系统返回相似度最高的三位明星及其相似度百分比
- 包含明星照片爬虫功能
- 完整的前后端分离架构
- 支持Docker化部署和独立部署两种方式

## 技术栈

- **后端**: Django, Django REST Framework
- **前端**: Vue 3, Element Plus
- **爬虫**: Beautiful Soup, Requests
- **人脸识别**: Face++ API
- **部署**: Docker, Nginx, Gunicorn

## 快速开始

### 使用Docker部署

1. 克隆代码仓库
   ```bash
   git clone <仓库地址>
   cd face-sim
   ```

2. 复制环境变量模板文件
   ```bash
   cp .env.example .env
   ```

3. 编辑.env文件，设置Face++ API密钥和其他配置项

4. 使用docker-compose部署
   ```bash
   docker-compose up -d
   ```

5. 访问系统
   浏览器打开 http://localhost 即可访问系统

### 独立部署

#### 后端部署

1. 安装Python依赖
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. 初始化数据库
   ```bash
   python manage.py migrate
   ```

3. 创建超级用户(可选)
   ```bash
   python manage.py createsuperuser
   ```

4. 启动开发服务器
   ```bash
   python manage.py runserver
   ```

#### 前端部署

1. 安装Node.js依赖
   ```bash
   cd frontend
   npm install
   ```

2. 启动开发服务器
   ```bash
   npm run serve
   ```

3. 访问开发版本
   浏览器打开 http://localhost:8080 即可访问系统

## 爬取明星数据

系统提供了爬取明星数据的脚本，可以通过以下方式运行：

```bash
cd scripts
python celebrity_crawler.py
```

## Face++ API配置

本项目使用Face++ API进行人脸比对，需要在[Face++官网](https://www.faceplusplus.com/)注册账号并获取API密钥，然后在`.env`文件中配置：

```
FACE_PLUS_PLUS_API_KEY=your_api_key
FACE_PLUS_PLUS_API_SECRET=your_api_secret
```

## 项目结构

```
face-sim/
├── backend/             # Django后端
│   ├── celebrity_compare/  # 应用目录
│   ├── facesim/          # 项目配置
│   └── requirements.txt  # 依赖列表
├── frontend/            # Vue前端
│   ├── src/             # 源代码
│   └── package.json     # 依赖列表
├── scripts/             # 爬虫脚本
└── docker-compose.yml   # Docker配置
```

## 注意事项

- 本项目仅供学习参考，请遵守相关法律法规
- Face++ API可能需要付费使用，请关注官方定价
- 爬虫脚本应遵守网站的robots.txt规则，避免频繁请求

## 许可证

MIT 许可证