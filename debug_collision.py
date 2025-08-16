#!/usr/bin/env python3
"""
调试碰撞检测问题
"""
import sys
import os
sys.path.append('ai_model')

from soccer_detector import SoccerDetector
import cv2
import numpy as np

def debug_collision_detection():
    """调试碰撞检测"""
    print("🔍 调试碰撞检测问题")
    print("=" * 50)
    
    detector = SoccerDetector()
    
    # 创建测试图像：球在球门内
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
    frame[:, :, 1] = 120  # 绿色背景
    
    # 添加一个球门
    cv2.rectangle(frame, (200, 150), (400, 250), (255, 255, 255), 4)
    # 在球门内添加一个白色球
    cv2.circle(frame, (300, 200), 25, (255, 255, 255), -1)
    cv2.circle(frame, (300, 200), 25, (0, 0, 0), 2)
    
    # 获取检测结果
    detection_result = detector.detect_objects(frame)
    
    print(f"🏀 原始球类检测数量: {len(detection_result['soccer_balls'])}")
    print("🏀 球类详细信息:")
    for i, ball in enumerate(detection_result['soccer_balls']):
        print(f"   球{i+1}: 置信度={ball['confidence']:.3f}, 方法={ball.get('detection_method', 'unknown')}, 中心={ball['center']}")
    
    print(f"\n🥅 原始球门检测数量: {len(detection_result['goal_areas'])}")
    print("🥅 球门详细信息:")
    for i, goal in enumerate(detection_result['goal_areas']):
        print(f"   门{i+1}: 置信度={goal['confidence']:.3f}, 方法={goal.get('detection_method', 'unknown')}, bbox={goal['bbox']}")
    
    # 手动测试碰撞检测逻辑
    print(f"\n🔧 手动测试碰撞检测:")
    
    # 过滤后的球和门
    valid_balls = [ball for ball in detection_result['soccer_balls'] if ball['confidence'] > 0.4]
    valid_goals = [goal for goal in detection_result['goal_areas'] if goal['confidence'] > 0.3]
    
    print(f"   📏 置信度过滤后 - 球: {len(valid_balls)}, 门: {len(valid_goals)}")
    
    if valid_balls and valid_goals:
        ball = valid_balls[0]
        goal = valid_goals[0]
        
        ball_x, ball_y = ball['center']
        ball_bbox = ball['bbox']
        goal_bbox = goal['bbox']
        
        print(f"   🏀 球中心: ({ball_x:.1f}, {ball_y:.1f})")
        print(f"   🏀 球边界框: {ball_bbox}")
        print(f"   🥅 门边界框: {goal_bbox}")
        
        # 检查球是否在门内
        ball_radius = max(ball_bbox[2] - ball_bbox[0], ball_bbox[3] - ball_bbox[1]) / 2
        ball_left = ball_x - ball_radius
        ball_right = ball_x + ball_radius
        ball_top = ball_y - ball_radius
        ball_bottom = ball_y + ball_radius
        
        print(f"   🏀 球完整边界: 左={ball_left:.1f}, 右={ball_right:.1f}, 上={ball_top:.1f}, 下={ball_bottom:.1f}")
        
        in_goal = (goal_bbox[0] < ball_left and ball_right < goal_bbox[2] and 
                  goal_bbox[1] < ball_top and ball_bottom < goal_bbox[3])
        
        print(f"   ⚽ 球是否完全在门内: {in_goal}")
        
        if not in_goal:
            # 检查简单的中心点是否在门内
            simple_in_goal = (goal_bbox[0] <= ball_x <= goal_bbox[2] and 
                            goal_bbox[1] <= ball_y <= goal_bbox[3])
            print(f"   ⚽ 球中心是否在门内: {simple_in_goal}")
    
    # 运行完整的碰撞检测
    collision = detector.check_ball_goal_collision(detection_result['soccer_balls'], detection_result['goal_areas'])
    print(f"\n💥 最终碰撞检测结果: {collision['has_collision']}")
    print(f"💥 碰撞类型: {collision.get('collision_type', 'None')}")

if __name__ == "__main__":
    debug_collision_detection()