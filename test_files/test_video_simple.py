#!/usr/bin/env python3
"""
简单的视频检测测试脚本 - 使用和你相同的方法
"""

import cv2
from ultralytics import YOLO
import os

def test_video_detection():
    """测试视频检测"""
    
    # 检查视频文件是否存在
    video_path = 'input_videos/08fd33_4.mp4'
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    print(f"✅ 找到视频文件: {video_path}")
    
    # 检查视频基本信息
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ 无法打开视频文件")
        return
    
    # 获取视频信息
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    print(f"📹 视频信息:")
    print(f"   分辨率: {width}x{height}")
    print(f"   帧率: {fps:.2f} FPS")
    print(f"   总帧数: {frame_count}")
    print(f"   时长: {duration:.2f} 秒")
    
    cap.release()
    
    # 测试YOLO模型
    print("\n🤖 加载YOLO模型...")
    try:
        model = YOLO('yolo11n.pt')
        print("✅ YOLO模型加载成功")
    except Exception as e:
        print(f"❌ YOLO模型加载失败: {e}")
        return
    
    # 使用和你完全相同的方法检测视频
    print(f"\n🔍 开始检测视频: {video_path}")
    print("这可能需要一些时间...")
    
    try:
        # 完全按照你的代码执行
        results = model.predict(video_path, save=True, conf=0.3)
        
        print(f"✅ 检测完成! 处理了 {len(results)} 帧")
        
        # 分析第一帧的结果
        if len(results) > 0:
            first_frame = results[0]
            print(f"\n📊 第一帧检测结果:")
            print(f"   检测到的对象数量: {len(first_frame.boxes) if first_frame.boxes is not None else 0}")
            
            if first_frame.boxes is not None:
                for i, box in enumerate(first_frame.boxes):
                    class_id = int(box.cls.item())
                    confidence = float(box.conf.item())
                    coords = box.xyxy[0].tolist()
                    
                    # 获取类别名称
                    class_name = model.names.get(class_id, f"class_{class_id}")
                    
                    print(f"   对象 {i+1}: {class_name} (ID:{class_id}) 置信度:{confidence:.3f}")
                    print(f"           坐标: [{coords[0]:.1f}, {coords[1]:.1f}, {coords[2]:.1f}, {coords[3]:.1f}]")
                    
                    # 特别关注运动球类 (class_id=32)
                    if class_id == 32:
                        print(f"           🏀 找到运动球类!")
            
            # 检查保存的结果
            runs_dir = "runs/detect"
            if os.path.exists(runs_dir):
                print(f"\n💾 检测结果已保存到: {runs_dir}")
                # 列出最新的预测结果目录
                predict_dirs = [d for d in os.listdir(runs_dir) if d.startswith('predict')]
                if predict_dirs:
                    latest_dir = max(predict_dirs, key=lambda x: os.path.getctime(os.path.join(runs_dir, x)))
                    print(f"   最新结果: {runs_dir}/{latest_dir}")
        else:
            print("⚠️ 没有检测到任何帧")
            
    except Exception as e:
        print(f"❌ 检测过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_video_detection()