#!/usr/bin/env python3
"""
检查足球检测的置信度
"""

import cv2
from ultralytics import YOLO
import numpy as np

def check_ball_detection_confidence():
    """检查足球检测的具体置信度"""
    
    video_path = 'input_videos/08fd33_4.mp4'
    model = YOLO('yolo11n.pt')
    
    # 只处理前100帧来快速检查
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    ball_detections = []
    
    print("🔍 分析足球检测置信度...")
    
    while cap.isOpened() and frame_count < 100:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # 使用较低的置信度阈值来看所有检测
        results = model.predict(frame, conf=0.1, verbose=False)
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    
                    # 检查是否为运动球类 (class_id = 32)
                    if class_id == 32:
                        coords = box.xyxy[0].tolist()
                        width = coords[2] - coords[0]
                        height = coords[3] - coords[1]
                        area = width * height
                        aspect_ratio = width / height
                        
                        ball_info = {
                            'frame': frame_count,
                            'confidence': confidence,
                            'bbox': coords,
                            'width': width,
                            'height': height,
                            'area': area,
                            'aspect_ratio': aspect_ratio
                        }
                        ball_detections.append(ball_info)
                        
                        print(f"⚽ 帧{frame_count}: 置信度={confidence:.3f}, 尺寸={width:.0f}x{height:.0f}, 宽高比={aspect_ratio:.2f}")
    
    cap.release()
    
    if ball_detections:
        print(f"\n📊 足球检测统计:")
        print(f"   总共检测到足球的帧数: {len(ball_detections)}")
        
        confidences = [d['confidence'] for d in ball_detections]
        areas = [d['area'] for d in ball_detections]
        aspect_ratios = [d['aspect_ratio'] for d in ball_detections]
        
        print(f"   置信度范围: {min(confidences):.3f} - {max(confidences):.3f}")
        print(f"   平均置信度: {np.mean(confidences):.3f}")
        print(f"   面积范围: {min(areas):.0f} - {max(areas):.0f}")
        print(f"   宽高比范围: {min(aspect_ratios):.2f} - {max(aspect_ratios):.2f}")
        
        # 检查有多少检测满足项目的严格要求
        strict_detections = []
        for d in ball_detections:
            if (d['confidence'] > 0.95 and
                0.7 < d['aspect_ratio'] < 1.4 and
                1500 < d['area'] < 25000 and
                d['width'] > 30 and d['height'] > 30):
                strict_detections.append(d)
        
        print(f"\n🎯 满足项目严格要求的检测:")
        print(f"   数量: {len(strict_detections)}")
        if strict_detections:
            for d in strict_detections:
                print(f"   帧{d['frame']}: 置信度={d['confidence']:.3f}")
        else:
            print("   ❌ 没有检测满足项目的严格要求 (置信度>0.95)")
            
        # 检查稍微放宽要求后的结果
        relaxed_detections = []
        for d in ball_detections:
            if (d['confidence'] > 0.5 and  # 降低置信度要求
                0.5 < d['aspect_ratio'] < 2.0 and  # 放宽宽高比
                500 < d['area'] < 50000 and  # 放宽面积要求
                d['width'] > 20 and d['height'] > 20):  # 降低最小尺寸
                relaxed_detections.append(d)
        
        print(f"\n🔄 放宽要求后的检测:")
        print(f"   数量: {len(relaxed_detections)}")
        if relaxed_detections:
            print("   前5个检测:")
            for d in relaxed_detections[:5]:
                print(f"   帧{d['frame']}: 置信度={d['confidence']:.3f}, 尺寸={d['width']:.0f}x{d['height']:.0f}")
    else:
        print("❌ 在前100帧中没有检测到任何足球")

if __name__ == "__main__":
    check_ball_detection_confidence()