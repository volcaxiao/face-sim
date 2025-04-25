import os
import json
import uuid
import requests
import concurrent.futures  # 添加并行处理模块
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Celebrity, ComparisonResult, ComparisonDetail
from .serializers import CelebritySerializer, ComparisonResultSerializer, PhotoUploadSerializer
from .facepp_utils import FacePPAPI
import threading


class CelebrityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    获取明星列表的API
    """
    queryset = Celebrity.objects.all().order_by('name')
    serializer_class = CelebritySerializer
    permission_classes = [permissions.AllowAny]


class FaceCompareAPIView(APIView):
    """
    人脸比对API，上传照片并返回最相似的明星
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = PhotoUploadSerializer(data=request.data)
        if serializer.is_valid():
            user_photo = serializer.validated_data['photo']
            
            # 获取会话ID（如果前端提供）
            session_id = request.data.get('session_id', str(uuid.uuid4()))
            
            # 创建比对结果记录
            comparison = ComparisonResult.objects.create(
                user_photo=user_photo,
                session_id=session_id,
                processing_status='processing',
                progress=0
            )
            
            # 在主线程中读取文件内容，避免在子线程中操作已关闭的文件
            try:
                # 重新定位文件指针
                user_photo.seek(0)
                
                # 读取文件内容
                photo_data = user_photo.read()
                
                # 确定文件类型
                file_name = user_photo.name if hasattr(user_photo, 'name') else 'user_photo.jpg'
                if file_name.endswith('.png'):
                    mime_type = 'image/png'
                elif file_name.endswith('.jpeg') or file_name.endswith('.jpg'):
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/jpeg'  # 默认MIME类型
                
                print(f"成功读取用户照片，大小: {len(photo_data)} 字节，类型: {mime_type}")
                
                # 异步处理图片比对，传递已读取的文件数据而非文件对象
                threading.Thread(
                    target=self.process_image_comparison,
                    args=(comparison, photo_data, file_name, mime_type)
                ).start()
                
            except Exception as e:
                error_message = f"读取用户照片时出错: {str(e)}"
                print(error_message)
                # 更新比对状态为失败
                comparison.processing_status = 'failed'
                comparison.progress = 0
                comparison.message = error_message
                comparison.save()
                
                return Response({
                    'id': comparison.id,
                    'status': 'failed',
                    'message': error_message
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 立即返回处理ID，前端可以轮询状态
            return Response({
                'id': comparison.id,
                'status': 'processing',
                'message': '照片上传成功，正在处理中...'
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def process_image_comparison(self, comparison, photo_data, file_name, mime_type):
        """异步处理图片比对的方法"""
        try:
            # 更新进度
            comparison.progress = 10
            comparison.save()
            
            # 检查是否配置了Face++ API密钥
            api_config = FacePPAPI.get_api_config()
            if not api_config['api_key'] or len(api_config['api_key']) <= 5:
                self.update_comparison_status(comparison, 'failed', '系统未配置Face++ API密钥，无法进行比对')
                return
            
            # 检查是否有明星数据
            celebrities = Celebrity.objects.all()
            if not celebrities.exists():
                self.update_comparison_status(comparison, 'failed', '数据库中没有明星数据，请先导入明星')
                return
            
            # 更新进度
            comparison.progress = 20
            comparison.save()
                
            # 调用Face++ API进行比对
            matched_celebrities = self.call_face_plus_plus_api(photo_data, file_name, mime_type, comparison)
            
            # 处理比对结果
            if not matched_celebrities or len(matched_celebrities) == 0:
                self.update_comparison_status(comparison, 'failed', '未能找到相似的明星，请尝试上传不同角度的照片')
                return
            
            # 存储比对结果
            self.save_comparison_details(comparison, matched_celebrities)
            
            # 检查是否存储成功
            if not ComparisonDetail.objects.filter(comparison=comparison).exists():
                self.update_comparison_status(comparison, 'failed', '比对处理失败，未能找到匹配的明星数据')
                return
            
            # 完成处理
            self.update_comparison_status(comparison, 'completed')
                
        except Exception as e:
            # 记录错误信息
            error_message = str(e)
            print(f"比对处理失败: {error_message}")
            self.update_comparison_status(comparison, 'failed', error_message)
    
    def update_comparison_status(self, comparison, status, error_message=None):
        """更新比对状态和进度"""
        comparison.processing_status = status
        if status == 'completed':
            comparison.progress = 100
        elif status == 'failed':
            comparison.progress = 0
            # 保存错误信息到数据库，方便前端显示具体错误原因
            comparison.message = error_message
            print(f"比对失败: {error_message}")
        comparison.save()
    
    def save_comparison_details(self, comparison, matched_celebrities):
        """保存比对结果详情"""
        try:
            comparison.progress = 90
            comparison.save()
            
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
                
        except Exception as e:
            print(f"保存比对详情时出错: {str(e)}")
            raise
    
    def call_face_plus_plus_api(self, photo_data, file_name, mime_type, comparison):
        """
        调用Face++ API进行人脸比对
        需要配置Face++ API的密钥和基础URL
        """
        # 获取API配置
        api_config = FacePPAPI.get_api_config()
        
        # 更新进度 - 初始阶段
        comparison.progress = 10
        comparison.save()
        
        # 获取所有已存储的明星人脸数据
        celebrities = Celebrity.objects.filter(face_token__isnull=False)
        if not celebrities.exists():
            # 如果没有face_token，尝试生成一些
            print("未找到任何face_token，尝试生成...")
            comparison.progress = 15
            comparison.save()
            
            try:
                processed_count = self.generate_face_tokens_for_celebrities(limit=20)
                if processed_count > 0:
                    print(f"成功为 {processed_count} 个明星生成face_token")
                    celebrities = Celebrity.objects.filter(face_token__isnull=False)
                else:
                    print("没有成功生成任何face_token")
            except Exception as e:
                print(f"生成明星face_token时出错: {str(e)}")
            
            if not celebrities.exists():
                print("无法生成face_token，返回空结果")
                return []
        
        comparison.progress = 20
        comparison.save()
        
        # 创建一个线程安全的结构来存储前三名
        import threading
        top_matches_lock = threading.Lock()  # 线程锁用于保护top_matches更新
        # top_matches存储前三名，初始化为空列表
        top_matches = []
        
        # 上传用户照片并获取face_token
        try:
            # 使用 FacePPAPI 工具类检测人脸
            user_face_token = None
            
            try:
                # 告知用户正在进行人脸检测
                print("正在检测用户照片中的人脸...")
                comparison.progress = 25
                comparison.save()
                
                # 直接使用图片数据检测人脸
                user_face_token = FacePPAPI.get_face_token(
                    image_data=photo_data, 
                    file_name=file_name,
                    mime_type=mime_type,
                    return_landmark=api_config['return_landmark']
                )
                
                # 检测成功后更新进度
                comparison.progress = 40
                comparison.save()
                
                if not user_face_token:
                    # 如果文件方式失败，可能需要转换图片格式
                    print("文件检测失败，尝试转换格式...")
                    try:
                        from PIL import Image
                        import io
                        
                        # 使用PIL打开并转换图片
                        img = Image.open(io.BytesIO(photo_data))
                        
                        # 转换为RGB模式（移除透明通道）
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # 保存为JPEG格式到内存缓冲区
                        buffer = io.BytesIO()
                        img.save(buffer, format='JPEG')
                        buffer.seek(0)
                        
                        # 使用转换后的图片重新尝试
                        user_face_token = FacePPAPI.get_face_token(
                            image_data=buffer.getvalue(),
                            file_name='converted_image.jpg',
                            mime_type='image/jpeg',
                            return_landmark=api_config['return_landmark']
                        )
                        
                        # 转换后检测成功的进度
                        if user_face_token:
                            comparison.progress = 40
                            comparison.save()
                    except ImportError:
                        print("无法导入PIL库进行图片转换")
                        raise Exception("不支持的图片格式，请上传JPG或PNG格式的图片")
                    except Exception as e:
                        print(f"转换图片格式时出错: {str(e)}")
                        raise Exception(f"图片格式转换失败: {str(e)}")
            except Exception as e:
                print(f"检测人脸出错: {str(e)}")
                raise Exception(f"人脸检测失败: {str(e)}")
            
            if not user_face_token:
                raise Exception("未能检测到人脸，请上传包含清晰人脸的照片")
                
            # 保存用户的face_token
            comparison.face_token = user_face_token
            comparison.save()
            
            print("人脸检测完成，准备进行人脸比对...")
            
            # 与每个明星进行比对
            total_celebrities = celebrities.count()
            processed_celebrities = 0
            
            # 比对开始，进度达到50%
            comparison.progress = 50
            comparison.save()
            
            def compare_with_celebrity(celebrity):
                # 跳过没有face_token的明星
                if not celebrity.face_token:
                    return
                    
                # 执行人脸比对
                similarity = FacePPAPI.compare_faces(user_face_token, celebrity.face_token)
                if similarity is None:
                    return
                    
                # 获取比对结果对象
                result = {
                    'celebrity_id': celebrity.id,
                    'similarity': similarity
                }
                
                # 使用线程锁来保护更新top_matches的操作
                with top_matches_lock:
                    # 根据相似度动态维护前三名
                    if len(top_matches) < 3:
                        # 如果不足三个，直接添加
                        top_matches.append(result)
                        # 添加后按相似度降序排序
                        top_matches.sort(key=lambda x: x['similarity'], reverse=True)
                    elif similarity > top_matches[-1]['similarity']:
                        # 如果已有三个且当前相似度大于第三名，替换第三名
                        top_matches[-1] = result
                        # 替换后重新排序
                        top_matches.sort(key=lambda x: x['similarity'], reverse=True)
            
            # 使用线程池并行执行比对
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(compare_with_celebrity, celebrity) for celebrity in celebrities]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        # 捕获任何可能的异常
                        future.result()
                    except Exception as e:
                        print(f"比对过程中发生错误: {str(e)}")
                    
                    # 更新进度
                    processed_celebrities += 1
                    if processed_celebrities % 5 == 0 or processed_celebrities == total_celebrities:
                        progress = 50 + int((processed_celebrities / total_celebrities) * 40)
                        comparison.progress = min(progress, 90)
                        comparison.save()
            
            # 如果没有任何匹配结果
            if not top_matches:
                print("没有找到任何匹配结果")
                return []
            
            # 直接返回已排序好的前三名
            return top_matches
            
        except requests.exceptions.RequestException as e:
            print(f"网络请求错误: {str(e)}")
            raise Exception(f"连接Face++ API服务失败，请检查网络连接: {str(e)}")
        except Exception as e:
            print(f"Face++ API调用错误: {str(e)}")
            # 将异常信息向上传递
            raise

    def generate_face_tokens_for_celebrities(self, limit=50):
        """
        为已有的名人数据生成Face++ token
        """
        # 获取需要处理的明星列表（没有face_token的）
        celebrities = Celebrity.objects.filter(face_token__isnull=True)[:limit]
        processed_count = 0
        
        for celebrity in celebrities:
            try:
                # 检查photo字段是否是URL
                if celebrity.photo and (str(celebrity.photo).startswith('http://') or str(celebrity.photo).startswith('https://')):
                    # 使用URL方式生成face_token
                    face_token = FacePPAPI.get_face_token(image_url=str(celebrity.photo))
                    
                    if face_token:
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
            
            # 检查是否为公开分享链接
            is_public_request = request.query_params.get('public') == 'true'
            
            # 安全检查：如果不是公开访问，且提供了session_id，验证是否匹配
            if not (is_public_request and comparison.is_public):
                session_id = request.query_params.get('session_id')
                if session_id and comparison.session_id and session_id != comparison.session_id:
                    return Response(
                        {'error': '无权限查看此结果'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                elif not session_id:
                    return Response(
                        {'error': '请提供session_id或通过公开链接访问'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            # 检查处理状态
            if comparison.processing_status == 'processing':
                return Response({
                    'id': comparison.id,
                    'status': 'processing',
                    'progress': comparison.progress,
                    'message': '比对处理中...'
                })
            
            elif comparison.processing_status == 'failed':
                return Response({
                    'id': comparison.id,
                    'status': 'failed',
                    'message': comparison.message or '比对处理失败'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 处理已完成，检查是否有比对详情
            if not ComparisonDetail.objects.filter(comparison=comparison).exists():
                return Response(
                    {'error': '未找到该比对结果的详情数据'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 使用序列化器返回数据
            serializer = ComparisonResultSerializer(comparison)
            return Response(serializer.data)
            
        except ComparisonResult.DoesNotExist:
            return Response(
                {'error': '未找到指定ID的比对结果'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"获取比对结果发生错误: {str(e)}")
            return Response(
                {'error': f'获取比对结果时发生错误: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ComparisonStatusAPIView(APIView):
    """
    查询比对结果处理状态的API
    """
    def get(self, request, pk):
        try:
            comparison = ComparisonResult.objects.get(pk=pk)
            
            # 安全检查：如果提供了session_id，验证是否匹配
            session_id = request.query_params.get('session_id')
            if session_id and comparison.session_id and session_id != comparison.session_id:
                return Response(
                    {'error': '无权限查看此结果'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            response_data = {
                'id': comparison.id,
                'status': comparison.processing_status,
                'progress': comparison.progress,
                'created_at': comparison.created_at
            }
            
            # 如果处理失败，添加错误信息
            if comparison.processing_status == 'failed' and comparison.message:
                response_data['message'] = comparison.message
                response_data['error'] = comparison.message
            
            return Response(response_data)
            
        except ComparisonResult.DoesNotExist:
            return Response(
                {'error': '未找到指定ID的比对结果'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ComparisonHistoryAPIView(APIView):
    """
    获取用户历史比对记录的API
    """
    def get(self, request):
        try:
            # 获取session_id参数
            session_id = request.query_params.get('session_id')
            if not session_id:
                return Response(
                    {'error': '缺少必要参数: session_id'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 查询指定会话的历史记录
            comparisons = ComparisonResult.objects.filter(session_id=session_id).order_by('-created_at')
            
            # 如果没有记录，返回空列表而不是404
            if not comparisons.exists():
                return Response([])
            
            # 构建响应数据
            results = []
            for comparison in comparisons:
                result_data = {
                    'id': comparison.id,
                    'created_at': comparison.created_at,
                    'processing_status': comparison.processing_status
                }
                
                # 添加用户照片URL（如果有）
                if comparison.user_photo:
                    result_data['user_photo_url'] = request.build_absolute_uri(comparison.user_photo.url)
                else:
                    result_data['user_photo_url'] = None
                
                # 如果处理完成，添加匹配结果最高的明星信息
                if comparison.processing_status == 'completed':
                    try:
                        top_match = ComparisonDetail.objects.filter(comparison=comparison).order_by('-similarity').first()
                        if top_match:
                            result_data['top_match'] = {
                                'celebrity_name': top_match.celebrity.name,
                                'similarity': top_match.similarity
                            }
                    except Exception as e:
                        print(f"获取匹配信息出错: {str(e)}")
                
                results.append(result_data)
            
            return Response(results)
            
        except Exception as e:
            print(f"获取历史记录时出错: {str(e)}")
            return Response(
                {'error': f'获取历史记录失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ShareComparisonAPIView(APIView):
    """
    设置比对结果为公开分享状态的API
    """
    def post(self, request, pk):
        try:
            comparison = ComparisonResult.objects.get(pk=pk)
            
            # 安全检查：如果提供了session_id，验证是否匹配
            session_id = request.query_params.get('session_id') or request.data.get('session_id')
            if session_id and comparison.session_id and session_id != comparison.session_id:
                return Response(
                    {'error': '无权限分享此结果'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 检查处理状态，只有处理完成的结果才能分享
            if comparison.processing_status != 'completed':
                return Response({
                    'error': '只能分享处理完成的结果',
                    'status': comparison.processing_status
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 设置为公开分享状态
            comparison.is_public = True
            
            # 如果没有分享码，生成一个分享码
            if not comparison.share_code:
                import random
                import string
                # 生成8位随机字母数字组合
                share_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                comparison.share_code = share_code
                
            comparison.save()
            
            # 构建分享URL
            host = request.get_host()
            # 强制使用前端端口8080，不使用后端API端口8000
            if ':' in host:
                host = host.split(':')[0] + ':8080'
            else:
                host = host + ':8080'
                
            protocol = 'https' if request.is_secure() else 'http'
            share_url = f"{protocol}://{host}/result/{comparison.id}?public=true"
            short_url = f"{protocol}://{host}/s/{comparison.share_code}"
            
            return Response({
                'id': comparison.id,
                'share_url': share_url,
                'short_url': short_url,
                'share_code': comparison.share_code,
                'message': '已成功设置为公开分享状态'
            })
            
        except ComparisonResult.DoesNotExist:
            return Response(
                {'error': '未找到指定ID的比对结果'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'分享设置失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
