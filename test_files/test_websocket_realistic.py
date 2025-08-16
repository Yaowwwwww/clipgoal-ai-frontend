#!/usr/bin/env python3
"""
使用真实场景测试WebSocket实时检测
"""
import asyncio
import websockets
import json
import base64
import cv2
import numpy as np

async def test_realistic_websocket():
    uri = "ws://192.168.0.103:8000/ws"
    
    try:
        print(f"🔗 连接到 {uri}")
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 读取之前创建的真实场景图片
            test_image = cv2.imread('realistic_test_original.jpg')
            
            if test_image is None:
                print("❌ 无法读取测试图片，先运行 python test_real_detection.py")
                return
            
            print(f"📷 使用真实足球场景图片 {test_image.shape}")
            
            # 编码为base64
            _, buffer = cv2.imencode('.jpg', test_image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # 发送1帧测试实时检测
            for i in range(1):
                print(f"\n📤 发送第 {i+1} 帧...")
                
                message = {
                    "image": f"data:image/jpeg;base64,{image_base64}"
                }
                
                await websocket.send(json.dumps(message))
                
                print("⏳ 等待检测结果...")
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                
                result = json.loads(response)
                
                if result['success']:
                    balls = result['detections']['soccer_balls']
                    goals = result['detections']['goal_areas']
                    
                    print(f"✅ 检测成功 - 足球: {len(balls)}, 球门: {len(goals)}")
                    
                    if balls:
                        print("⚽ 检测到的足球:")
                        for j, ball in enumerate(balls):
                            method = ball.get('detection_method', 'unknown')
                            print(f"   球{j+1}: {ball['confidence']:.2f} ({method}) {ball['bbox']}")
                    
                    if goals:
                        print("🥅 检测到的球门:")
                        for j, goal in enumerate(goals):
                            method = goal.get('detection_method', 'unknown')
                            print(f"   门{j+1}: {goal['confidence']:.2f} ({method}) {goal['bbox']}")
                else:
                    print(f"❌ 检测失败: {result.get('message', '未知错误')}")
                
                # 等待500ms，模拟实时检测频率
                await asyncio.sleep(0.5)
            
            print(f"\n🎉 实时检测测试完成！")
            
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test_realistic_websocket())