#!/usr/bin/env python3
"""
直接运行你的代码
"""

from ultralytics import YOLO

# 完全按照你的代码
model = YOLO('yolo11n.pt')

# 这会显示逐帧输出
result = model.predict('input_videos/08fd33_4.mp4', save=True)

first_frame = result[0]
print(first_frame)

for box in first_frame.boxes:
    print(box)