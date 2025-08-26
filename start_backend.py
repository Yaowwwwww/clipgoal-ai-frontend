#!/usr/bin/env python3
"""
启动ClipGoal-AI后端服务
"""

import subprocess
import sys
import os
import time

def check_requirements():
    """检查依赖是否已安装"""
    try:
        import fastapi
        import uvicorn
        import cv2
        import numpy as np
        import ultralytics
        import torch
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return False

def install_requirements():
    """安装依赖"""
    requirements_files = [
        "backend/requirements.txt",
        "ai_model/requirements.txt"
    ]
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            print(f"正在安装 {req_file} 中的依赖...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file])

def download_yolo_model():
    """下载YOLOv11模型"""
    try:
        from ultralytics import YOLO
        print("正在下载YOLOv11模型...")
        model = YOLO('yolo11n.pt')  # 下载nano版本
        print("✅ YOLOv11模型下载完成")
        return True
    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        return False

def start_server():
    """启动FastAPI服务器"""
    try:
        os.chdir("backend")
        print("🚀 启动ClipGoal-AI后端服务...")
        print("服务地址: http://localhost:8000")
        print("API文档: http://localhost:8000/docs")
        print("按 Ctrl+C 停止服务")
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 服务已停止")
    except Exception as e:
        print(f"❌ 启动服务失败: {e}")

def main():
    print("🎯 ClipGoal-AI 后端服务启动脚本")
    print("=" * 40)
    
    # 检查并安装依赖
    if not check_requirements():
        print("正在安装依赖...")
        install_requirements()
        time.sleep(2)
    
    # 下载YOLO模型
    if not download_yolo_model():
        print("⚠️ 模型下载失败，但仍可继续启动服务")
    
    # 启动服务
    start_server()

if __name__ == "__main__":
    main()