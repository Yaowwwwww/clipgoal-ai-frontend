# ClipGoal-AI

一个基于YOLOv11的AI驱动足球检测和精彩片段自动剪辑应用。

## 功能特性

### 🤖 AI检测功能
- **足球实时检测**: 使用YOLOv11检测画面中的足球
- **方形球门识别**: 自动识别并标记球门区域
- **进球瞬间检测**: 智能判断进球时刻并发出提醒
- **轨迹追踪**: 实时追踪足球运动轨迹

### 📱 移动端功能
- **实时相机预览**: 支持iOS和Android
- **AI检测可视化**: 实时显示检测结果覆盖层
- **手动区域标记**: 支持手动划定关注区域
- **模式切换**: Goal-Oriented和Ground-Oriented两种模式

### 🔧 技术架构
- **前端**: React Native + Expo
- **后端**: FastAPI + WebSocket
- **AI模型**: YOLOv11 + PyTorch
- **实时通信**: WebSocket实时传输检测结果

## 快速开始

### 1. 环境要求
- Python 3.8+
- Node.js 16+
- React Native开发环境
- 摄像头设备

### 2. 安装后端
```bash
# 克隆项目
cd ClipGoal-AI

# 启动后端服务（自动安装依赖）
python start_backend.py
```

### 3. 安装前端
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

### 4. 运行应用
- 在手机上安装Expo Go应用
- 扫描二维码启动应用
- 进入Record页面开始使用AI检测

## 使用指南

### AI检测模式
1. 打开应用进入Record页面
2. 点击"🤖 AI关闭"按钮启用AI检测
3. 将相机对准足球场景
4. 系统将实时检测：
   - 🟢 绿色框: 足球位置
   - 🔴 红色框: 球门区域
   - ⚽ 进球提醒: 检测到进球时显示

### 手动标记模式
1. 关闭AI检测模式
2. 在画面上点击4个点标记关注区域
3. 按顺时针方向点击完成区域划定

### 检测信息
- 顶部面板显示检测状态
- 实时显示足球数量和球门检测状态
- 检测中状态指示

## API文档

后端服务启动后，可访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要端点
- `POST /detect`: 单张图片检测
- `WebSocket /ws`: 实时检测流
- `GET /health`: 健康检查

## 项目结构

```
ClipGoal-AI/
├── frontend/                 # React Native前端
│   ├── screens/
│   │   ├── RecordScreen.tsx  # 相机录制页面
│   │   ├── HomeScreen.tsx    # 首页
│   │   └── ...
│   └── navigation/           # 导航配置
├── backend/                  # FastAPI后端
│   ├── app.py               # 主应用
│   └── requirements.txt     # Python依赖
├── ai_model/                # AI模型
│   ├── soccer_detector.py   # 足球检测器
│   └── requirements.txt     # AI依赖
└── start_backend.py         # 后端启动脚本
```

## 配置说明

### 后端配置
- 默认端口: 8000
- WebSocket端点: `/ws`
- 检测频率: 每500ms一帧

### AI模型配置
- 模型: YOLOv11n (nano版本)
- 置信度阈值: 0.5
- IoU阈值: 0.4
- 支持类别: 足球、球员、球门柱、球门区域等

### 前端配置
- API地址: `http://localhost:8000`
- 检测可视化: SVG覆盖层
- 实时更新频率: 500ms

## 开发说明

### 自定义检测类别
在`ai_model/soccer_detector.py`中修改`class_names`字典：
```python
self.class_names = {
    0: 'soccer_ball',
    1: 'player',
    2: 'goal_post',
    # 添加新类别...
}
```

### 调整检测参数
```python
# 在SoccerDetector中调整
self.confidence_threshold = 0.5  # 置信度阈值
self.iou_threshold = 0.4         # IoU阈值
```

### 添加新的运动类型
1. 在`soccer_detector.py`中添加新的检测逻辑
2. 更新前端UI支持新的运动模式
3. 训练相应的模型数据

## 训练自定义模型

### 1. 准备数据集
```bash
# 数据集结构
soccer_dataset/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── data.yaml
```

### 2. 训练模型
```python
from ai_model.soccer_detector import SoccerDetector

detector = SoccerDetector()
detector.fine_tune(
    data_yaml='soccer_dataset/data.yaml',
    epochs=100,
    batch_size=16,
    sport_type='soccer'
)
```

## 故障排除

### 常见问题

1. **WebSocket连接失败**
   - 检查后端服务是否启动
   - 确认API_BASE_URL配置正确
   - 检查网络连接

2. **AI检测不工作**
   - 确认YOLOv11模型已下载
   - 检查Python依赖是否完整安装
   - 查看后端日志错误信息

3. **相机权限问题**
   - 在设备设置中授权相机权限
   - 重启应用重新请求权限

4. **检测精度不高**
   - 确保光线充足
   - 保持相机稳定
   - 考虑训练自定义模型

## 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境设置
1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

MIT License - 详见LICENSE文件

## 联系方式

如有问题或建议，请通过以下方式联系：
- GitHub Issues
- Email: your-email@example.com

---

**ClipGoal-AI** - 让AI帮你捕捉每一个精彩瞬间！ ⚽🤖