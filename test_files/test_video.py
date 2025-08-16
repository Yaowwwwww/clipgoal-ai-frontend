#!/usr/bin/env python3
"""
测
试iOS视频的YOLO检测 - 输出逐帧结果
"""

from ultralytics import YOLO

def test_video():
    """测试视频检测并显示逐帧输出"""
    
    print("🔍 开始测试iOS视频检测...")
    print("📹 视频路径: input_videos/08fd33_4.mp4")
    print("🤖 使用模型: yolo11n.pt")
    print("=" * 60)
    
    # 加载YOLO模型
    model = YOLO('yolo11n.pt')
    
    # 检测视频 - 这会显示你要求的逐帧输出格式
    results = model.predict('input_videos/08fd33_4.mp4', save=True, conf=0.3)
    
    print("=" * 60)
    print(f"✅ 检测完成！处理了 {len(results)} 帧")
    
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
        print(f"   足球检测帧:")
        for ball in ball_frames:
            print(f"   - 帧{ball['frame']}: 置信度={ball['confidence']:.3f}")
    else:
        print("   ❌ 没有检测到足球")
    
    print(f"\n💾 检测结果已保存到: runs/detect/predict/")
    print(f"🎯 测试完成！")

if __name__ == "__main__":
    test_video()