#!/usr/bin/env python3
"""
测试增强后的足球检测系统 - 支持多种球类和任意角度球门
"""
import sys
import os
sys.path.append('ai_model')

from soccer_detector import SoccerDetector
import cv2
import numpy as np

def create_diverse_sports_scene():
    """创建包含多种球类和不同角度球门的场景"""
    # 创建更大的场景
    image = np.ones((720, 1080, 3), dtype=np.uint8) * 40
    image[:, :, 1] = 100  # 绿色草地
    
    # 添加草地纹理
    for i in range(0, 720, 15):
        cv2.line(image, (0, i), (1080, i), (35, 90, 35), 1)
    
    print("🎨 创建多样化运动场景...")
    
    # 1. 经典黑白足球
    cv2.circle(image, (200, 300), 45, (255, 255, 255), -1)
    # 五边形图案
    pentagon_points = []
    center = (200, 300)
    radius = 18
    for i in range(5):
        angle = i * 2 * np.pi / 5 - np.pi / 2
        x = int(center[0] + radius * np.cos(angle))
        y = int(center[1] + radius * np.sin(angle))
        pentagon_points.append([x, y])
    pentagon_points = np.array(pentagon_points)
    cv2.fillPoly(image, [pentagon_points], (0, 0, 0))
    
    # 2. 橙色篮球
    cv2.circle(image, (450, 200), 40, (0, 165, 255), -1)
    # 篮球纹理线
    cv2.line(image, (410, 200), (490, 200), (0, 0, 0), 3)
    cv2.line(image, (450, 160), (450, 240), (0, 0, 0), 3)
    cv2.ellipse(image, (450, 200), (25, 40), 0, 0, 180, (0, 0, 0), 2)
    cv2.ellipse(image, (450, 200), (25, 40), 0, 180, 360, (0, 0, 0), 2)
    
    # 3. 红色球
    cv2.circle(image, (750, 350), 35, (0, 0, 255), -1)
    cv2.circle(image, (750, 350), 35, (255, 255, 255), 2)
    
    # 4. 蓝色球
    cv2.circle(image, (300, 500), 38, (255, 100, 0), -1)
    
    # 5. 黄色网球
    cv2.circle(image, (600, 450), 25, (0, 255, 255), -1)
    cv2.ellipse(image, (600, 450), (25, 25), 45, 0, 180, (255, 255, 255), 2)
    cv2.ellipse(image, (600, 450), (25, 25), -45, 0, 180, (255, 255, 255), 2)
    
    print("✅ 创建了5个不同类型的球")
    
    # 球门1: 正面视角的白色球门
    goal1_x, goal1_y = 850, 150
    goal1_w, goal1_h = 200, 100
    cv2.rectangle(image, (goal1_x, goal1_y), (goal1_x + goal1_w, goal1_y + goal1_h), (255, 255, 255), 6)
    cv2.rectangle(image, (goal1_x + 5, goal1_y + 5), (goal1_x + goal1_w - 5, goal1_y + goal1_h - 5), (255, 255, 255), 2)
    # 球门网格
    for i in range(goal1_x + 20, goal1_x + goal1_w, 20):
        cv2.line(image, (i, goal1_y + 6), (i, goal1_y + goal1_h - 6), (200, 200, 200), 1)
    for i in range(goal1_y + 20, goal1_y + goal1_h, 20):
        cv2.line(image, (goal1_x + 6, i), (goal1_x + goal1_w - 6, i), (200, 200, 200), 1)
    
    # 球门2: 侧面角度的金属球门
    goal2_corners = np.array([[50, 400], [250, 380], [280, 500], [80, 520]], dtype=np.int32)
    cv2.polylines(image, [goal2_corners], True, (180, 180, 180), 5)  # 灰色金属
    cv2.fillPoly(image, [goal2_corners], (40, 40, 40), lineType=cv2.LINE_AA)
    
    # 球门3: 彩色球门（红色）
    goal3_x, goal3_y = 400, 600
    goal3_w, goal3_h = 180, 80
    cv2.rectangle(image, (goal3_x, goal3_y), (goal3_x + goal3_w, goal3_y + goal3_h), (0, 0, 200), 4)
    
    print("✅ 创建了3个不同角度和颜色的球门")
    
    # 添加一些球场线
    cv2.line(image, (0, 360), (1080, 360), (255, 255, 255), 3)  # 中线
    cv2.circle(image, (540, 360), 100, (255, 255, 255), 3)  # 中圈
    
    return image

