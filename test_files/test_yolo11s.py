#!/usr/bin/env python3
"""
测试YOLO11s模型性能
"""

from ultralytics import YOLO
import time

def test_yolo11s():
    """测试YOLO11s模型"""
    
    print("🔍 测试YOLO11s模型...")
    print("📥 正在下载YOLO11s模型...")
    
    # 下载并加载YOLO11s模型
    model = YOLO('yolo11s.pt')
    
    print("✅ YOLO11s模型加载完成")
    print("📹 开始测试iOS视频...")
    
    # 测试处理时间
    start_time = time.time()
    
    # 使用YOLO11s处理视频
    results = model.predict('input_videos/08fd33_4.mp4', save=True, conf=0.3, verbose=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n📊 YOLO11s性能统计:")
    print(f"   总处理时间: {total_time:.2f}秒")
    print(f"   总帧数: {len(results)}")
    print(f"   平均每帧处理时间: {total_time/len(results)*1000:.1f}ms")
    
    # 统计足球检测
    ball_frames = []
    for frame_idx, result in enumerate(results):
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls.item())
                if class_id == 32:  # sports ball
                    confidence = float(box.conf.item())
                    ball_frames.append({
                        'frame': frame_idx + 1,
                        'confidence': confidence
                    })
    
    print(f"\n⚽ 足球检测结果:")
    if ball_frames:
        print(f"   检测到足球的帧数: {len(ball_frames)}")
        confidences = [b['confidence'] for b in ball_frames]
        print(f"   置信度范围: {min(confidences):.3f} - {max(confidences):.3f}")
        print(f"   平均置信度: {sum(confidences)/len(confidences):.3f}")
        print(f"   足球检测帧: {[b['frame'] for b in ball_frames]}")
    else:
        print("   ❌ 没有检测到足球")
    
    print(f"\n💾 结果保存到: runs/detect/predict/")

if __name__ == "__main__":
    test_yolo11s()