#!/usr/bin/env python3
"""
测试调整后的检测参数
"""

import cv2
import numpy as np
from ultralytics import YOLO
import sys
import os

# 添加 ai_model 目录到路径
sys.path.append('ai_model')

class AdjustedSoccerDetector:
    """调整参数的足球检测器"""
    
    def __init__(self, model_path: str = 'yolo11n.pt'):
        self.model = YOLO(model_path)
        
        # 🔧 调整后的参数 - 适配小足球和iOS视频
        self.confidence_threshold = 0.2  # 降低置信度要求
        self.iou_threshold = 0.4
        
        self.ball_classes = {
            32: 'sports ball',
        }
    
    def detect_objects(self, frame: np.ndarray) -> dict:
        """检测物体"""
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        detections = []
        soccer_balls = []
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()
                
                for box, conf, cls in zip(boxes, confidences, classes):
                    x1, y1, x2, y2 = box
                    class_id = int(cls)
                    
                    detection = {
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': float(conf),
                        'class_id': int(class_id),
                        'class_name': self.ball_classes.get(class_id, f'class_{class_id}'),
                        'center': [float((x1 + x2) / 2), float((y1 + y2) / 2)],
                        'detection_method': 'yolo_adjusted'
                    }
                    
                    detections.append(detection)
                    
                    # 检测运动球类，使用调整后的条件
                    if class_id == 32 and conf > 0.15:  # 大幅降低置信度要求
                        box_width = x2 - x1
                        box_height = y2 - y1
                        aspect_ratio = box_width / box_height
                        box_area = box_width * box_height
                        
                        # 🔧 调整后的验证条件 - 适配小球
                        if (0.5 < aspect_ratio < 2.5 and      # 放宽宽高比
                            300 < box_area < 10000 and       # 大幅降低面积要求
                            box_width > 15 and box_height > 15):  # 降低最小尺寸
                            soccer_balls.append(detection)
        
        return {
            'detections': detections,
            'soccer_balls': soccer_balls,
            'goal_areas': [],
            'frame_shape': frame.shape
        }

def test_video_with_adjusted_params():
    """使用调整后的参数测试视频"""
    
    video_path = 'input_videos/08fd33_4.mp4'
    detector = AdjustedSoccerDetector()
    
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    ball_detections = []
    
    print("🔍 使用调整后的参数测试检测...")
    
    # 测试前50帧
    while cap.isOpened() and frame_count < 50:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # 使用调整后的检测器
        result = detector.detect_objects(frame)
        
        if result['soccer_balls']:
            for ball in result['soccer_balls']:
                ball_detections.append({
                    'frame': frame_count,
                    'confidence': ball['confidence'],
                    'bbox': ball['bbox'],
                    'center': ball['center']
                })
                
                bbox = ball['bbox']
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]
                
                print(f"⚽ 帧{frame_count}: 置信度={ball['confidence']:.3f}, 尺寸={width:.0f}x{height:.0f}")
    
    cap.release()
    
    print(f"\n📊 调整后的检测结果:")
    print(f"   检测到足球的帧数: {len(ball_detections)}")
    
    if ball_detections:
        confidences = [d['confidence'] for d in ball_detections]
        print(f"   置信度范围: {min(confidences):.3f} - {max(confidences):.3f}")
        print(f"   平均置信度: {np.mean(confidences):.3f}")
        print(f"   ✅ 成功检测到足球!")
        
        # 保存一帧带检测框的图像
        cap = cv2.VideoCapture(video_path)
        best_detection = max(ball_detections, key=lambda x: x['confidence'])
        best_frame_num = best_detection['frame']
        
        # 跳到最佳检测帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, best_frame_num - 1)
        ret, frame = cap.read()
        
        if ret:
            # 绘制检测框
            bbox = best_detection['bbox']
            cv2.rectangle(frame, 
                         (int(bbox[0]), int(bbox[1])), 
                         (int(bbox[2]), int(bbox[3])), 
                         (0, 255, 0), 2)
            
            # 添加标签
            label = f"Ball {best_detection['confidence']:.3f}"
            cv2.putText(frame, label, 
                       (int(bbox[0]), int(bbox[1]) - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 保存图像
            cv2.imwrite('ios_ball_detected.jpg', frame)
            print(f"   💾 保存检测结果图像: ios_ball_detected.jpg")
        
        cap.release()
    else:
        print("   ❌ 仍然没有检测到足球")
    
    # 建议的修改
    print(f"\n💡 建议修改 soccer_detector.py:")
    print(f"   1. 将 confidence_threshold 从 0.95 改为 0.2")
    print(f"   2. 将面积要求从 1500-25000 改为 300-10000") 
    print(f"   3. 将最小尺寸从 30x30 改为 15x15")
    print(f"   4. 放宽宽高比要求从 0.7-1.4 改为 0.5-2.5")

if __name__ == "__main__":
    test_video_with_adjusted_params()