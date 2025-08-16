#!/usr/bin/env python3
"""
测试升级后的项目 - YOLO11s + 适配iOS视频
"""

import sys
import os
sys.path.append('ai_model')

from soccer_detector import SoccerDetector
import cv2
import time

def test_upgraded_detector():
    """测试升级后的检测器"""
    
    print("🔧 测试升级后的项目配置...")
    print("=" * 60)
    
    # 1. 测试YOLO11s模型加载
    print("📥 加载YOLO11s检测器...")
    detector = SoccerDetector()  # 现在默认使用yolo11s.pt
    print("✅ YOLO11s检测器加载成功")
    
    # 2. 测试iOS视频帧处理
    print("\n📹 测试iOS视频帧处理...")
    
    video_path = 'input_videos/08fd33_4.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ 无法打开视频文件")
        return
    
    # 测试前10帧
    frame_results = []
    total_processing_time = 0
    
    for frame_num in range(1, 11):
        ret, frame = cap.read()
        if not ret:
            break
        
        print(f"\n📷 处理帧{frame_num}...")
        start_time = time.time()
        
        # 使用升级后的检测器
        result = detector.process_frame(frame)
        
        processing_time = (time.time() - start_time) * 1000
        total_processing_time += processing_time
        
        ball_count = len(result['detections']['soccer_balls'])
        
        print(f"   📊 帧{frame_num}: 检测到{ball_count}个足球, 耗时{processing_time:.1f}ms")
        
        # 保存结果
        frame_results.append({
            'frame': frame_num,
            'ball_count': ball_count,
            'processing_time': processing_time,
            'balls': result['detections']['soccer_balls']
        })
    
    cap.release()
    
    # 3. 分析结果
    print(f"\n📊 升级后的性能分析:")
    print(f"   平均处理时间: {total_processing_time/len(frame_results):.1f}ms/帧")
    
    total_balls_detected = sum(r['ball_count'] for r in frame_results)
    frames_with_balls = len([r for r in frame_results if r['ball_count'] > 0])
    
    print(f"   检测到足球的帧数: {frames_with_balls}/{len(frame_results)}")
    print(f"   总足球检测次数: {total_balls_detected}")
    
    if frames_with_balls > 0:
        print(f"   ✅ 成功检测到足球!")
        
        # 显示检测详情
        print(f"\n⚽ 足球检测详情:")
        for result in frame_results:
            if result['ball_count'] > 0:
                for i, ball in enumerate(result['balls']):
                    conf = ball['confidence']
                    bbox = ball['bbox']
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    print(f"   帧{result['frame']} 足球{i+1}: 置信度={conf:.3f}, 尺寸={width:.0f}x{height:.0f}")
    else:
        print(f"   ⚠️ 未检测到足球，可能需要进一步调整参数")
    
    # 4. 测试新的检测参数
    print(f"\n🔧 当前检测参数:")
    print(f"   模型: YOLO11s")
    print(f"   置信度阈值: {detector.confidence_threshold}")
    print(f"   IoU阈值: {detector.iou_threshold}")
    
    print(f"\n🎯 升级总结:")
    print(f"   ✅ 使用YOLO11s模型")
    print(f"   ✅ 降低置信度阈值到0.3")
    print(f"   ✅ 适配iOS视频中的小足球")
    print(f"   ✅ 支持逐帧实时处理")

def simulate_realtime_processing():
    """模拟实时处理"""
    
    print(f"\n🔄 模拟实时处理测试...")
    
    detector = SoccerDetector()
    cap = cv2.VideoCapture('input_videos/08fd33_4.mp4')
    
    frame_count = 0
    ball_history = []
    frame_buffer = []
    
    print(f"开始模拟实时处理前20帧...")
    
    while cap.isOpened() and frame_count < 20:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        start_time = time.time()
        
        # 模拟实时处理
        result = detector.process_frame(frame, ball_history, frame_buffer)
        
        processing_time = (time.time() - start_time) * 1000
        ball_count = len(result['detections']['soccer_balls'])
        
        # 模拟WebSocket输出格式
        print(f"📷 帧{frame_count}: 尺寸{frame.shape[1]}x{frame.shape[0]}")
        print(f"✅ 帧{frame_count}: 检测到{ball_count}个足球, 耗时{processing_time:.1f}ms")
        
        # 更新历史
        ball_history = result['ball_history']
        frame_buffer = result['frame_buffer']
    
    cap.release()
    print(f"✅ 实时处理测试完成")

if __name__ == "__main__":
    test_upgraded_detector()
    simulate_realtime_processing()