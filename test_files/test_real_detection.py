#!/usr/bin/env python3
"""
测试真实的足球和球门检测
"""
import sys
import os
sys.path.append('ai_model')

from soccer_detector import SoccerDetector
import cv2
import numpy as np

def create_realistic_soccer_scene():
    """创建更真实的足球场景"""
    # 创建绿色草地背景
    image = np.ones((640, 800, 3), dtype=np.uint8) * 50
    image[:, :, 1] = 120  # 绿色草地
    
    # 添加一些草地纹理
    for i in range(0, 640, 20):
        cv2.line(image, (0, i), (800, i), (40, 100, 40), 1)
    
    # 绘制一个更真实的足球
    # 白色底色
    cv2.circle(image, (200, 300), 40, (255, 255, 255), -1)
    
    # 足球的五边形图案 (黑色)
    # 中心五边形
    pentagon_points = []
    center = (200, 300)
    radius = 15
    for i in range(5):
        angle = i * 2 * np.pi / 5 - np.pi / 2
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        pentagon_points.append([x, y])
    
    pentagon_points = np.array(pentagon_points)
    cv2.fillPoly(image, [pentagon_points], (0, 0, 0))
    
    # 添加六边形图案
    for i in range(5):
        angle = i * 2 * np.pi / 5 - np.pi / 2
        x = int(center[0] + 25 * np.cos(angle))
        y = int(center[1] + 25 * np.sin(angle))
        
        # 绘制六边形
        hex_points = []
        for j in range(6):
            hex_angle = j * 2 * np.pi / 6
            hx = int(x + 10 * np.cos(hex_angle))
            hy = int(y + 10 * np.sin(hex_angle))
            hex_points.append([hx, hy])
        
        hex_points = np.array(hex_points)
        cv2.polylines(image, [hex_points], True, (0, 0, 0), 2)
    
    # 绘制球门 - 白色矩形框架
    goal_x, goal_y = 550, 200
    goal_width, goal_height = 180, 120
    
    # 球门框架 (白色)
    cv2.rectangle(image, (goal_x, goal_y), (goal_x + goal_width, goal_y + goal_height), (255, 255, 255), 8)
    cv2.rectangle(image, (goal_x + 5, goal_y + 5), (goal_x + goal_width - 5, goal_y + goal_height - 5), (255, 255, 255), 3)
    
    # 球门网格 (灰色)
    for i in range(goal_x + 20, goal_x + goal_width, 20):
        cv2.line(image, (i, goal_y + 8), (i, goal_y + goal_height - 8), (200, 200, 200), 1)
    for i in range(goal_y + 20, goal_y + goal_height, 20):
        cv2.line(image, (goal_x + 8, i), (goal_x + goal_width - 8, i), (200, 200, 200), 1)
    
    # 添加第二个足球（橙色训练球）
    cv2.circle(image, (400, 450), 35, (0, 165, 255), -1)  # 橙色
    cv2.circle(image, (400, 450), 35, (0, 0, 0), 3)  # 黑色边框
    
    # 添加一些白线（球场标记）
    cv2.line(image, (0, 320), (800, 320), (255, 255, 255), 3)  # 中线
    cv2.circle(image, (400, 320), 80, (255, 255, 255), 3, lineType=cv2.LINE_AA)  # 中圈
    
    return image

def main():
    print("🎯 创建真实足球场景并测试检测...")
    
    # 初始化检测器
    detector = SoccerDetector()
    
    # 创建真实场景
    test_image = create_realistic_soccer_scene()
    
    # 保存原图
    cv2.imwrite('realistic_test_original.jpg', test_image)
    print("📸 原始场景已保存: realistic_test_original.jpg")
    
    # 执行检测
    print("🔍 开始检测...")
    import time
    start_time = time.time()
    
    result = detector.process_frame(test_image)
    
    end_time = time.time()
    print(f"⏱️  检测耗时: {end_time - start_time:.2f}秒")
    
    # 显示结果
    soccer_balls = result['detections']['soccer_balls']
    goal_areas = result['detections']['goal_areas']
    
    print(f"\n📊 检测结果:")
    print(f"足球数量: {len(soccer_balls)}")
    print(f"球门数量: {len(goal_areas)}")
    
    if soccer_balls:
        print(f"\n⚽ 足球检测详情:")
        for i, ball in enumerate(soccer_balls):
            method = ball.get('detection_method', 'unknown')
            print(f"  球{i+1}: 置信度={ball['confidence']:.2f}, 方法={method}")
            print(f"      边界框={ball['bbox']}")
    
    if goal_areas:
        print(f"\n🥅 球门检测详情:")
        for i, goal in enumerate(goal_areas):
            method = goal.get('detection_method', 'unknown')
            print(f"  球门{i+1}: 置信度={goal['confidence']:.2f}, 方法={method}")
            print(f"        边界框={goal['bbox']}")
    
    # 绘制检测结果
    result_image = test_image.copy()
    
    # 绘制足球检测框
    for ball in soccer_balls:
        bbox = ball['bbox']
        confidence = ball['confidence']
        method = ball.get('detection_method', 'unknown')
        
        # 绘制边界框
        cv2.rectangle(result_image, (int(bbox[0]), int(bbox[1])), 
                     (int(bbox[2]), int(bbox[3])), (0, 255, 0), 3)
        
        # 添加标签
        label = f"Ball {confidence:.2f} ({method})"
        cv2.putText(result_image, label, (int(bbox[0]), int(bbox[1]) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 绘制球门检测框
    for goal in goal_areas:
        bbox = goal['bbox']
        confidence = goal['confidence']
        method = goal.get('detection_method', 'unknown')
        
        # 绘制边界框
        cv2.rectangle(result_image, (int(bbox[0]), int(bbox[1])), 
                     (int(bbox[2]), int(bbox[3])), (0, 0, 255), 3)
        
        # 添加标签
        label = f"Goal {confidence:.2f} ({method})"
        cv2.putText(result_image, label, (int(bbox[0]), int(bbox[1]) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # 保存结果
    cv2.imwrite('realistic_test_result.jpg', result_image)
    print("📸 检测结果已保存: realistic_test_result.jpg")
    
    print("✅ 真实场景测试完成！")

if __name__ == "__main__":
    main()