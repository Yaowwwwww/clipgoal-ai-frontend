#!/usr/bin/env python3
"""
逐帧检测并输出和你要求相同的格式
"""

import cv2
import time
from ultralytics import YOLO

def test_frame_by_frame_detection():
    """逐帧检测并输出详细信息"""
    
    video_path = 'input_videos/08fd33_4.mp4'
    model = YOLO('yolo11n.pt')
    
    # 打开视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 无法打开视频文件: {video_path}")
        return
    
    # 获取视频信息
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📹 视频信息: {width}x{height}, {fps}fps, {total_frames}帧")
    print(f"🔍 开始逐帧检测...")
    print()
    
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # 记录开始时间
        start_time = time.time()
        
        # 进行检测
        results = model.predict(frame, conf=0.3, verbose=False)
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        # 统计检测结果
        detection_summary = []
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                # 统计各类别的数量
                class_counts = {}
                for box in result.boxes:
                    class_id = int(box.cls.item())
                    class_name = model.names.get(class_id, f'class_{class_id}')
                    
                    if class_name in class_counts:
                        class_counts[class_name] += 1
                    else:
                        class_counts[class_name] = 1
                
                # 按照YOLO输出格式排序和格式化
                for class_name, count in sorted(class_counts.items()):
                    if class_name == 'person':
                        detection_summary.insert(0, f"{count} {class_name}s")  # persons放在最前面
                    elif class_name == 'sports ball':
                        detection_summary.append(f"{count} sports ball")
                    else:
                        detection_summary.append(f"{count} {class_name}")
        
        # 构建输出字符串 - 完全模拟你要求的格式
        detection_str = ", ".join(detection_summary) if detection_summary else ""
        if detection_str:
            detection_str = " " + detection_str + ","
        
        # 输出格式完全匹配你的要求
        output_resolution = f"{height}x{width}"  # 注意：YOLO输出是高x宽
        print(f"video 1/1 (frame {frame_count}/{total_frames}) {video_path}: {output_resolution}{detection_str} {processing_time:.1f}ms")
        
        # 可选：只处理一部分帧来快速测试
        # if frame_count >= 200:  # 只处理前200帧
        #     break
    
    cap.release()
    print(f"\n✅ 处理完成，共{frame_count}帧")

def test_specific_range(start_frame=140, end_frame=165):
    """测试特定帧范围，模拟你提供的输出"""
    
    video_path = 'input_videos/08fd33_4.mp4'
    model = YOLO('yolo11n.pt')
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ 无法打开视频文件: {video_path}")
        return
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    
    print(f"🎯 测试帧{start_frame}-{end_frame}，模拟你的输出格式:")
    print()
    
    # 跳到起始帧
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame - 1)
    
    for frame_num in range(start_frame, min(end_frame + 1, total_frames + 1)):
        ret, frame = cap.read()
        if not ret:
            break
        
        start_time = time.time()
        results = model.predict(frame, conf=0.3, verbose=False)
        processing_time = (time.time() - start_time) * 1000
        
        # 统计检测结果
        detection_summary = []
        
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                class_counts = {}
                for box in result.boxes:
                    class_id = int(box.cls.item())
                    class_name = model.names.get(class_id, f'class_{class_id}')
                    
                    if class_name in class_counts:
                        class_counts[class_name] += 1
                    else:
                        class_counts[class_name] = 1
                
                # 格式化输出
                for class_name, count in sorted(class_counts.items()):
                    if class_name == 'person':
                        detection_summary.insert(0, f"{count} {class_name}s")
                    elif class_name == 'sports ball':
                        detection_summary.append(f"{count} sports ball")
                    else:
                        detection_summary.append(f"{count} {class_name}")
        
        detection_str = ", ".join(detection_summary) if detection_summary else ""
        if detection_str:
            detection_str = " " + detection_str + ","
        
        output_resolution = f"{height}x{width}"
        print(f"video 1/1 (frame {frame_num}/{total_frames}) {video_path}: {output_resolution}{detection_str} {processing_time:.1f}ms")
    
    cap.release()

if __name__ == "__main__":
    # 选择运行哪个测试
    print("请选择:")
    print("1. 测试特定帧范围(141-164) - 快速验证格式")
    print("2. 完整视频逐帧检测 - 完整测试")
    
    choice = input("输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        test_specific_range(141, 164)
    elif choice == "2":
        test_frame_by_frame_detection()
    else:
        print("默认运行特定帧范围测试...")
        test_specific_range(141, 164)