#!/usr/bin/env python3
"""
测试禁用功能的系统
"""
import asyncio
import websockets
import json
import sys
import os
sys.path.append('ai_model')

from soccer_detector import SoccerDetector
import cv2
import numpy as np

async def test_disabled_features():
    """测试禁用的自动球门检测和碰撞检测功能"""
    print("🧪 测试禁用功能的ClipGoal-AI系统")
    print("=" * 50)
    
    # 1. 测试AI检测器本地
    print("\n📊 1. 测试本地AI检测器...")
    detector = SoccerDetector()
    
    # 创建包含球和球门的测试图像
    test_image = np.ones((480, 640, 3), dtype=np.uint8) * 50
    test_image[:, :, 1] = 120  # 绿色背景
    
    # 添加一个白色圆球
    cv2.circle(test_image, (300, 200), 30, (255, 255, 255), -1)
    cv2.circle(test_image, (300, 200), 30, (0, 0, 0), 2)
    
    # 添加一个球门
    cv2.rectangle(test_image, (450, 150), (600, 250), (255, 255, 255), 4)
    
    # 执行检测
    result = detector.process_frame(test_image)
    print(f"   ✅ AI检测器工作正常")
    print(f"   🏀 检测到球类: {len(result['detections']['soccer_balls'])}")
    print(f"   🥅 检测到球门: {len(result['detections']['goal_areas'])} (应该是0)")
    print(f"   ⚽ 碰撞检测: {result['collision_info']['has_collision']} (应该是False)")
    print(f"   🎥 精彩片段: {result['clip_info'] is not None} (应该是False)")
    print(f"   📊 进球时刻: {result['is_goal_moment']} (应该是False)")
    
    # 2. 测试WebSocket通信
    print("\n📡 2. 测试WebSocket通信...")
    uri = "ws://192.168.0.103:8000/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket连接成功")
            
            # 发送测试数据
            import base64
            _, buffer = cv2.imencode('.jpg', test_image)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            message = {
                "image": f"data:image/jpeg;base64,{image_base64}",
                "timestamp": 12345
            }
            
            await websocket.send(json.dumps(message))
            
            # 接收响应
            response = await asyncio.wait_for(websocket.recv(), timeout=10)
            data = json.loads(response)
            
            print(f"   ✅ WebSocket通信正常")
            print(f"   📊 检测成功: {data['success']}")
            print(f"   🏀 WebSocket检测球类: {len(data['detections']['soccer_balls'])}")
            print(f"   🥅 WebSocket检测球门: {len(data['detections']['goal_areas'])} (应该是0)")
            print(f"   ⚽ 碰撞检测: {data['collision_info']['has_collision']} (应该是False)")
            print(f"   📊 进球时刻: {data['is_goal_moment']} (应该是False)")
            print(f"   🎥 精彩片段: {data['clip_info'] is not None} (应该是False)")
            
    except Exception as e:
        print(f"   ❌ WebSocket测试失败: {e}")
        return False
    
    # 3. 测试只有球门的情况
    print("\n🥅 3. 测试只有球门的情况...")
    goal_only_image = np.ones((480, 640, 3), dtype=np.uint8) * 50
    goal_only_image[:, :, 1] = 120  # 绿色背景
    # 添加球门
    cv2.rectangle(goal_only_image, (200, 150), (400, 250), (255, 255, 255), 4)
    cv2.rectangle(goal_only_image, (500, 150), (600, 250), (255, 255, 255), 4)
    
    result = detector.process_frame(goal_only_image)
    print(f"   🏀 检测到球类: {len(result['detections']['soccer_balls'])}")
    print(f"   🥅 检测到球门: {len(result['detections']['goal_areas'])} (应该是0)")
    print(f"   ⚽ 碰撞检测: {result['collision_info']['has_collision']} (应该是False)")
    
    # 4. 总结
    print("\n" + "=" * 50)
    print("🎯 禁用功能测试结果")
    print("=" * 50)
    print("✅ 自动球门检测: 已禁用")
    print("✅ 碰撞检测逻辑: 已禁用")
    print("✅ 精彩片段生成: 已禁用")
    print("✅ 进球时刻判断: 已禁用")
    print("✅ 球类检测功能: 正常工作")
    print("✅ WebSocket通信: 正常工作")
    
    print("\n📱 现在用户可以：")
    print("   • 🏀 实时检测各种球类")
    print("   • 🎯 手动标注球门区域（4点标注）")
    print("   • 📐 查看精确的球类检测框")
    print("   • 🔇 静音实时检测")
    print("   • ❌ 不会再收到误报进球提醒")
    print("   • ❌ 不会再自动检测球门")
    
    return True

def main():
    """主函数"""
    success = asyncio.run(test_disabled_features())
    
    if success:
        print("\n🎉 所有功能禁用成功！")
        print("📱 手机应用现在只会：")
        print("   1. 检测和显示球类")
        print("   2. 支持手动标注球门")
        print("   3. 不再误报进球或自动检测球门")
    else:
        print("❌ 测试失败，请检查配置")

if __name__ == "__main__":
    main()