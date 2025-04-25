import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class FacePPAPI:
    """
    Face++ API 工具类，提供统一的接口调用方法
    """
    
    @staticmethod
    def get_api_config():
        """获取 Face++ API 配置"""
        return {
            'api_key': settings.FACE_PLUS_PLUS.get('API_KEY', ''),
            'api_secret': settings.FACE_PLUS_PLUS.get('API_SECRET', ''),
            'api_url': settings.FACE_PLUS_PLUS.get('API_URL', 'https://api-cn.faceplusplus.com/facepp/v3'),
            'return_attributes': settings.FACE_PLUS_PLUS.get('RETURN_ATTRIBUTES', 'gender,age,beauty'),
            'return_landmark': settings.FACE_PLUS_PLUS.get('RETURN_LANDMARK', '0')
        }
    
    @staticmethod
    def detect_face_by_url(image_url, return_landmark=None):
        """
        通过图片URL检测人脸并返回face_token
        
        参数:
            image_url (str): 图片URL
            return_landmark (str, 可选): 是否返回人脸关键点，可选值：0, 1, 2
        
        返回:
            dict 或 None: 检测结果或None（如果出错）
        """
        # 获取API配置
        config = FacePPAPI.get_api_config()
        api_key = config['api_key']
        api_secret = config['api_secret']
        api_base_url = config['api_url']
        
        # 验证API密钥
        if not api_key or len(api_key) <= 5:
            logger.warning("未配置有效的Face++ API密钥")
            return None
            
        # 验证URL
        if not image_url or not isinstance(image_url, str):
            logger.error(f"无效的图片URL: {image_url}")
            return None
            
        # 确保URL格式正确
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif not (image_url.startswith('http://') or image_url.startswith('https://')):
            logger.error(f"非标准URL格式: {image_url}")
            return None
        
        # 构建请求参数
        detect_url = f"{api_base_url}/detect"
        detect_data = {
            'api_key': api_key,
            'api_secret': api_secret,
            'image_url': image_url,
            'return_attributes': config['return_attributes']
        }
        
        # 添加关键点检测参数
        if return_landmark is not None:
            detect_data['return_landmark'] = return_landmark
        else:
            detect_data['return_landmark'] = config['return_landmark']
            
        try:
            # 发送请求
            logger.info(f"正在通过URL调用Face++ API检测人脸: {image_url[:50]}...")
            response = requests.post(detect_url, data=detect_data, timeout=10)
            result = response.json()
            
            # 处理错误
            if 'error_message' in result:
                logger.error(f"Face++ API错误: {result['error_message']}")
                return None
                
            # 检查是否检测到人脸
            if 'faces' in result and result['faces']:
                return result
            else:
                logger.warning(f"未在图片中检测到人脸")
                return None
                
        except Exception as e:
            logger.error(f"调用Face++ API时出错: {str(e)}")
            return None
            
    @staticmethod
    def detect_face_by_file(image_data, file_name='image.jpg', mime_type=None, return_landmark=None):
        """
        通过图片文件数据检测人脸并返回face_token
        
        参数:
            image_data (bytes): 图片数据
            file_name (str): 文件名
            mime_type (str, 可选): MIME类型，如果为None则根据文件名推断
            return_landmark (str, 可选): 是否返回人脸关键点，可选值：0, 1, 2
            
        返回:
            dict 或 None: 检测结果或None（如果出错）
        """
        # 获取API配置
        config = FacePPAPI.get_api_config()
        api_key = config['api_key']
        api_secret = config['api_secret']
        api_base_url = config['api_url']
        
        # 验证API密钥
        if not api_key or len(api_key) <= 5:
            logger.warning("未配置有效的Face++ API密钥")
            return None
            
        # 验证图片数据
        if not image_data:
            logger.error("无效的图片数据")
            return None
            
        # 确定MIME类型
        if not mime_type:
            if file_name.lower().endswith('.png'):
                mime_type = 'image/png'
            elif file_name.lower().endswith('.jpeg') or file_name.lower().endswith('.jpg'):
                mime_type = 'image/jpeg'
            else:
                mime_type = 'image/jpeg'  # 默认为JPEG
                
        # 构建请求参数
        detect_url = f"{api_base_url}/detect"
        detect_files = {
            'image_file': (file_name, image_data, mime_type)
        }
        detect_data = {
            'api_key': api_key,
            'api_secret': api_secret,
            'return_attributes': config['return_attributes']
        }
        
        # 添加关键点检测参数
        if return_landmark is not None:
            detect_data['return_landmark'] = return_landmark
        else:
            detect_data['return_landmark'] = config['return_landmark']
            
        try:
            # 发送请求
            logger.info(f"正在通过文件调用Face++ API检测人脸，文件名: {file_name}")
            response = requests.post(detect_url, data=detect_data, files=detect_files, timeout=10)
            result = response.json()
            
            # 处理错误
            if 'error_message' in result:
                logger.error(f"Face++ API错误: {result['error_message']}")
                return None
                
            # 检查是否检测到人脸
            if 'faces' in result and result['faces']:
                return result
            else:
                logger.warning(f"未在图片中检测到人脸")
                return None
                
        except Exception as e:
            logger.error(f"调用Face++ API时出错: {str(e)}")
            return None

    @staticmethod
    def get_face_token(image_url=None, image_data=None, file_name='image.jpg', mime_type=None, return_landmark=None):
        """
        获取人脸token，支持URL和文件两种方式
        
        参数:
            image_url (str, 可选): 图片URL
            image_data (bytes, 可选): 图片数据
            file_name (str): 文件名，仅当提供image_data时使用
            mime_type (str, 可选): MIME类型，如果为None则根据文件名推断
            return_landmark (str, 可选): 是否返回人脸关键点，可选值：0, 1, 2
            
        返回:
            str 或 None: face_token或None（如果出错）
        """
        result = None
        
        # 优先使用直接提供的图片数据
        if image_data:
            result = FacePPAPI.detect_face_by_file(image_data, file_name, mime_type, return_landmark)
        
        # 如果没有图片数据但有URL，先尝试URL方式
        elif image_url:
            # 确保URL格式正确
            if image_url.startswith('//'):
                image_url = 'https:' + image_url
                
            # 先尝试使用URL直接调用API
            result = FacePPAPI.detect_face_by_url(image_url, return_landmark)
            
            # 如果URL方式失败，尝试下载图片后用文件方式
            if not result:
                logger.info(f"URL方式检测失败，尝试下载图片: {image_url[:50]}...")
                try:
                    response = requests.get(image_url, timeout=10)
                    if response.status_code == 200:
                        downloaded_image_data = response.content
                        result = FacePPAPI.detect_face_by_file(
                            downloaded_image_data, 
                            'downloaded_image.jpg', 
                            None, 
                            return_landmark
                        )
                    else:
                        logger.error(f"下载图片失败，状态码: {response.status_code}")
                except Exception as e:
                    logger.error(f"下载图片时出错: {str(e)}")
        else:
            logger.error("未提供图片URL或图片数据")
            return None
            
        # 提取face_token
        if result and 'faces' in result and result['faces']:
            return result['faces'][0]['face_token']
        return None
        
    @staticmethod
    def compare_faces(face_token1, face_token2):
        """
        比较两个人脸的相似度
        
        参数:
            face_token1 (str): 第一个face_token
            face_token2 (str): 第二个face_token
            
        返回:
            float 或 None: 相似度(0-100)或None（如果出错）
        """
        # 获取API配置
        config = FacePPAPI.get_api_config()
        api_key = config['api_key']
        api_secret = config['api_secret']
        api_base_url = config['api_url']
        
        # 验证参数
        if not face_token1 or not face_token2:
            logger.error("无效的face_token")
            return None
            
        # 构建请求参数
        compare_url = f"{api_base_url}/compare"
        compare_data = {
            'api_key': api_key,
            'api_secret': api_secret,
            'face_token1': face_token1,
            'face_token2': face_token2
        }
        
        try:
            # 发送请求
            response = requests.post(compare_url, data=compare_data, timeout=10)
            result = response.json()
            
            # 处理错误
            if 'error_message' in result:
                logger.error(f"Face++ API错误: {result['error_message']}")
                return None
                
            # 返回相似度
            if 'confidence' in result:
                return result['confidence']
            else:
                logger.warning(f"未获取到相似度")
                return None
                
        except Exception as e:
            logger.error(f"调用Face++ API时出错: {str(e)}")
            return None