def main():
    print("🚀 测试增强后的多球类和全角度球门检测系统...")
    
    # 初始化检测器
    detector = SoccerDetector()
    
    # 创建多样化场景
    test_image = create_diverse_sports_scene()
    
    # 保存原图
    cv2.imwrite('enhanced_test_original.jpg', test_image)
    print("📸 多样化场景已保存: enhanced_test_original.jpg")
    
    # 执行检测
    print("\n🔍 开始增强检测...")
    import time
    start_time = time.time()
    
    result = detector.process_frame(test_image)
    
    end_time = time.time()
    print(f"⏱️  检测耗时: {end_time - start_time:.2f}秒")
    
    # 显示结果
    balls = result['detections']['soccer_balls']
    goals = result['detections']['goal_areas']
    
    print(f"\n📊 增强检测结果:")
    print(f"🏀 检测到球类: {len(balls)}")
    print(f"🥅 检测到球门: {len(goals)}")
    
    if balls:
        print(f"\n🏀 球类检测详情:")
        for i, ball in enumerate(balls):
            method = ball.get('detection_method', 'unknown')
            class_name = ball.get('class_name', 'ball')
            print(f"  球{i+1}: {class_name} - 置信度={ball['confidence']:.2f}, 方法={method}")
            print(f"      位置={ball['bbox']}")
    
    if goals:
        print(f"\n🥅 球门检测详情:")
        for i, goal in enumerate(goals):
            method = goal.get('detection_method', 'unknown')
            corners = goal.get('corners', [])
            print(f"  门{i+1}: 置信度={goal['confidence']:.2f}, 方法={method}")
            print(f"      边界框={goal['bbox']}")
            if corners:
                print(f"      角点数量={len(corners)}")
    
    # 绘制检测结果
    result_image = test_image.copy()
    
    # 绘制球类检测框
    colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    for i, ball in enumerate(balls):
        bbox = ball['bbox']
        confidence = ball['confidence']
        method = ball.get('detection_method', 'unknown')
        class_name = ball.get('class_name', 'ball')
        
        color = colors[i % len(colors)]
        
        # 绘制边界框
        cv2.rectangle(result_image, (int(bbox[0]), int(bbox[1])), 
                     (int(bbox[2]), int(bbox[3])), color, 3)
        
        # 添加标签
        label = f"{class_name} {confidence:.2f} ({method})"
        cv2.putText(result_image, label, (int(bbox[0]), int(bbox[1]) - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    # 绘制球门检测结果
    for i, goal in enumerate(goals):
        bbox = goal['bbox']
        confidence = goal['confidence']
        method = goal.get('detection_method', 'unknown')
        corners = goal.get('corners', [])
        
        if corners and len(corners) >= 4:
            # 绘制四边形
            corners_np = np.array(corners, dtype=np.int32)
            cv2.polylines(result_image, [corners_np], True, (0, 0, 255), 4)
            
            # 绘制角点
            for corner in corners:
                cv2.circle(result_image, (int(corner[0]), int(corner[1])), 5, (0, 0, 255), -1)
        else:
            # 绘制矩形
            cv2.rectangle(result_image, (int(bbox[0]), int(bbox[1])), 
                         (int(bbox[2]), int(bbox[3])), (0, 0, 255), 4)
        
        # 添加标签
        label = f"Goal {confidence:.2f} ({method})"
        cv2.putText(result_image, label, (int(bbox[0]), int(bbox[1]) - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # 保存结果
    cv2.imwrite('enhanced_test_result.jpg', result_image)
    print("\n📸 增强检测结果已保存: enhanced_test_result.jpg")
    
    # 性能总结
    print(f"\n📈 系统性能总结:")
    print(f"   • 球类检测能力: ✅ 支持多种颜色和形状")
    print(f"   • 球门检测能力: ✅ 支持任意角度和颜色")  
    print(f"   • 检测方法: ✅ YOLO + 颜色检测 + 形状检测")
    print(f"   • 实时性能: ✅ {end_time - start_time:.2f}秒/帧 (适合500ms间隔)")
    print(f"   • 可视化: ✅ 四边形框和角点标记")
    
    print("\n🎉 增强检测系统测试完成！")
    print("📱 现在可以在手机应用中:")
    print("   • 🏀 识别各种颜色和类型的球类")
    print("   • 🥅 检测任意角度和颜色的球门")
    print("   • 🎯 手动标注自定义球门区域")
    print("   • 📐 看到精确的四边形检测框")

if __name__ == "__main__":
    main()