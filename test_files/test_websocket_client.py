#!/usr/bin/env python3
"""
测试WebSocket客户端
"""
import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

async def test_websocket():
    uri = "ws://192.168.0.103:8000/ws"
    
    try:
        print(f"🔗 连接到 {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 创建一个测试图像
            test_image = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.circle(test_image, (320, 240), 50, (0, 255, 0), -1)  # 绿色圆圈
            
            # 编码为base64
            _, buffer = cv2.imencode('.jpg', test_image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 发送数据
            message = {
                "image": f"data:image/jpeg;base64,{image_base64}"
            }
            
            print("📤 发送测试图像...")
            await websocket.send(json.dumps(message))
            
            print("⏳ 等待响应...")
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            
            result = json.loads(response)
            print("📡 收到响应:", result)
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())