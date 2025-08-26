# ClipGoal-AI Frontend

ClipGoal-AI 前端移动应用 - React Native + Expo实现的实时足球检测和录制应用

## 技术栈
- **React Native** (0.79.5) - 跨平台移动开发
- **Expo** (53.0.20) - 开发和部署平台  
- **TypeScript** - 类型安全
- **React Navigation** - 导航组件
- **Expo Camera** - 相机功能
- **React Native SVG** - 图形绘制

## 功能特性
- 📱 跨平台移动应用 (iOS/Android)
- 📹 实时相机预览和录制
- ⚽ 实时足球检测可视化
- 🥅 手动球门区域标注
- 🔴 大型录制按钮设计
- 🌐 WebSocket实时通信
- 📊 检测状态可视化

## 快速启动

### 环境要求
- Node.js 16+
- npm 或 yarn
- Expo CLI
- iOS模拟器 或 Android模拟器/设备

### 安装依赖
```bash
npm install
```

### 启动开发服务
```bash
npm start
```

### 运行到特定平台
```bash
npm run ios      # iOS模拟器
npm run android  # Android模拟器/设备
npm run web      # Web浏览器
```

## 配置说明

### 网络配置
在 `screens/RecordScreen.tsx` 中配置后端API地址：

```typescript
const getApiUrl = () => {
  if (Platform.OS === 'ios') {
    return 'http://YOUR_IP:8000'; // 替换为你的IP
  } else if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000'; // Android模拟器
  }
};
```

### 相机权限
应用会自动请求相机权限，请确保授权以使用检测功能。

## 主要界面

### 欢迎页 (WelcomeScreen)
- 应用介绍和导航入口

### 主页 (HomeScreen) 
- 运动项目选择界面

### 录制页 (RecordScreen)
- **实时相机预览**
- **AI检测结果可视化** (绿色框标记足球)
- **球门手动标注** (蓝色区域)
- **录制控制** (大红色圆形按钮)
- **检测状态指示器**

### 库页 (LibraryScreen)
- 录制的视频片段管理

## 核心功能

### 实时检测
- 每秒向后端发送帧进行AI分析
- 实时显示检测结果和边界框
- 置信度和坐标信息展示

### 球门标注
- 点击"标注球门"进入标注模式
- 按顺时针顺序点击4个角点
- 自动生成球门检测区域

### 录制功能
- 大红色圆形录制按钮
- 支持开始/停止录制
- 录制状态实时反馈
- 自动碰撞触发录制

### 碰撞检测
- 足球与球门区域重叠检测
- 自动触发录制功能
- 视觉提示和状态更新

## 文件结构
```
├── screens/           # 主要界面
│   ├── RecordScreen.tsx    # 核心录制界面
│   ├── HomeScreen.tsx      # 主页
│   ├── WelcomeScreen.tsx   # 欢迎页
│   └── LibraryScreen.tsx   # 视频库
├── navigation/        # 导航配置
│   └── TabNavigator.tsx    # 底部标签导航
├── assets/           # 静态资源
└── App.tsx          # 应用入口
```

## 开发说明

### 调试
- 使用Expo开发工具调试
- 摇动设备打开开发菜单
- 支持热重载和实时编辑

### 构建发布
```bash
# 创建构建
expo build:ios
expo build:android

# 或使用EAS Build
eas build --platform ios
eas build --platform android
```

## 网络配置指南

### iOS真机测试
需要配置本地IP地址，确保设备和开发机在同一WiFi网络

### Android模拟器
使用 `10.0.2.2` 作为host地址访问开发机

### 网络问题排查
1. 确保后端服务运行在 `0.0.0.0:8000`
2. 检查防火墙设置
3. 使用 `network_test.html` 测试连接

## 与后端集成
后端项目地址：https://github.com/Yaowwwwww/clipgoal-ai-backend

## 许可证
MIT License
