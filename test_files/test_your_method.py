#!/usr/bin/env python3
"""
使用你的方法进行检测，但显示详细的逐帧信息
"""

from ultralytics import YOLO

def test_with_your_method():
    """使用你的调用方法，但显示详细输出"""
    
    print("🔍 使用你的方法进行检测...")
    print("代码: model.predict('input_videos/08fd33_4.mp4', save=True)")
    print()
    
    # 完全按照你的方法
    model = YOLO('yolo11n.pt')
    
    # 这里会显示和你要求一样的逐帧输出
    results = model.predict('input_videos/08fd33_4.mp4', save=True)
    
    print(f"\n✅ 检测完成! 总共处理了 {len(results)} 帧")
    
    # 分析第一帧 - 按照你的代码
    first_frame = results[0]
    print(f"\n📊 第一帧信息:")
    print(f"first_frame = {first_frame}")
    
    if first_frame.boxes is not None:
        print(f"\n📦 第一帧的所有检测框:")
        for i, box in enumerate(first_frame.boxes):
            print(f"box[{i}] = {box}")
    else:
        print("\n⚠️ 第一帧没有检测到任何对象")
    
    # 额外分析：找到有足球的帧
    print(f"\n⚽ 查找有足球的帧:")
    ball_frames = []
    
    for frame_idx, result in enumerate(results):
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls.item())
                if class_id == 32:  # sports ball
                    confidence = float(box.conf.item())
                    ball_frames.append({
                        'frame': frame_idx + 1,
                        'confidence': confidence,
                        'box': box
                    })
    
    if ball_frames:
        print(f"   找到 {len(ball_frames)} 个足球检测:")
        for ball in ball_frames[:10]:  # 显示前10个
            print(f"   帧{ball['frame']}: 置信度={ball['confidence']:.3f}")
            print(f"   box = {ball['box']}")
    else:
        print("   ❌ 没有检测到足球")
    
    # 统计所有检测类别
    print(f"\n📈 整个视频的检测统计:")
    all_classes = {}
    
    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls.item())
                class_name = model.names.get(class_id, f'class_{class_id}')
                
                if class_name in all_classes:
                    all_classes[class_name] += 1
                else:
                    all_classes[class_name] = 1
    
    for class_name, count in sorted(all_classes.items(), key=lambda x: x[1], reverse=True):
        print(f"   {class_name}: {count} 次检测")

def test_with_verbose():
    """使用verbose=True来显示详细输出"""
    
    print("🔍 使用verbose=True显示详细输出...")
    print()
    
    model = YOLO('yolo11n.pt')
    
    # 添加verbose=True来显示详细的逐帧信息
    results = model.predict('input_videos/08fd33_4.mp4', save=True, verbose=True)
    
    print(f"\n✅ 处理完成!")

if __name__ == "__main__":
    print("选择测试方法:")
    print("1. 你的原始方法 + 详细分析")
    print("2. 添加verbose=True显示逐帧输出")
    
    choice = input("输入选择 (1 或 2): ").strip()
    
    if choice == "2":
        test_with_verbose()
    else:
        test_with_your_method()