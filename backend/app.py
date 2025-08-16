"""
ClipGoal-AI 后端服务
提供实时足球和球门检测API
"""

from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import base64
import json
import asyncio
import time
import sys
import os

# 自定义JSON编码器，处理numpy数据类型
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, '__int__'):
            return int(obj)
        elif hasattr(obj, '__float__'):
            return float(obj)
        return super().default(obj)

# 添加AI模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ai_model'))

from soccer_detector import SoccerDetector

app = FastAPI(title="ClipGoal-AI Detection API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延迟初始化检测器
detector = None

def get_detector():
    global detector
    if detector is None:
        print("正在初始化YOLO11s足球检测器...")
        detector = SoccerDetector(model_path='yolo11s.pt')
        print("✅ YOLO11s足球检测器初始化完成")
    return detector

# 存储连接的WebSocket客户端
active_connections = []
ball_history = []
frame_buffer = []  # 10秒帧缓冲区
saved_clips = []   # 保存的精彩片段


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except:
                # 连接已断开，移除它
                self.active_connections.remove(connection)


manager = ConnectionManager()


def decode_base64_image(base64_string: str) -> np.ndarray:
    """
    解码base64图像
    """
    try:
        # 移除数据URL前缀
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
        
        # 解码
        image_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return image
    except Exception as e:
        print(f"解码图像失败: {e}")
        return None


def encode_image_to_base64(image: np.ndarray) -> str:
    """
    编码图像为base64
    """
    try:
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{image_base64}"
    except Exception as e:
        print(f"编码图像失败: {e}")
        return ""


@app.get("/")
async def root():
    return {"message": "ClipGoal-AI Detection API"}


@app.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    """
    检测上传的图像
    """
    try:
        # 读取图像
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "无法解码图像"}
        
        # 执行检测
        global ball_history, frame_buffer, saved_clips
        current_detector = get_detector()
        result = current_detector.process_frame(frame, ball_history, frame_buffer)
        ball_history = result['ball_history']
        frame_buffer = result['frame_buffer']
        
        # 如果检测到碰撞，保存片段信息
        if result['clip_info']:
            saved_clips.append(result['clip_info'])
            print(f"🎥 保存精彩片段: {result['clip_info']['collision_type']}, 帧数: {result['clip_info']['frame_count']}")
            
            # 限制保存的片段数量
            if len(saved_clips) > 50:
                saved_clips.pop(0)
        
        # 绘制检测结果
        output_frame = current_detector.draw_detections(frame, result)
        output_base64 = encode_image_to_base64(output_frame)
        
        # 准备响应数据
        response_data = {
            "success": True,
            "detections": {
                "soccer_balls": result['detections']['soccer_balls'],
                "goal_areas": result['detections']['goal_areas']
            },
            "collision_info": result['collision_info'],
            "is_goal_moment": result['is_goal_moment'],
            "trajectory": result['trajectory'],
            "clip_info": result['clip_info'],
            "processed_image": output_base64,
            "timestamp": result['timestamp']
        }
        
        return response_data
        
    except Exception as e:
        return {"error": f"检测失败: {str(e)}"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    实时检测WebSocket端点 - YOLO11s逐帧处理
    """
    await manager.connect(websocket)
    global ball_history
    frame_count = 0
    
    try:
        while True:
            # 接收来自客户端的数据
            data = await websocket.receive_text()
            frame_data = json.loads(data)
            
            # 解码图像
            frame = decode_base64_image(frame_data['image'])
            
            if frame is not None:
                frame_count += 1
                start_time = time.time()
                
                print(f"📷 帧{frame_count}: 尺寸{frame.shape[1]}x{frame.shape[0]}")
                
                # 执行YOLO11s检测
                global frame_buffer, saved_clips
                current_detector = get_detector()
                result = current_detector.process_frame(frame, ball_history, frame_buffer)
                
                processing_time = (time.time() - start_time) * 1000
                ball_count = len(result['detections']['soccer_balls'])
                
                print(f"✅ 帧{frame_count}: 检测到{ball_count}个足球, 耗时{processing_time:.1f}ms")
                
                ball_history = result['ball_history']
                frame_buffer = result['frame_buffer']
                
                # 禁用精彩片段保存 - 用户不需要自动片段
                # if result['clip_info']:
                #     saved_clips.append(result['clip_info'])
                #     print(f"🎥 WebSocket保存精彩片段: {result['clip_info']['collision_type']}")
                #     
                #     if len(saved_clips) > 50:
                #         saved_clips.pop(0)
                
                # 准备响应数据 - 优化版本，减少数据量
                # 只传输必要的检测信息，移除冗余数据
                soccer_balls_optimized = []
                for ball in result['detections']['soccer_balls']:
                    soccer_balls_optimized.append({
                        'bbox': [round(x, 1) for x in ball['bbox']],  # 减少小数位数
                        'confidence': round(ball['confidence'], 2),
                        'center': [round(x, 1) for x in ball['center']],
                        'class_name': ball.get('class_name', 'ball'),
                        'detection_method': ball.get('detection_method', 'unknown')
                    })
                
                # 禁用自动球门检测 - 只允许手动标注球门
                goal_areas_optimized = []  # 不再处理自动检测的球门
                # for goal in result['detections']['goal_areas']:
                #     goal_data = {
                #         'bbox': [round(x, 1) for x in goal['bbox']],
                #         'confidence': round(goal['confidence'], 2),
                #         'center': [round(x, 1) for x in goal['center']],
                #         'detection_method': goal.get('detection_method', 'unknown')
                #     }
                #     # 只在有corners时才包含，且限制数量
                #     if goal.get('corners') and len(goal['corners']) <= 8:
                #         goal_data['corners'] = [[round(p[0], 1), round(p[1], 1)] 
                #                                for p in goal['corners'][:8]]
                #     goal_areas_optimized.append(goal_data)
                
                # 简化轨迹数据
                trajectory_optimized = None
                if result['trajectory'] and result['trajectory'].get('positions'):
                    positions = result['trajectory']['positions']
                    # 只保留最近的5个位置点
                    recent_positions = positions[-5:] if len(positions) > 5 else positions
                    trajectory_optimized = {
                        'positions': [[round(p[0], 1), round(p[1], 1)] for p in recent_positions],
                        'speed': round(result['trajectory'].get('speed', 0), 2)
                    }
                
                # 简化碰撞信息 - 禁用状态
                collision_optimized = {
                    'has_collision': False,  # 已禁用
                    'collision_type': None,
                    'distance': None
                }
                
                # 简化clip信息 - 禁用状态
                clip_optimized = None  # 不再生成精彩片段
                
                response_data = {
                    "success": True,
                    "detections": {
                        "soccer_balls": soccer_balls_optimized,
                        "goal_areas": []  # 不再返回自动检测的球门
                    },
                    "collision_info": collision_optimized,
                    "is_goal_moment": False,  # 已禁用
                    "trajectory": trajectory_optimized,
                    "clip_info": None,  # 已禁用
                    "timestamp": round(result['timestamp'], 2)
                }
                
                # 发送检测结果
                response_json = json.dumps(response_data, cls=NumpyEncoder, separators=(',', ':'))
                print(f"📤 发送WebSocket响应: {len(response_json)} 字符")
                
                # 检查数据大小，如果过大则进一步优化
                if len(response_json) > 5000:
                    print(f"⚠️ 响应数据过大 ({len(response_json)} 字符)，进行进一步优化")
                    # 进一步简化数据
                    minimal_response = {
                        "success": True,
                        "detections": {
                            "soccer_balls": soccer_balls_optimized[:3],  # 最多3个球
                            "goal_areas": []  # 不返回自动检测的球门
                        },
                        "collision_info": {"has_collision": False},
                        "is_goal_moment": False,
                        "timestamp": round(result['timestamp'], 2)
                    }
                    response_json = json.dumps(minimal_response, separators=(',', ':'))
                    print(f"📤 优化后响应大小: {len(response_json)} 字符")
                
                await websocket.send_text(response_json)
            else:
                error_response = json.dumps({
                    "success": False,
                    "error": "无法解码图像",
                    "detections": {"soccer_balls": [], "goal_areas": []},
                    "collision_info": {"has_collision": False},
                    "is_goal_moment": False,
                    "timestamp": round(time.time(), 2)
                }, separators=(',', ':'))
                await websocket.send_text(error_response)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"❌ WebSocket处理错误: {e}")
        try:
            # 发送错误信息给客户端
            error_response = json.dumps({
                "success": False,
                "error": str(e)[:100],  # 限制错误消息长度
                "detections": {"soccer_balls": [], "goal_areas": []},
                "collision_info": {"has_collision": False},
                "is_goal_moment": False,
                "timestamp": round(time.time(), 2)
            }, separators=(',', ':'))
            await websocket.send_text(error_response)
        except:
            pass  # 如果连接已断开，忽略发送错误
        
        manager.disconnect(websocket)


@app.get("/clips")
async def get_saved_clips():
    """
    获取保存的精彩片段列表
    """
    global saved_clips
    return {
        "success": True,
        "total_clips": len(saved_clips),
        "clips": saved_clips
    }

@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "detector_loaded": detector is not None,
        "active_connections": len(manager.active_connections),
        "frame_buffer_size": len(frame_buffer),
        "saved_clips_count": len(saved_clips)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)