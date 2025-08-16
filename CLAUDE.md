# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ClipGoal-AI is a React Native mobile app with Python backend that uses YOLOv11 AI to detect soccer balls and goals in real-time video, automatically generating highlight clips when ball-goal collisions are detected. The app provides real-time visual feedback with bounding boxes around detected objects.

## Architecture

### Frontend (React Native + Expo)
- **Main App**: `frontend/App.tsx` - Root component with navigation setup
- **Navigation**: `frontend/navigation/TabNavigator.tsx` - Bottom tab navigation
- **Core Screen**: `frontend/screens/RecordScreen.tsx` - Camera interface with real-time AI detection visualization
- **API Integration**: WebSocket connection to backend for real-time detection streaming
- **Visualization**: SVG overlays for real-time bounding boxes and detection feedback

### Backend (FastAPI + WebSocket)
- **Main Server**: `backend/app.py` - FastAPI server with WebSocket support for real-time frame processing
- **Endpoints**: `/health`, `/detect` (single frame), `/clips` (saved clips), WebSocket `/ws` (real-time stream)
- **Frame Management**: Global frame buffer for 10-second clip extraction

### AI Detection System
- **Core Engine**: `ai_model/soccer_detector.py` - SoccerDetector class with multi-modal detection
- **Detection Methods**: 
  - YOLOv11 for sports ball detection (COCO class ID=32)
  - Color-based soccer ball detection (white/black patterns)
  - Line-based goal detection using Hough transforms and edge detection
- **Collision Detection**: Distance-based algorithms for ball-goal collision detection
- **Clip Generation**: Automatic 10-second highlight extraction when collisions detected

## Commands

### Backend Development
```bash
# Start backend server (auto-installs dependencies and downloads YOLO model)
python start_backend.py

# Manual backend startup
cd backend && uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Install backend dependencies
pip install -r backend/requirements.txt
pip install -r ai_model/requirements.txt
```

### Frontend Development
```bash
# Install dependencies
cd frontend && npm install

# Start development server
npm start

# Run on specific platforms
npm run android
npm run ios
npm run web
```

### Testing
```bash
# Test AI detection functionality
python test_detection.py

# Test WebSocket connection
# Open test_websocket.html in browser

# Test network connectivity
# Open network_test.html in browser
```

## Network Configuration

The app uses platform-specific API endpoints:
- **iOS**: `192.168.0.103:8000` (local IP required for device testing)
- **Android Emulator**: `10.0.2.2:8000` (emulator bridge IP)
- **Development**: Local IP address must be configured in RecordScreen.tsx

## Key Components and Interactions

### Real-time Detection Flow
1. **Camera Feed**: RecordScreen captures frames at ~500ms intervals
2. **Frame Processing**: Frames sent via WebSocket to backend
3. **AI Detection**: SoccerDetector processes frames using multi-modal approach
4. **Visualization**: Results returned to frontend for SVG overlay rendering
5. **Clip Generation**: Frame buffer maintains 10-second window for highlight extraction

### Detection Configuration
- **Confidence Threshold**: 0.3 (adjustable in soccer_detector.py:36)
- **IoU Threshold**: 0.4 (adjustable in soccer_detector.py:37)
- **Frame Buffer**: 300 frames (10 seconds at 30fps)
- **Collision Detection**: Ball radius + 10px threshold for contact detection

### Data Flow
- Frontend captures camera frames → WebSocket transmission → Backend AI processing → Detection results → Frontend visualization → Potential clip saving

## Development Notes

### Modifying Detection Parameters
- Adjust thresholds in `ai_model/soccer_detector.py` lines 36-37
- Color detection ranges configured in lines 43-48
- Ball size constraints in lines 74-82

### Adding New Sports
- Extend `soccer_detector.py` with sport-specific detection methods
- Update frontend UI to support new sport modes
- Modify YOLO class mappings as needed

### Network Issues Debugging
- Check backend service status: `curl http://localhost:8000/health`
- Verify WebSocket connectivity using test_websocket.html
- Update API_BASE_URL in RecordScreen.tsx for different network configurations

### Testing Detection
- Use `test_detection.py` to validate detection on synthetic images
- Check output files: `test_original.jpg` and `test_result.jpg` for visual verification
- Monitor console logs for detection statistics and performance metrics
- 项目所有的test file需要放在/Users/jameswang/Desktop/project/ClipGoal-AI/test_files 然后非必要不创建报告文件