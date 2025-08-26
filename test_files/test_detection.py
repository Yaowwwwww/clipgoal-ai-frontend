#!/usr/bin/env python3
"""
测试足球检测功能
"""

import cv2
import numpy as np
import sys
import os

# 添加模型路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_model'))

from soccer_detector import SoccerDetector
import time

def create_test_image_with_soccer_and_goal():
    """
    创建一个包含足球和球门的测试图像
    """
    # 创建绿色足球场背景
    img = np.ones((480, 640, 3), dtype=np.uint8) * 50
    img[:, :, 1] = 120  # 绿色背景
    
    # 绘制足球（白色圆形+黑色五边形图案）
    ball_center = (200, 300)
    ball_radius = 25
    
    # 白色足球
    cv2.circle(img, ball_center, ball_radius, (255, 255, 255), -1)
    
    # 黑色五边形图案
    pentagon_points = []
    for i in range(5):
        angle = i * 72 * np.pi / 180
        x = int(ball_center[0] + 15 * np.cos(angle))
        y = int(ball_center[1] + 15 * np.sin(angle))
        pentagon_points.append([x, y])
    
    cv2.fillPoly(img, [np.array(pentagon_points)], (0, 0, 0))
    
    # 绘制球门（白色矩形框架）
    goal_left = 450
    goal_right = 600
    goal_top = 180
    goal_bottom = 320
    
    # 球门柱（垂直线）
    cv2.line(img, (goal_left, goal_top), (goal_left, goal_bottom), (255, 255, 255), 8)
    cv2.line(img, (goal_right, goal_top), (goal_right, goal_bottom), (255, 255, 255), 8)
    
    # 横梁（水平线）
    cv2.line(img, (goal_left, goal_top), (goal_right, goal_top), (255, 255, 255), 8)
    
    # 球门网格（可选）
    for i in range(goal_left + 20, goal_right, 20):
        cv2.line(img, (i, goal_top), (i, goal_bottom), (200, 200, 200), 1)
    for j in range(goal_top + 20, goal_bottom, 20):
        cv2.line(img, (goal_left, j), (goal_right, j), (200, 200, 200), 1)
    
    # 添加场地线条
    cv2.line(img, (0, 240), (640, 240), (255, 255, 255), 3)  # 中线
    cv2.circle(img, (320, 240), 60, (255, 255, 255), 3)     # 中圆
    
    return img

def test_soccer_detection():
    """
    测试足球检测功能
    """
    print("🎯 开始测试足球检测功能...")
    
    # 初始化检测器
    try:
        detector = SoccerDetector()
        print("✅ 检测器初始化成功")
    except Exception as e:
        print(f"❌ 检测器初始化失败: {e}")
        return
    
    # 创建测试图像
    test_image = create_test_image_with_soccer_and_goal()
    print("✅ 测试图像创建完成")
    
    # 保存原始测试图像
    cv2.imwrite("test_original.jpg", test_image)
    print("📸 原始图像已保存: test_original.jpg")
    
    # 执行检测
    print("🔍 开始检测...")
    start_time = time.time()
    
    result = detector.process_frame(test_image)
    
    detection_time = time.time() - start_time
    print(f"⏱️  检测耗时: {detection_time:.2f}秒")
    
    # 输出检测结果
    print("\n📊 检测结果:")
    print(f"足球数量: {len(result['detections']['soccer_balls'])}")
    print(f"球门数量: {len(result['detections']['goal_areas'])}")
    print(f"是否检测到碰撞: {result['is_goal_moment']}")
    
    # 详细信息
    if result['detections']['soccer_balls']:
        print("\n⚽ 足球检测详情:")
        for i, ball in enumerate(result['detections']['soccer_balls']):
            print(f"  球{i+1}: 置信度={ball['confidence']:.2f}, 方法={ball.get('detection_method', 'unknown')}")
            print(f"      边界框=[{ball['bbox'][0]:.0f}, {ball['bbox'][1]:.0f}, {ball['bbox'][2]:.0f}, {ball['bbox'][3]:.0f}]")
    
    if result['detections']['goal_areas']:
        print("\n🥅 球门检测详情:")
        for i, goal in enumerate(result['detections']['goal_areas']):
            print(f"  球门{i+1}: 置信度={goal['confidence']:.2f}, 方法={goal.get('detection_method', 'unknown')}")
            print(f"        边界框=[{goal['bbox'][0]:.0f}, {goal['bbox'][1]:.0f}, {goal['bbox'][2]:.0f}, {goal['bbox'][3]:.0f}]")
    
    # 绘制检测结果
    print("\n🎨 绘制检测结果...")
    result_image = detector.draw_detections(test_image, result)
    
    # 保存结果图像
    cv2.imwrite("test_result.jpg", result_image)
    print("📸 结果图像已保存: test_result.jpg")
    
    # 显示图像（如果有图形界面）
    try:
        cv2.imshow("Original", test_image)
        cv2.imshow("Detection Result", result_image)
        cv2.waitKey(5000)  # 显示5秒
        cv2.destroyAllWindows()
        print("🖼️  图像显示完成")
    except:
        print("ℹ️  无法显示图像（可能是无图形环境）")
    
    print("✅ 测试完成！")

if __name__ == "__main__":
    test_soccer_detection()