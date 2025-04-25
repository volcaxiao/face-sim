#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import random
import requests
from bs4 import BeautifulSoup
import django
import logging
import json
from urllib.parse import urljoin, quote
from concurrent.futures import ThreadPoolExecutor
import re

# 设置Django环境
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "facesim.settings")
django.setup()

# 导入Django模型
from celebrity_compare.models import Celebrity
from django.conf import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 爬虫配置
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
]

def get_headers():
    """获取随机UA头"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://star.endata.com.cn/Star/Search',
    }

def generate_face_token(photo_url):
    """为明星照片生成Face++ token"""
    try:
        # 从设置中获取Face++ API配置
        API_KEY = settings.FACE_PLUS_PLUS.get('API_KEY', '')
        API_SECRET = settings.FACE_PLUS_PLUS.get('API_SECRET', '')
        
        if not API_KEY or len(API_KEY) <= 5:
            logger.warning("未配置有效的Face++ API密钥，无法生成Face++ token")
            return None
        
        # 检查URL是否有效
        if not photo_url or not isinstance(photo_url, str):
            logger.error(f"无效的照片URL: {photo_url}")
            return None
            
        # 确保URL格式正确
        if photo_url.startswith('//'):
            photo_url = 'https:' + photo_url
        elif not (photo_url.startswith('http://') or photo_url.startswith('https://')):
            logger.error(f"非标准URL格式: {photo_url}")
            return None
            
        # 尝试检查URL是否可访问
        try:
            head_response = requests.head(photo_url, timeout=5)
            if head_response.status_code != 200:
                logger.error(f"照片URL不可访问，状态码: {head_response.status_code}, URL: {photo_url}")
                return None
        except Exception as e:
            logger.error(f"检查照片URL可访问性时出错: {str(e)}, URL: {photo_url}")
            return None
            
        API_BASE_URL = settings.FACE_PLUS_PLUS.get('API_URL', 'https://api-cn.faceplusplus.com/facepp/v3')
        FACE_DETECT_URL = f"{API_BASE_URL}/detect"
        
        # 使用URL参数调用Face++ API
        detect_data = {
            'api_key': API_KEY,
            'api_secret': API_SECRET,
            'image_url': photo_url,
            'return_attributes': 'gender,age,beauty'
        }
        
        logger.info(f"正在调用Face++ API检测照片: {photo_url[:50]}...")
        detect_response = requests.post(FACE_DETECT_URL, data=detect_data, timeout=10)
        detect_result = detect_response.json()
        
        # 检查是否有错误
        if 'error_message' in detect_result:
            error_msg = detect_result['error_message']
            logger.error(f"生成Face++ token出错: {error_msg}")
            
            # 如果是URL无效错误，尝试下载图片然后用文件上传
            if 'INVALID_IMAGE_URL' in error_msg:
                logger.info(f"URL无效，尝试下载图片然后通过文件上传...")
                try:
                    # 下载图片
                    img_response = requests.get(photo_url, timeout=10)
                    if img_response.status_code == 200:
                        # 使用文件方式上传
                        detect_files = {
                            'image_file': ('temp.jpg', img_response.content, 'image/jpeg')
                        }
                        detect_data = {
                            'api_key': API_KEY,
                            'api_secret': API_SECRET,
                            'return_attributes': 'gender,age,beauty'
                        }
                        detect_response = requests.post(FACE_DETECT_URL, data=detect_data, files=detect_files, timeout=10)
                        detect_result = detect_response.json()
                        
                        # 再次检查是否有错误
                        if 'error_message' in detect_result:
                            logger.error(f"通过文件上传仍然出错: {detect_result['error_message']}")
                            return None
                    else:
                        logger.error(f"下载图片失败，状态码: {img_response.status_code}")
                        return None
                except Exception as e:
                    logger.error(f"下载和上传图片出错: {str(e)}")
                    return None
            else:
                return None
        
        # 检查是否检测到人脸
        if 'faces' in detect_result and detect_result['faces']:
            face_token = detect_result['faces'][0]['face_token']
            logger.info(f"成功生成Face++ token: {face_token[:10]}...")
            return face_token
        else:
            logger.warning(f"未在照片中检测到人脸: {photo_url}")
            return None
            
    except Exception as e:
        logger.error(f"生成Face++ token时出错: {str(e)}")
        return None

def save_celebrity_to_db(celebrity_data, source_name):
    """保存明星信息到数据库和JSON文件"""
    try:
        # 检查是否已存在同名明星
        existing = Celebrity.objects.filter(name=celebrity_data['name']).first()
        if not existing:
            # 提取性别、国籍、出生日期等信息
            gender = None
            nationality = None
            birth_date = None
            
            if source_name == "sina" and 'raw_data' in celebrity_data:
                gender = celebrity_data['raw_data'].get('性别')
                nationality = celebrity_data['raw_data'].get('国籍')
                birth_date = celebrity_data['raw_data'].get('出生日期')
                
            elif source_name == "endata" and 'raw_data' in celebrity_data:
                gender = celebrity_data['raw_data'].get('StarSex')
                nationality = celebrity_data['raw_data'].get('Country')
                # 处理时间戳格式的出生日期
                birth_date_ts = celebrity_data['raw_data'].get('BirthdayDate')
                if birth_date_ts:
                    try:
                        # 将时间戳转换为日期字符串
                        from datetime import datetime
                        birth_date = datetime.fromtimestamp(birth_date_ts/1000).strftime('%Y-%m-%d')
                    except:
                        birth_date = None

            # 为照片生成Face++ token
            face_token = generate_face_token(celebrity_data['photo_url'])
            
            # 创建新的明星记录
            Celebrity.objects.create(
                name=celebrity_data['name'],
                photo=celebrity_data['photo_url'],
                face_token=face_token,
                description=celebrity_data.get('description', ''),
                gender=gender,
                nationality=nationality,
                birth_date=birth_date,
                detail_url=celebrity_data.get('detail_url'),
                source=source_name  # 添加数据源信息
            )
            logger.info(f"成功保存明星到数据库: {celebrity_data['name']}")
            
            # 同时保存到JSON文件
            save_celebrity_to_json(celebrity_data, source_name)
            return True
        else:
            # 如果已存在且没有Face++ token，尝试生成并更新
            if not existing.face_token:
                face_token = generate_face_token(celebrity_data['photo_url'])
                if face_token:
                    existing.face_token = face_token
                    # 同时更新其他可能缺失的字段
                    if not existing.gender and 'raw_data' in celebrity_data:
                        if source_name == "sina":
                            existing.gender = celebrity_data['raw_data'].get('性别')
                        elif source_name == "endata":
                            existing.gender = celebrity_data['raw_data'].get('StarSex')
                    if not existing.nationality and 'raw_data' in celebrity_data:
                        if source_name == "sina":
                            existing.nationality = celebrity_data['raw_data'].get('国籍')
                        elif source_name == "endata":
                            existing.nationality = celebrity_data['raw_data'].get('Country')
                    if not existing.birth_date and 'raw_data' in celebrity_data:
                        if source_name == "sina":
                            existing.birth_date = celebrity_data['raw_data'].get('出生日期')
                        elif source_name == "endata":
                            birth_date_ts = celebrity_data['raw_data'].get('BirthdayDate')
                            if birth_date_ts:
                                try:
                                    from datetime import datetime
                                    existing.birth_date = datetime.fromtimestamp(birth_date_ts/1000).strftime('%Y-%m-%d')
                                except:
                                    pass
                    if not existing.detail_url and 'detail_url' in celebrity_data:
                        existing.detail_url = celebrity_data['detail_url']
                    if not existing.source:
                        existing.source = source_name  # 更新数据源信息
                    existing.save()
                    logger.info(f"已为已存在的明星 {celebrity_data['name']} 生成Face++ token")
            else:
                logger.info(f"明星已存在: {celebrity_data['name']}")
            return False
    except Exception as e:
        logger.error(f"保存明星异常: {celebrity_data['name']}, 错误: {str(e)}")
        return False

def save_celebrity_to_json(celebrity_data, source_name):
    """保存明星信息到JSON文件，按数据源分类"""
    try:
        # 确保data目录存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # 根据数据源选择文件名
        file_name = f"{source_name}_celebrities.json"
        file_path = os.path.join(data_dir, file_name)
        
        # 读取现有数据，处理文件不存在或格式错误的情况
        existing_data = []
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"JSON文件 {file_path} 格式错误，将重新创建")
                # 如果JSON格式错误，备份旧文件
                if os.path.exists(file_path):
                    backup_path = file_path + ".bak"
                    os.rename(file_path, backup_path)
                    logger.info(f"已将错误的JSON文件备份为 {backup_path}")
        
        # 检查是否已存在相同名字的明星
        exists = any(item.get('name') == celebrity_data['name'] for item in existing_data)
        if not exists:
            # 添加新数据
            existing_data.append(celebrity_data)
            # 保存更新后的数据，确保使用正确的编码
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            logger.info(f"成功保存明星数据到 {file_name}")
        return True
    except Exception as e:
        logger.error(f"保存明星JSON数据异常: {celebrity_data['name']}, 错误: {str(e)}")
        # 记录更详细的错误信息以便调试
        import traceback
        logger.error(traceback.format_exc())
        return False

def crawl_endata_stars(page_count=5, max_count=50):
    """爬取艺恩网站的明星数据"""
    base_url = "https://star.endata.com.cn/Star/Search"
    api_url = "https://star.endata.com.cn/api/star/search"
    
    headers = get_headers()
    
    count = 0
    for page in range(1, page_count + 1):
        logger.info(f"正在抓取艺恩网站第 {page} 页")
        try:
            # 访问API获取明星数据
            params = {
                'r': str(random.random()),  # 随机参数防止缓存
                'pageindex': page,
                'pagesize': 10,
                'order': '',
                'ordertype': '',
                'searchkey': '',
                'from': 'pub'
            }
            
            response = requests.get(api_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 1 and 'data' in result and 'table0' in result['data']:
                    stars = result['data']['table0']
                    
                    for star in stars:
                        try:
                            name = star.get('StarBaseName', '')
                            photo_url = star.get('HeadImg', '')
                            star_id = star.get('StarBaseID', '')
                            
                            # 生成详情页URL
                            detail_url = f"https://star.endata.com.cn/Star/Detail?id={star_id}" if star_id else None
                            
                            # 生成明星简介
                            description_parts = []
                            
                            # 添加基本信息
                            if star.get('BirthYear'):
                                description_parts.append(f"年代: {star.get('BirthYear')}")
                            if star.get('StarAge'):
                                description_parts.append(f"年龄: {star.get('StarAge')}岁")
                            if star.get('StarSex'):
                                description_parts.append(f"性别: {star.get('StarSex')}")
                            if star.get('Country'):
                                description_parts.append(f"国家/地区: {star.get('Country')}")
                            if star.get('Professions'):
                                description_parts.append(f"职业: {star.get('Professions')}")
                            if star.get('StarCustomTags'):
                                description_parts.append(f"标签: {star.get('StarCustomTags')}")
                            
                            # 添加排名和热度指数
                            if star.get('Irank'):
                                description_parts.append(f"艺恩指数排名: {star.get('Irank')}")
                            if star.get('FlowValueIndex_L1'):
                                description_parts.append(f"流量价值指数: {star.get('FlowValueIndex_L1')}")
                            if star.get('MajorHotIndex_L2'):
                                description_parts.append(f"热度指数: {star.get('MajorHotIndex_L2')}")
                            
                            description = "\n".join(description_parts)
                            
                            if name and photo_url:
                                celebrity_data = {
                                    "name": name,
                                    "photo_url": photo_url,
                                    "description": description,
                                    "source": "endata",
                                    "raw_data": star,
                                    "detail_url": detail_url
                                }
                                
                                if save_celebrity_to_db(celebrity_data, "endata"):
                                    count += 1
                                    print(f"艺恩网: 已保存 {name} (总数: {count})")
                                    
                                    if count >= max_count:
                                        logger.info(f"已达到最大抓取数量 {max_count}，停止抓取")
                                        return count
                            
                            # 随机延迟，避免被封
                            time.sleep(random.uniform(0.5, 1.5))
                            
                        except Exception as e:
                            logger.error(f"处理明星数据时出错: {str(e)}")
                else:
                    logger.error(f"艺恩网API返回格式异常: {result}")
            else:
                logger.error(f"艺恩网API请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            logger.error(f"抓取艺恩网第 {page} 页时出错: {str(e)}")
        
        # 页面间延迟
        time.sleep(random.uniform(2, 4))
    
    logger.info(f"艺恩网爬取完成，成功保存 {count} 个明星信息")
    return count

def crawl_sina_stars(page_count=5, max_count=50):
    """爬取新浪娱乐的明星数据"""
    base_url = "https://ent.sina.com.cn/ku/star_search_index.d.html"
    
    headers = get_headers()
    headers['Referer'] = base_url
    
    count = 0
    current_count = Celebrity.objects.filter(source="sina").count()
    remaining_count = max(0, max_count - current_count)
    
    for page in range(1, page_count + 1):
        if count >= remaining_count:
            logger.info(f"已达到目标抓取数量，停止抓取")
            break
            
        logger.info(f"正在抓取新浪娱乐第 {page} 页")
        try:
            # 构建带页码的URL
            page_url = f"{base_url}?page={page}"
            
            response = requests.get(page_url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 查找明星列表
                star_list = soup.select('div#dataList ul.tv-list.star_list.clearfix li')
                
                if not star_list:
                    logger.error(f"在第 {page} 页未找到明星列表")
                    continue
                
                for star_item in star_list:
                    try:
                        # 获取明星姓名
                        name_tag = star_item.select_one('h4.left a')
                        if not name_tag:
                            continue
                        name = name_tag.get_text().strip()
                        
                        # 获取明星详情页链接
                        detail_url = name_tag.get('href')
                        
                        # 获取明星照片
                        img_tag = star_item.select_one('a.item-img.left img')
                        photo_url = img_tag.get('src') if img_tag else ''
                        if photo_url and photo_url.startswith('//'):
                            photo_url = 'https:' + photo_url
                        
                        # 提取基本信息
                        intro_div = star_item.select_one('div.item-intro')
                        if not intro_div:
                            continue
                            
                        info = {}
                        intro_paragraphs = intro_div.select('p')
                        for p in intro_paragraphs:
                            label = p.select_one('span.txt')
                            if label:
                                key = label.get_text().strip().rstrip(':')
                                # 获取标签后面的文本
                                value = p.get_text().replace(label.get_text(), '').strip()
                                info[key] = value
                        
                        # 构建描述
                        description_parts = []
                        if '性别' in info:
                            description_parts.append(f"性别: {info['性别']}")
                        if '职业' in info:
                            description_parts.append(f"职业: {info['职业']}")
                        if '国籍' in info:
                            description_parts.append(f"国籍: {info['国籍']}")
                        if '出生日期' in info:
                            description_parts.append(f"出生日期: {info['出生日期']}")
                        if '星座' in info:
                            description_parts.append(f"星座: {info['星座']}")
                        if '身高' in info:
                            description_parts.append(f"身高: {info['身高']}")
                            
                        description = "\n".join(description_parts)
                        
                        # 获取更多详细信息（可选）
                        if detail_url:
                            try:
                                detail_resp = requests.get(detail_url, headers=headers, timeout=10)
                                detail_resp.encoding = 'utf-8'
                                
                                if detail_resp.status_code == 200:
                                    detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
                                    # 寻找详细简介
                                    intro_text = detail_soup.select_one('div.star-info-txt')
                                    if intro_text:
                                        more_info = intro_text.get_text().strip()
                                        if more_info:
                                            description += "\n\n" + more_info
                            except Exception as e:
                                logger.error(f"获取明星详情页出错: {detail_url}, 错误: {str(e)}")
                        
                        if name and photo_url:
                            celebrity_data = {
                                "name": name,
                                "photo_url": photo_url,
                                "description": description,
                                "source": "sina",
                                "raw_data": info,
                                "detail_url": detail_url
                            }
                            
                            if save_celebrity_to_db(celebrity_data, "sina"):
                                count += 1
                                print(f"新浪娱乐: 已保存 {name} (总数: {count})")
                                
                                if count >= remaining_count:
                                    logger.info(f"已达到最大抓取数量，停止抓取")
                                    return count
                        
                        # 随机延迟，避免被封
                        time.sleep(random.uniform(0.5, 1.5))
                        
                    except Exception as e:
                        logger.error(f"处理明星数据时出错: {str(e)}")
                
                # 如果本页没有找到明星数据，可能已到末页
                if len(star_list) == 0:
                    logger.info("没有找到更多明星数据，停止爬取")
                    break
                    
            else:
                logger.error(f"请求新浪娱乐页面失败，状态码: {response.status_code}")
        
        except Exception as e:
            logger.error(f"抓取新浪娱乐第 {page} 页时出错: {str(e)}")
        
        # 页面间延迟
        time.sleep(random.uniform(2, 4))
    
    logger.info(f"新浪娱乐爬取完成，成功保存 {count} 个明星信息")
    return count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="明星数据爬虫")
    parser.add_argument('--source', type=str, choices=['endata', 'sina', 'all'], default='all',
                      help='数据源: endata-艺恩, sina-新浪娱乐, all-所有')
    parser.add_argument('--page_count', type=int, default=5, help='每个数据源爬取的页数')
    parser.add_argument('--max_count', type=int, default=50, help='最多爬取总明星数')
    args = parser.parse_args()
    
    total_count = 0
    if args.source in ['endata', 'all']:
        endata_count = crawl_endata_stars(args.page_count, args.max_count)
        total_count += endata_count
        
    if args.source in ['sina', 'all'] and total_count < args.max_count:
        remaining = args.max_count - total_count
        sina_count = crawl_sina_stars(args.page_count, remaining)
        total_count += sina_count
    
    print(f"爬取完成，共爬取了 {total_count} 个明星数据")