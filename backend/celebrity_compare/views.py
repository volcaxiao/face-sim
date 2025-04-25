import os
import json
import random
import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Celebrity, ComparisonResult, ComparisonDetail
from .serializers import CelebritySerializer, ComparisonResultSerializer, PhotoUploadSerializer


class CelebrityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    获取明星列表的API
    """
    queryset = Celebrity.objects.all().order_by('name')
    serializer_class = CelebritySerializer
    permission_classes = [permissions.AllowAny]


class FaceCompareAPIView(APIView):
    """
    人脸比对API，上传照片并返回最相似的三位明星
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = PhotoUploadSerializer(data=request.data)
        if serializer.is_valid():
            user_photo = serializer.validated_data['photo']
            
            # 创建比对结果记录
            comparison = ComparisonResult.objects.create(user_photo=user_photo)
            
            try:
                # 检查是否配置了Face++ API密钥
                face_api_key = settings.FACE_PLUS_PLUS.get('API_KEY')
                if not face_api_key or len(face_api_key) <= 5:
                    return Response({'error': '系统未配置Face++ API密钥，无法进行比对。请联系管理员设置密钥。'}, 
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
                
                # 检查是否有明星数据
                celebrities = Celebrity.objects.all()
                if not celebrities.exists():
                    comparison.delete()  # 删除无用的比对记录
                    return Response({'error': '数据库中没有明星数据，请先运行爬虫脚本导入明星！'}, 
                                status=status.HTTP_404_NOT_FOUND)
                    
                matched_celebrities = self.call_face_plus_plus_api(user_photo)
                
                # 如果没有匹配到任何明星
                if not matched_celebrities or len(matched_celebrities) == 0:
                    comparison.delete()  # 删除无用的比对记录
                    return Response({'error': '未能找到相似的明星，请尝试上传不同角度的照片'}, 
                                status=status.HTTP_404_NOT_FOUND)
                    
                # 存储比对结果
                for match in matched_celebrities:
                    try:
                        celebrity = Celebrity.objects.get(id=match['celebrity_id'])
                        ComparisonDetail.objects.create(
                            comparison=comparison,
                            celebrity=celebrity,
                            similarity=match['similarity']
                        )
                    except Celebrity.DoesNotExist:
                        continue
                
                # 如果没有成功存储任何比对结果，返回错误
                if not ComparisonDetail.objects.filter(comparison=comparison).exists():
                    comparison.delete()
                    return Response({'error': '比对处理失败，未能找到匹配的明星数据'}, 
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                # 返回比对结果
                result_serializer = ComparisonResultSerializer(comparison)
                return Response(result_serializer.data, status=status.HTTP_201_CREATED)
            
            except Exception as e:
                # 删除已创建的比对记录，避免留下无用数据
                comparison.delete()
                # 返回友好的错误信息
                error_message = str(e)
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                
                # 根据错误信息设置不同的状态码
                if "未能检测到人脸" in error_message:
                    status_code = status.HTTP_400_BAD_REQUEST
                elif "照片尺寸不符合要求" in error_message:
                    status_code = status.HTTP_400_BAD_REQUEST
                elif "API密钥" in error_message or "API错误" in error_message:
                    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                
                return Response({'error': error_message}, status=status_code)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def call_face_plus_plus_api(self, user_photo):
        """
        调用Face++ API进行人脸比对
        需要配置Face++ API的密钥和基础URL
        """
        # 从设置中获取Face++ API配置
        API_KEY = settings.FACE_PLUS_PLUS.get('API_KEY', '')
        API_SECRET = settings.FACE_PLUS_PLUS.get('API_SECRET', '')
        API_BASE_URL = settings.FACE_PLUS_PLUS.get('API_URL', 'https://api-cn.faceplusplus.com/facepp/v3')
        
        FACE_DETECT_URL = f"{API_BASE_URL}/detect"
        FACE_COMPARE_URL = f"{API_BASE_URL}/compare"
        
        # 获取所有已存储的明星人脸数据
        celebrities = Celebrity.objects.filter(face_token__isnull=False)
        if not celebrities.exists():
            # 如果没有face_token，尝试生成一些
            print("未找到任何face_token，尝试生成...")
            self.generate_face_tokens_for_celebrities(limit=20)
            celebrities = Celebrity.objects.filter(face_token__isnull=False)
            if not celebrities.exists():
                print("无法生成face_token，返回空结果")
                return []
        
        matches = []
        
        # 上传用户照片并获取face_token
        try:
            # 重新定位文件指针到开始位置
            user_photo.seek(0)
            
            # 读取用户照片内容
            photo_data = user_photo.read()
            
            # 检测用户照片中的人脸 - 使用multipart/form-data格式发送文件
            # 指定文件名、MIME类型和内容
            mime_type = 'image/jpeg'  # 默认MIME类型
            
            # 尝试根据文件名后缀确定MIME类型
            file_name = user_photo.name.lower() if hasattr(user_photo, 'name') else 'user_photo.jpg'
            if file_name.endswith('.png'):
                mime_type = 'image/png'
            elif file_name.endswith('.jpeg') or file_name.endswith('.jpg'):
                mime_type = 'image/jpeg'
            
            detect_files = {
                'image_file': (file_name, photo_data, mime_type)
            }
            
            detect_data = {
                'api_key': API_KEY,
                'api_secret': API_SECRET,
                'return_attributes': 'gender,age,beauty'
            }
            
            print(f"正在上传照片到Face++ API，文件名: {file_name}，MIME类型: {mime_type}")
            detect_response = requests.post(FACE_DETECT_URL, data=detect_data, files=detect_files)
            detect_result = detect_response.json()
            
            # 详细处理Face++ API的各种错误情况
            if 'error_message' in detect_result:
                print(f"Face++ API错误: {detect_result['error_message']}")
                error_msg = detect_result['error_message']
                
                # 如果是图片格式问题，尝试转换格式
                if "IMAGE_ERROR_UNSUPPORTED_FORMAT" in error_msg:
                    print("不支持的图片格式，尝试转换为JPEG格式...")
                    try:
                        from PIL import Image
                        import io
                        
                        # 重新定位文件指针
                        user_photo.seek(0)
                        
                        # 使用PIL打开并转换图片
                        img = Image.open(io.BytesIO(photo_data))
                        
                        # 转换为RGB模式（移除透明通道）
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # 保存为JPEG格式到内存缓冲区
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG')
                        buffer.seek(0)
                        
                        # 使用转换后的图片重新调用API
                        detect_files = {
                            'image_file': ('converted_image.jpg', buffer.getvalue(), 'image/jpeg')
                        }
                        
                        detect_response = requests.post(FACE_DETECT_URL, data=detect_data, files=detect_files)
                        detect_result = detect_response.json()
                        
                        # 再次检查错误
                        if 'error_message' in detect_result:
                            print(f"转换格式后仍然出错: {detect_result['error_message']}")
                            raise Exception(f"Face++ API错误: {detect_result['error_message']}")
                    except ImportError:
                        print("无法导入PIL库进行图片转换")
                        raise Exception("不支持的图片格式，请上传JPG或PNG格式的图片")
                    except Exception as e:
                        print(f"转换图片格式时出错: {str(e)}")
                        raise Exception(f"图片格式转换失败: {str(e)}")
                elif "INVALID_IMAGE_SIZE" in error_msg:
                    raise Exception("照片尺寸不符合要求，请使用分辨率更高的照片")
                elif "INVALID_IMAGE_URL" in error_msg:
                    raise Exception("照片格式不正确，请更换照片")
                elif "AUTHORIZATION" in error_msg:
                    raise Exception("Face++ API授权失败，请检查API密钥设置")
                else:
                    raise Exception(f"Face++ API错误: {error_msg}")
            
            if 'faces' not in detect_result or not detect_result['faces']:
                # 未检测到人脸，返回具体错误信息
                raise Exception("未能检测到人脸，请上传包含清晰人脸的照片")
                
            user_face_token = detect_result['faces'][0]['face_token']
            
            # 重新定位文件指针，以便再次读取
            user_photo.seek(0)
            
            # 与每个明星进行比对
            for celebrity in celebrities:
                compare_data = {
                    'api_key': API_KEY,
                    'api_secret': API_SECRET,
                    'face_token1': user_face_token,
                    'face_token2': celebrity.face_token
                }
                
                compare_response = requests.post(FACE_COMPARE_URL, data=compare_data)
                compare_result = compare_response.json()
                
                # 检查比对API的错误
                if 'error_message' in compare_result:
                    print(f"Face++比对API错误: {compare_result['error_message']}")
                    continue
                
                if 'confidence' in compare_result:
                    similarity = compare_result['confidence']
                    matches.append({
                        'celebrity_id': celebrity.id,
                        'similarity': similarity
                    })
            
            # 按相似度排序
            matches.sort(key=lambda x: x['similarity'], reverse=True)
            return matches[:3]  # 返回前三个最相似的
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {str(e)}")
            raise Exception(f"连接Face++ API服务失败，请检查网络连接: {str(e)}")
        except Exception as e:
            print(f"Face++ API调用错误: {str(e)}")
            # 将异常信息向上传递，而不是直接返回Response
            raise

    def generate_face_tokens_for_celebrities(self, limit=50):
        """
        为已有的名人数据生成Face++ token
        """
        # 获取API配置
        API_KEY = settings.FACE_PLUS_PLUS.get('API_KEY', '')
        API_SECRET = settings.FACE_PLUS_PLUS.get('API_SECRET', '')
        API_BASE_URL = settings.FACE_PLUS_PLUS.get('API_URL', 'https://api-cn.faceplusplus.com/facepp/v3')
        FACE_DETECT_URL = f"{API_BASE_URL}/detect"
        
        # 获取需要处理的明星列表（没有face_token的）
        celebrities = Celebrity.objects.filter(face_token__isnull=True)[:limit]
        processed_count = 0
        
        for celebrity in celebrities:
            try:
                # 检查photo字段是否是URL
                if celebrity.photo and (str(celebrity.photo).startswith('http://') or str(celebrity.photo).startswith('https://')):
                    # 使用URL参数调用Face++ API
                    detect_data = {
                        'api_key': API_KEY,
                        'api_secret': API_SECRET,
                        'image_url': str(celebrity.photo),
                        'return_attributes': 'gender,age,beauty'
                    }
                    
                    detect_response = requests.post(FACE_DETECT_URL, data=detect_data)
                    detect_result = detect_response.json()
                    
                    # 检查是否有错误
                    if 'error_message' in detect_result:
                        print(f"为名人 {celebrity.name} 生成Face++ token出错: {detect_result['error_message']}")
                        continue
                    
                    # 检查是否检测到人脸
                    if 'faces' in detect_result and detect_result['faces']:
                        face_token = detect_result['faces'][0]['face_token']
                        celebrity.face_token = face_token
                        celebrity.save()
                        processed_count += 1
                        print(f"成功为 {celebrity.name} 生成Face++ token")
                    else:
                        print(f"未在 {celebrity.name} 的照片中检测到人脸")
                    
                    # 添加延迟，避免API请求过于频繁
                    import time
                    time.sleep(0.5)
                else:
                    # 如果照片不是URL，跳过处理
                    continue
                    
            except Exception as e:
                print(f"处理名人 {celebrity.name} 时出错: {str(e)}")
        
        return processed_count


class ComparisonResultDetailAPIView(APIView):
    """
    获取单个比对结果的详情
    """
    def get(self, request, pk):
        try:
            # 查询指定ID的比对结果
            comparison = ComparisonResult.objects.get(pk=pk)
            
            # 检查是否有比对详情
            if not ComparisonDetail.objects.filter(comparison=comparison).exists():
                return Response({'error': '未找到该比对结果的详情数据'}, status=status.HTTP_404_NOT_FOUND)
            
            # 使用序列化器返回数据
            serializer = ComparisonResultSerializer(comparison)
            return Response(serializer.data)
        except ComparisonResult.DoesNotExist:
            return Response({'error': '未找到指定ID的比对结果'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"获取比对结果发生错误: {str(e)}")
            return Response({'error': f'获取比对结果时发生错误: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CrawlCelebritiesAPIView(APIView):
    """
    爬取明星照片的API，仅限管理员使用
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        try:
            # 导入爬虫脚本
            from scripts.celebrity_crawler import crawl_celebrities
            
            # 启动爬虫任务
            crawl_celebrities()
            
            return Response({"message": "爬取任务已完成，请查看管理后台"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
