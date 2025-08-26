import React, { useRef, useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  TouchableOpacity,
  TouchableWithoutFeedback,
  Animated,
  Alert,
  Dimensions,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import {
  CameraView,
  useCameraPermissions,
  CameraType,
} from 'expo-camera';
import Svg, { Circle, Line, Rect, G, Polygon, Text as SvgText } from 'react-native-svg';
import { useIsFocused } from '@react-navigation/native';

type Point = { x: number; y: number };

interface Detection {
  bbox: number[];
  confidence: number;
  class_name: string;
  center: number[];
}

interface GoalArea {
  bbox: number[];
  width: number;
  height: number;
  center: number[];
  confidence: number;
  corners?: Point[];
}

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// 矩形重叠检测函数 - 更直观和准确
const doRectanglesOverlap = (rect1: { x1: number, y1: number, x2: number, y2: number }, 
                            rect2: { x1: number, y1: number, x2: number, y2: number }): boolean => {
  // 矩形overlap检测：如果两个矩形不重叠，返回false；否则返回true
  const noOverlap = (rect1.x2 < rect2.x1 ||   // rect1在rect2左边
                     rect2.x2 < rect1.x1 ||   // rect2在rect1左边  
                     rect1.y2 < rect2.y1 ||   // rect1在rect2上边
                     rect2.y2 < rect1.y1);    // rect2在rect1上边
  
  return !noOverlap;
};

// 从多边形计算边界矩形
const getBoundingRect = (polygon: Point[]): { x1: number, y1: number, x2: number, y2: number } => {
  const xs = polygon.map(p => p.x);
  const ys = polygon.map(p => p.y);
  
  return {
    x1: Math.min(...xs),
    y1: Math.min(...ys), 
    x2: Math.max(...xs),
    y2: Math.max(...ys)
  };
};



// 根据运行环境自动判断API地址
const getApiUrl = () => {
  if (__DEV__) {
    // 开发环境，根据平台和运行方式选择地址
    if (Platform.OS === 'ios') {
      // iOS模拟器和真机都可以使用局域网IP
      return 'http://10.0.0.50:8000';
    } else if (Platform.OS === 'android') {
      // Android模拟器使用特殊地址
      return 'http://10.0.2.2:8000';
    } else {
      // Web端使用localhost
      return 'http://localhost:8000';
    }
  } else {
    // 生产环境，使用实际服务器地址
    return 'http://10.0.0.50:8000';
  }
};

const API_BASE_URL = getApiUrl();

export default function RecordScreen() {
  /* ---------- 安全区域 ---------- */
  const insets = useSafeAreaInsets();
  
  /* ---------- 权限 ---------- */
  const [permission, requestPermission] = useCameraPermissions();
  
  // 自动请求权限（放在 useEffect 中）
  useEffect(() => {
    if (!permission || (!permission.granted && permission.canAskAgain)) {
      // 延迟请求以避免警告
      setTimeout(() => {
        requestPermission();
      }, 100);
    }
  }, [permission, requestPermission]);

  /* ---------- 相机引用 ---------- */
  const cameraRef = useRef<CameraView | null>(null);

  /* ---------- 页面聚焦 ---------- */
  const isFocused = useIsFocused();
  
  // 页面失焦时重置相机状态
  useEffect(() => {
    if (!isFocused) {
      setIsCameraReady(false);
      if (isRecording) {
        stopVideoRecording();
      }
    }
  }, [isFocused]);

  /* ---------- 淡入淡出动画 ---------- */
  const camOpacity = useRef(new Animated.Value(0)).current;   // 相机淡入
  const [frameSize, setFrameSize] = useState<{ w: number; h: number } | null>(null);

  /* ---------- AI检测状态 ---------- */
  const [aiEnabled, setAiEnabled] = useState(false);
  const [soccerBalls, setSoccerBalls] = useState<Detection[]>([]);
  const [isGoalMoment, setIsGoalMoment] = useState(false);
  const [webSocket, setWebSocket] = useState<WebSocket | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected');
  const isConnecting = useRef(false);
  
  /* ---------- 进球overlap检测状态 ---------- */
  const [hasGoalOverlap, setHasGoalOverlap] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingStartTime, setRecordingStartTime] = useState<number | null>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [shouldShowAlert, setShouldShowAlert] = useState(false);
  
  // === 新增：用 ref 记录上一帧是否重叠，避免闭包读到旧值 ===
  const overlapRef = useRef(false);
  const lastGoalAlertRef = useRef(0); // 进球 Alert 冷却时间戳


  // === 新增：本地点亮 GOAL 横幅 1.5s（不再只依赖后端字段）===
  const raiseLocalGoalBanner = () => {
    setIsGoalMoment(true);
    setTimeout(() => setIsGoalMoment(false), 1500);
  };

  /* ---------- 视频录制功能 ---------- */
  const startVideoRecording = async () => {
    console.log('🎥 准备开始录制，检查条件...');
    console.log('  - cameraRef.current:', !!cameraRef.current);
    console.log('  - isCameraReady:', isCameraReady);
    console.log('  - isRecording:', isRecording);
    
    // 检测是否在Expo Go中运行
    const isExpoGo = !!(global as any).expo;
    
    if (!cameraRef.current) {
      console.log('⚠️ 相机引用不存在');
      Alert.alert('⚠️ 提示', '相机未初始化', [{ text: '确定' }]);
      return;
    }
    
    if (!isCameraReady) {
      console.log('⚠️ 相机未就绪，等待中...');
      Alert.alert('⚠️ 提示', '相机正在准备中，请稍后再试', [{ text: '确定' }]);
      return;
    }
    
    if (isRecording) {
      console.log('⚠️ 已在录制中');
      return;
    }

    // 如果在Expo Go中，使用模拟录制
    if (isExpoGo) {
      console.log('📱 检测到Expo Go环境，使用模拟录制');
      simulateRecording();
      return;
    }

    try {
      console.log('🎥 开始真实录制视频...');
      setIsRecording(true);
      setRecordingStartTime(Date.now());

      // Expo Camera recordAsync API
      // 注意：Expo Go 中可能无法正常工作，需要使用开发构建或独立应用
      const video = await cameraRef.current.recordAsync({
        maxDuration: 10, // 最多录制10秒
        // 在iOS上需要指定codec
        ...(Platform.OS === 'ios' && { codec: 'h264' }),
      });

      console.log('✅ 视频录制完成:', video.uri);
      console.log('📹 视频详情:', {
        uri: video.uri,
        codec: video.codec,
        duration: `${(Date.now() - (recordingStartTime || Date.now())) / 1000}秒`
      });
      
      // TODO: 保存视频到相册或上传
      // 可以使用 expo-media-library 保存到相册
      
      setIsRecording(false);
      setRecordingStartTime(null);
      
      // 显示成功提示
      Alert.alert(
        '✅ 录制完成',
        `视频已保存，时长: ${Math.round((Date.now() - (recordingStartTime || Date.now())) / 1000)}秒`,
        [{ text: '确定' }]
      );
    } catch (error) {
      console.error('❌ 录制失败:', error);
      setIsRecording(false);
      setRecordingStartTime(null);
      
      const errorMessage = (error as any).message || String(error);
      
      // 如果是用户手动停止，不显示错误
      if (errorMessage.includes('Recording was stopped')) {
        console.log('📹 录制被用户停止');
      } else if (errorMessage.includes('Camera is not ready')) {
        console.log('⚠️ 相机未就绪错误');
        Alert.alert('⚠️ 相机未就绪', '请等待相机准备完成后再试', [{ text: '确定' }]);
      } else {
        Alert.alert('❌ 录制失败', errorMessage.substring(0, 100), [{ text: '确定' }]);
      }
    }
  };

  // 模拟录制功能（用于Expo Go测试）
  const simulateRecording = () => {
    console.log('🎬 开始模拟录制（Expo Go环境）');
    setIsRecording(true);
    setRecordingStartTime(Date.now());
    
    Alert.alert(
      '📱 Expo Go 提示',
      '视频录制在Expo Go中存在限制。\n当前为模拟录制模式，仅用于测试UI流程。\n\n要使用真实录制功能，请使用：\n• EAS Build 开发构建\n• 或导出独立应用',
      [{ text: '了解' }]
    );
    
    // 模拟10秒后自动停止
    setTimeout(() => {
      if (isRecording) {
        console.log('🎬 模拟录制完成');
        setIsRecording(false);
        setRecordingStartTime(null);
        Alert.alert(
          '✅ 模拟录制完成',
          '模拟录制10秒完成（仅UI演示）',
          [{ text: '确定' }]
        );
      }
    }, 10000);
  };

  const stopVideoRecording = async () => {
    if (!cameraRef.current || !isRecording) {
      return;
    }

    try {
      console.log('⏹️ 停止录制...');
      await cameraRef.current.stopRecording();
      setIsRecording(false);
      setRecordingStartTime(null);
    } catch (error) {
      console.error('❌ 停止录制失败:', error);
      setIsRecording(false);
      setRecordingStartTime(null);
    }
  };
  
  // 足球检测状态管理
  const [detectionStatus, setDetectionStatus] = useState<{
    hasFootball: boolean;
    confidence: number;
    lastDetectionTime: number;
  }>({ hasFootball: false, confidence: 0, lastDetectionTime: 0 });
  
  const detectionTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  
  /* ---------- 手动球门标注状态 ---------- */
  const [isAnnotatingGoal, setIsAnnotatingGoal] = useState(false);
  const [goalCorners, setGoalCorners] = useState<Point[]>([]);
  const [manualGoalArea, setManualGoalArea] = useState<Point[] | null>(null);
  


  // 更新检测状态的函数
  const updateDetectionStatus = (hasValidBalls: boolean, confidence: number) => {
    const currentTime = Date.now();
    
    if (hasValidBalls) {
      // 检测到足球，立即更新状态（可以被新的绿色打断）
      if (detectionTimeoutRef.current) {
        clearTimeout(detectionTimeoutRef.current);
      }
      
      setDetectionStatus({
        hasFootball: true,
        confidence,
        lastDetectionTime: currentTime
      });
      
      // 设置1秒后允许变为红色
      detectionTimeoutRef.current = setTimeout(() => {
        setDetectionStatus(prev => {
          // 只有在1秒内没有新的检测时才变为红色
          if (currentTime === prev.lastDetectionTime) {
            return { hasFootball: false, confidence: 0, lastDetectionTime: currentTime };
          }
          return prev;
        });
      }, 1000);
    } else {
      // 没有检测到足球，检查是否在保护期内
      const timeSinceLastDetection = currentTime - detectionStatus.lastDetectionTime;
      if (timeSinceLastDetection >= 1000) {
        // 超过1秒保护期，可以变为红色
        setDetectionStatus({
          hasFootball: false,
          confidence: 0,
          lastDetectionTime: currentTime
        });
      }
      // 否则保持当前状态不变
    }
  };

  /* ---------- 球门标注处理函数 ---------- */
  const handleGoalAnnotation = (event: any) => {
    console.log('🎯 handleGoalAnnotation被调用，isAnnotatingGoal:', isAnnotatingGoal);
    
    if (!isAnnotatingGoal) {
      console.log('⚠️ 不在标注模式，忽略触摸');
      return;
    }
    
    console.log('🎯 检测到触摸事件，开始处理坐标');
    
    // Pressable的onPress事件提供的是nativeEvent
    const nativeEvent = event.nativeEvent;
    console.log('🎯 nativeEvent:', nativeEvent);
    
    // 在Pressable中，坐标在nativeEvent的pageX和pageY
    const x = nativeEvent.pageX || nativeEvent.locationX || 100;
    const y = nativeEvent.pageY || nativeEvent.locationY || 100;
    
    const newPoint = { x, y };
    
    console.log('📍 新增坐标点:', newPoint, `当前是第${goalCorners.length + 1}个点`);
    
    const newCorners = [...goalCorners, newPoint];
    setGoalCorners(newCorners);
    console.log('📍 更新后的角点数组:', newCorners);
    
    // 当标注完4个角点时，完成标注
    if (newCorners.length === 4) {
      console.log('📍 4个角点已收集完成，保存到manualGoalArea');
      setManualGoalArea(newCorners);
      setIsAnnotatingGoal(false);
      console.log('✅ 球门标注完成！');
      console.log('📍 球门四个角坐标:', newCorners.map(p => `(${Math.round(p.x)}, ${Math.round(p.y)})`).join(', '));
      
      // 立即显示成功Alert
      Alert.alert(
        '✅ 球门标注成功',
        `已保存球门区域，坐标：\n${newCorners.map((p, i) => `角${i+1}: (${Math.round(p.x)}, ${Math.round(p.y)})`).join('\n')}`,
        [{ text: '确定', onPress: () => console.log('✅ 标注成功确认') }]
      );
    }
  };
  
  const startGoalAnnotation = () => {
    console.log('🎯 启动球门标注模式');
    setIsAnnotatingGoal(true);
    setGoalCorners([]);
    setManualGoalArea(null);
    console.log('🎯 状态设置完成: isAnnotatingGoal=true, goalCorners=[], manualGoalArea=null');
    console.log('🎯 请按顺时针方向点击4个角点');
    
    // 添加提示
    setTimeout(() => {
      Alert.alert(
        '🥅 球门标注',
        '请按顺时针方向点击球门的4个角点',
        [{ text: '开始标注', style: 'default' }]
      );
    }, 200);
  };
  
  const clearGoalAnnotation = () => {
    setIsAnnotatingGoal(false);
    setGoalCorners([]);
    setManualGoalArea(null);
    setHasGoalOverlap(false);
    setShouldShowAlert(false);
    overlapRef.current = false;
    console.log('🧹 清除球门标注');
  };
  
  // 页面聚焦：开启AI并连接WS；失焦时清理
  useEffect(() => {
    if (isFocused) {
      // 进入页面：开启检测 & 连接 WebSocket
      setAiEnabled(true);
      camOpacity.setValue(0);
      const t = setTimeout(() => {
        connectWebSocket();
      }, 300);
      return () => clearTimeout(t);
    } else {
      // 离开页面：关闭检测 & 断开 WebSocket，并清理状态
      setAiEnabled(false);
      setIsDetecting(false);
      disconnectWebSocket();

      if (detectionTimeoutRef.current) {
        clearTimeout(detectionTimeoutRef.current);
        detectionTimeoutRef.current = null;
      }

      setHasGoalOverlap(false);
      setShouldShowAlert(false);
      overlapRef.current = false; // 复位上帧重叠标记
    }
  }, [isFocused]);


  /* ---------- 页面聚焦时：初始化相机 ---------- */
  useEffect(() => {
    if (shouldShowAlert && !isAnnotatingGoal) {
      Alert.alert('🥅 进球检测！', '足球与球门重叠！', [
        { text: '确定', onPress: () => {} },
      ]);
      setShouldShowAlert(false);
    }
  }, [shouldShowAlert, isAnnotatingGoal]);


  /* ---------- WebSocket连接管理 ---------- */
  const connectWebSocket = () => {
    if (isConnecting.current || webSocket?.readyState === WebSocket.OPEN) {
      return; // 避免重复连接
    }
    
    isConnecting.current = true;
    try {
      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws`;
      console.log('尝试连接WebSocket:', wsUrl);
      console.log('当前平台:', Platform.OS);
      console.log('API地址:', API_BASE_URL);
      
      setConnectionStatus('connecting');
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ WebSocket连接已建立');
        setWebSocket(ws);
        setConnectionStatus('connected');
        isConnecting.current = false;
      };
      
      ws.onmessage = (event) => {
        try {
          // 检查数据类型和内容
          if (!event.data || typeof event.data !== 'string') {
            console.log('⚠️ 收到非字符串WebSocket数据:', typeof event.data);
            return;
          }

          // 检查是否是有效的JSON格式
          const messageData = event.data.trim();
          if (!messageData.startsWith('{') && !messageData.startsWith('[')) {
            console.log('⚠️ 收到非JSON格式数据:', messageData.substring(0, 100));
            return;
          }

          const data = JSON.parse(messageData);
          // 减少日志输出以提高性能
          // console.log('📡 收到WebSocket消息:', data);
          
          if (data && typeof data === 'object' && data.success !== undefined) {
            if (data.success) {
              const balls = data.detections?.soccer_balls || [];
              
              console.log('📡 WebSocket收到数据:', balls.length, '个足球');
              console.log('📡 manualGoalArea状态:', !!manualGoalArea, '长度:', manualGoalArea?.length);
              if (manualGoalArea) {
                console.log('📡 manualGoalArea详细内容:', manualGoalArea.map(p => `(${Math.round(p.x)}, ${Math.round(p.y)})`).join(', '));
              }
              
              // 简化检测日志，减少性能影响
              if (balls.length > 0) {
                // 只计算有效足球数量，不输出详细日志
                const validCount = balls.filter((ball: Detection) => {
                  if (!ball.bbox || ball.bbox.length < 4) return false;
                  const width = ball.bbox[2] - ball.bbox[0];
                  const height = ball.bbox[3] - ball.bbox[1];
                  const aspectRatio = width / height;
                  const area = width * height;
                  return ball.confidence > 0.15 && 
                         aspectRatio > 0.3 && aspectRatio < 3.0 && 
                         area > 100 && area < 100000 && 
                         width > 10 && height > 10;
                }).length;
                
                // 只在有有效足球时输出日志
                if (validCount > 0) {
                  console.log(`⚽ 检测到 ${validCount} 个足球`);
                }
              } else {
                // 没有检测到任何足球
                updateDetectionStatus(false, 0);
              }
              
              // 检查足球与手动标注球门的overlap
              let goalOverlapDetected = false;
              const validBalls = balls.filter((ball: Detection) => {
                if (!ball.bbox || ball.bbox.length < 4) return false;
                const width = ball.bbox[2] - ball.bbox[0];
                const height = ball.bbox[3] - ball.bbox[1];
                const aspectRatio = width / height;
                const area = width * height;
                return ball.confidence > 0.15 && 
                       aspectRatio > 0.3 && aspectRatio < 3.0 && 
                       area > 100 && area < 100000 && 
                       width > 10 && height > 10;
              });
              
              // 更新检测状态
              if (validBalls.length > 0) {
                const highestConfidence = Math.max(...validBalls.map((b: Detection) => b.confidence));
                updateDetectionStatus(true, highestConfidence);
                
                // 矩形overlap检测
                console.log('🔍 检查overlap条件 - manualGoalArea存在:', !!manualGoalArea, '长度:', manualGoalArea?.length);
                if (manualGoalArea && manualGoalArea.length === 4) {
                  console.log('🔍 条件满足，进入overlap检测逻辑');
                  
                  // 计算球门边界矩形
                  const goalBoundingRect = getBoundingRect(manualGoalArea);
                  console.log('🔍 球门边界矩形:', goalBoundingRect);
                  
                  const ball = validBalls[0];
                  console.log('🔍 检查第一个有效足球:', ball);
                  if (ball.bbox && ball.bbox.length >= 4) {
                    console.log('🔍 足球bbox有效，开始坐标计算');
                    const [x1, y1, x2, y2] = ball.bbox;
                    
                    // 坐标缩放计算
                    // —— 统一使用真实帧尺寸；若还未拿到则回退一个保守值 —— 
                    const srcW = frameSize?.w ?? 2048;
                    const srcH = frameSize?.h ?? 4032;

                    const tabBarHeight = 83;
                    const actualViewHeight = screenHeight - tabBarHeight;

                    const scaleX = screenWidth / srcW;
                    const scaleY = actualViewHeight / srcH;

                    // 解包 bbox，并兼容“0~1 归一化”或“基于其它输入尺寸”的情况
                    let [bx1, by1, bx2, by2] = ball.bbox;

                    // 如果后端是 0~1 归一化坐标，则放大到像素坐标
                    if (Math.max(bx1, by1, bx2, by2) <= 1.5) {
                      bx1 *= srcW;  by1 *= srcH;
                      bx2 *= srcW;  by2 *= srcH;
                    }

                    // 再把像素坐标缩放到当前屏幕坐标
                    const scaledX1 = bx1 * scaleX;
                    const scaledY1 = by1 * scaleY;
                    const scaledX2 = bx2 * scaleX;
                    const scaledY2 = by2 * scaleY;

                    
                    // 计算足球矩形在屏幕坐标系中的位置
                    const ballRect = {
                      x1: x1 * scaleX,
                      y1: y1 * scaleY,
                      x2: x2 * scaleX,
                      y2: y2 * scaleY
                    };
                    
                    // 执行矩形overlap检测
                    goalOverlapDetected = doRectanglesOverlap(ballRect, goalBoundingRect);
                    
                    console.log('🔍 Overlap检测结果:', goalOverlapDetected);
                    if (goalOverlapDetected) {
                      console.log('🥅⚽ 检测到进球overlap! 足球矩形与球门矩形重叠!');
                    }
                  }
                }
              } else {
                updateDetectionStatus(false, 0);
              }
              
              console.log('🔄 设置hasGoalOverlap状态为:', goalOverlapDetected);
              console.log('🔄 即将进行状态变化检查...');
              setHasGoalOverlap(goalOverlapDetected);
              
              const prev = overlapRef.current;

              if (goalOverlapDetected && !prev) {
                console.log('🎯 检测到新的重叠事件！准备触发录制...');
                overlapRef.current = true;       // 更新"上一帧重叠"标记

                // —— 开始录制视频（带冷却避免重复触发）——
                const now = Date.now();
                const timeSinceLastAlert = now - lastGoalAlertRef.current;
                console.log(`🎯 距离上次录制: ${timeSinceLastAlert}ms, isRecording: ${isRecording}`);
                
                if (timeSinceLastAlert > 3000 && !isRecording) {
                  console.log('🎬 满足录制条件，开始录制！');
                  lastGoalAlertRef.current = now;
                  startVideoRecording();
                } else {
                  console.log(`⏳ 冷却中或正在录制，跳过触发 (冷却剩余: ${3000 - timeSinceLastAlert}ms)`);
                }

                raiseLocalGoalBanner();          // 本地点亮 GOAL 横幅 1.5s（保留）
              } else if (!goalOverlapDetected && prev) {
                console.log('🎯 离开重叠区域');
                overlapRef.current = false;      // 离开重叠区，复位
              }

              
            // 立即更新状态，减少延迟
            setSoccerBalls(balls);
            if (data.is_goal_moment) setIsGoalMoment(true);
            } else {
              console.log('❌ 检测失败:', data.message || '未知错误');
            }
          } else {
            console.log('⚠️ 收到格式不正确的数据:', data);
          }
        } catch (error) {
          console.error('❌ 解析WebSocket数据失败:', error);
          console.log('原始数据前200字符:', event.data?.substring(0, 200));
          console.log('数据类型:', typeof event.data, '长度:', event.data?.length);
          
          // 如果连续解析失败，可能需要重连
          if ((error as Error).message?.includes('JSON Parse error')) {
            console.log('🔄 JSON解析错误，可能需要重连');
          }
        }
      };
      
      ws.onerror = (error) => {
        console.error('❌ WebSocket错误:', error);
        setConnectionStatus('error');
        setIsDetecting(false);
        
        // 显示详细错误信息
        setTimeout(() => {
          Alert.alert(
            '连接失败',
            `无法连接到服务器\n地址: ${API_BASE_URL}\n请确保后端服务正在运行`,
            [
              { text: '重试', onPress: reconnectWebSocket },
              { text: '取消', style: 'cancel' }
            ]
          );
        }, 1000);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket连接已关闭, 代码:', event.code, '原因:', event.reason);
        setWebSocket(null);
        setConnectionStatus('disconnected');
        setIsDetecting(false);
        isConnecting.current = false;
        
        // 如果不是主动关闭且页面仍在焦点，尝试重连
        if (event.code !== 1000 && isFocused) {
          setTimeout(() => {
            console.log('尝试重新连接...');
            connectWebSocket();
          }, 3000);
        }
      };
    } catch (error) {
      console.error('WebSocket连接失败:', error);
      setConnectionStatus('error');
      setIsDetecting(false);
      isConnecting.current = false;
    }
  };

  const disconnectWebSocket = () => {
    console.log('🔌 断开WebSocket连接');
    if (webSocket) {
      webSocket.close();
      setWebSocket(null);
    }
    setConnectionStatus('disconnected');
    setIsDetecting(false);
    // 清理检测结果
    setSoccerBalls([]);
  };

  /* ---------- 重新连接 ---------- */
  const reconnectWebSocket = () => {
    disconnectWebSocket();
    setTimeout(() => {
      connectWebSocket();
    }, 1000);
  };


  /* ---------- 发送帧到AI检测服务 ---------- */
  const sendFrameForDetection = () => {
    // 添加更严格的状态检查，标注模式时暂停检测
    if (!webSocket || !cameraRef.current || !aiEnabled || !isFocused || isAnnotatingGoal) {
      return;
    }

    // 检查WebSocket连接状态
    if (webSocket.readyState !== WebSocket.OPEN) {
      return;
    }
    
    console.log('📷 正在捕获相机帧...');
    
    // 使用异步处理，不阻塞定时器
    setTimeout(async () => {
      try {
        // 添加相机引用的有效性检查
        if (!cameraRef.current) {
          return;
        }
        
        const picture = await cameraRef.current.takePictureAsync({
          base64: true,
          quality: 0.05, // 极低质量，减少处理时间
          skipProcessing: true
          // 注意：Expo Camera没有mute参数，需要在应用设置中关闭声音
        });
        if (picture?.width && picture?.height) {
          setFrameSize({ w: picture.width, h: picture.height });
        }


        // 再次检查状态，因为拍照是异步操作
        if (!webSocket || webSocket.readyState !== WebSocket.OPEN) {
          return;
        }

        if (picture && picture.base64) {
          const frameData = {
            image: `data:image/jpeg;base64,${picture.base64}`,
            timestamp: Date.now()
          };
          
          // 异步发送，不阻塞UI
          webSocket.send(JSON.stringify(frameData));
        }
      } catch (error) {
        const errorMessage = (error as Error).message || String(error);
        
        if (errorMessage.includes('unmounted') || errorMessage.includes('Camera')) {
          setIsDetecting(false);
          return;
        }
        // 其他错误静默处理，避免日志spam
      }
    }, 0); // 立即异步执行，不阻塞当前线程
  };

  /* ---------- 定期发送帧进行检测 ---------- */
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    
    if (aiEnabled && webSocket && connectionStatus === 'connected' && isFocused && !isAnnotatingGoal) {
      if (!isDetecting) {
        setIsDetecting(true);
        console.log('🚀 开始实时检测，每1秒发送一帧');
      }
      
      // 调整帧间隔到1000ms，稳定检测频率
      interval = setInterval(() => {
        // 在发送前再次确认状态
        if (isFocused && webSocket && webSocket.readyState === WebSocket.OPEN && aiEnabled && cameraRef.current) {
          // 完全非阻塞调用，立即返回
          sendFrameForDetection();
        } else {
          setIsDetecting(false);
        }
      }, 1000);
    } else {
      if (isDetecting) {
        console.log('⏹️ 停止实时检测');
        setIsDetecting(false);
      }
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
        console.log('🧹 清理检测定时器');
      }
    };
  }, [aiEnabled, webSocket, connectionStatus, isFocused, isAnnotatingGoal]);

  /* ---------- 相机就绪 → 淡入 ---------- */
  const handleCameraReady = () => {
    console.log('📷 相机就绪回调触发！');
    
    // 延迟一点时间确保相机真正就绪
    setTimeout(() => {
      console.log('📷 相机确认就绪，可以开始录制');
      setIsCameraReady(true);
    }, 500);
    
    Animated.timing(camOpacity, {
      toValue: 1,
      duration: 250,
      useNativeDriver: true,
    }).start();
  };

  /* ---------- 权限处理 ---------- */
  if (!permission) {
    return (
      <View style={styles.container}>
        <Text style={styles.noPerm}>正在请求相机权限...</Text>
      </View>
    );
  }
  
  if (!permission.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.noPerm}>需要相机权限才能使用此功能</Text>
        <Pressable 
          style={styles.reconnectBtn} 
          onPress={requestPermission}
        >
          <Text style={styles.reconnectBtnText}>授权相机</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {isFocused && (
        /* 相机淡入包裹层 */
        <Animated.View style={[styles.cameraWrapper, { opacity: camOpacity }]}>
          <CameraView
            ref={cameraRef}
            style={StyleSheet.absoluteFill}
            facing="back"
            onCameraReady={handleCameraReady}
          />

          {/* —— AI检测结果可视化 —— */}
          <Svg style={StyleSheet.absoluteFill} pointerEvents="none">
            
            {/* 屏幕边界确定 - 考虑导航栏 */}
            {(() => {
              console.log('🔍 获取的屏幕尺寸: ', screenWidth, 'x', screenHeight);
              console.log('🔍 安全区域: top=', insets.top, 'bottom=', insets.bottom);
              console.log('🔍 soccerBalls数组:', soccerBalls);
              console.log('🔍 soccerBalls长度:', soccerBalls.length);
              
              // 计算实际相机视图区域（填满到导航栏边界）
              const tabBarHeight = 83; // React Navigation底部导航栏高度约83px
              const actualViewHeight = screenHeight - tabBarHeight;
              
              return (
                <G key="screen-boundary-detection">
                  {/* 屏幕边界标记 - 调整为实际相机视图区域 */}
                  
                  {/* 移除所有旧的边框线 */}
                  
                  {/* 四角L形标记 - 清洁的相机取景框，考虑safe area */}
                  {/* 左上角 L 形 */}
                  <Line x1={10} y1={insets.top + 10} x2={40} y2={insets.top + 10} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  <Line x1={10} y1={insets.top + 10} x2={10} y2={insets.top + 40} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  
                  {/* 右上角 L 形 */}
                  <Line x1={screenWidth - 40} y1={insets.top + 10} x2={screenWidth - 10} y2={insets.top + 10} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  <Line x1={screenWidth - 10} y1={insets.top + 10} x2={screenWidth - 10} y2={insets.top + 40} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  
                  {/* 左下角 L 形 */}
                  <Line x1={10} y1={actualViewHeight - 40} x2={10} y2={actualViewHeight - 10} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  <Line x1={10} y1={actualViewHeight - 10} x2={40} y2={actualViewHeight - 10} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  
                  {/* 右下角 L 形 */}
                  <Line x1={screenWidth - 10} y1={actualViewHeight - 40} x2={screenWidth - 10} y2={actualViewHeight - 10} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  <Line x1={screenWidth - 40} y1={actualViewHeight - 10} x2={screenWidth - 10} y2={actualViewHeight - 10} stroke="#ffffff" strokeWidth={2} opacity={0.8} />
                  
                  
                  {/* 绿色框跟踪足球位置 + overlap检测可视化 */}
                  {soccerBalls.length > 0 && (() => {
                    const ball = soccerBalls[0]; // 取第一个检测到的足球
                    
                    if (ball.bbox && ball.bbox.length >= 4) {
                      const [x1, y1, x2, y2] = ball.bbox;
                      
                      // 直接按照实际YOLO输入尺寸到屏幕尺寸的比例缩放
                      // 使用相机实际输出尺寸，由后端日志动态确定
                      // —— 统一使用真实帧尺寸；若还未拿到则回退一个保守值 —— 
                      const srcW = frameSize?.w ?? 2048;
                      const srcH = frameSize?.h ?? 4032;

                      const tabBarHeight = 83;
                      const actualViewHeight = screenHeight - tabBarHeight;

                      const scaleX = screenWidth / srcW;
                      const scaleY = actualViewHeight / srcH;

                      // 解包 bbox，并兼容“0~1 归一化”或“基于其它输入尺寸”的情况
                      let [bx1, by1, bx2, by2] = ball.bbox;

                      // 如果后端是 0~1 归一化坐标，则放大到像素坐标
                      if (Math.max(bx1, by1, bx2, by2) <= 1.5) {
                        bx1 *= srcW;  by1 *= srcH;
                        bx2 *= srcW;  by2 *= srcH;
                      }

                      // 再把像素坐标缩放到当前屏幕坐标
                      const scaledX1 = bx1 * scaleX;
                      const scaledY1 = by1 * scaleY;
                      const scaledX2 = bx2 * scaleX;
                      const scaledY2 = by2 * scaleY;

                      
                      
                      
                      return (
                        <G key="soccer-ball-detection">
                          {/* 足球检测框 */}
                          <Rect
                            x={scaledX1}
                            y={scaledY1}
                            width={scaledX2 - scaledX1}
                            height={scaledY2 - scaledY1}
                            stroke="#00FF00"
                            strokeWidth={3}
                            fill="transparent"
                            opacity={1.0}
                          />
                          
                          
                          {/* 如果有球门区域，显示overlap状态 */}
                          {manualGoalArea && manualGoalArea.length === 4 && (() => {
                            const goalBoundingRect = getBoundingRect(manualGoalArea);
                            const ballRect = {
                              x1: scaledX1,
                              y1: scaledY1,
                              x2: scaledX2,
                              y2: scaledY2
                            };
                            const isOverlapping = doRectanglesOverlap(ballRect, goalBoundingRect);
                            
                            return (
                              <SvgText
                                x={scaledX2 + 10}
                                y={scaledY1 + 30}
                                fontSize={14}
                                fill={isOverlapping ? "#FFA500" : "#FFFFFF"}
                                textAnchor="start"
                                fontWeight="bold"
                              >
                                {isOverlapping ? "重叠!" : "无重叠"}
                              </SvgText>
                            );
                          })()}
                          
                          {/* 四角坐标显示 - 优化布局防止重叠 */}
                          <SvgText
                            x={scaledX1 - 10}
                            y={scaledY1 - 8}
                            fontSize={10}
                            fill="#ffffff"
                            textAnchor="end"
                            fontWeight="bold"
                          >
                            {`${Math.round(scaledX1)}, ${Math.round(scaledY1)}`}
                          </SvgText>
                          <SvgText
                            x={scaledX2 + 10}
                            y={scaledY1 - 8}
                            fontSize={10}
                            fill="#ffffff"
                            textAnchor="start"
                            fontWeight="bold"
                          >
                            {`${Math.round(scaledX2)}, ${Math.round(scaledY1)}`}
                          </SvgText>
                          <SvgText
                            x={scaledX1 - 10}
                            y={scaledY2 + 18}
                            fontSize={10}
                            fill="#ffffff"
                            textAnchor="end"
                            fontWeight="bold"
                          >
                            {`${Math.round(scaledX1)}, ${Math.round(scaledY2)}`}
                          </SvgText>
                          <SvgText
                            x={scaledX2 + 10}
                            y={scaledY2 + 18}
                            fontSize={10}
                            fill="#ffffff"
                            textAnchor="start"
                            fontWeight="bold"
                          >
                            {`${Math.round(scaledX2)}, ${Math.round(scaledY2)}`}
                          </SvgText>
                        </G>
                      );
                    }
                    
                    return null;
                  })()}
                  
                  {/* 手动标注的球门显示 + 边界矩形可视化 */}
                  {manualGoalArea && manualGoalArea.length === 4 && (() => {
                    // 计算球门边界矩形 - 这是overlap检测使用的关键矩形！
                    const goalBoundingRect = getBoundingRect(manualGoalArea);
                    
                    return (
                      <G key="manual-goal-area">
                        {/* 球门区域多边形填充 */}
                        <Polygon
                          points={manualGoalArea.map(p => `${p.x},${p.y}`).join(' ')}
                          fill="rgba(0, 100, 200, 0.3)"
                          stroke="#0064C8"
                          strokeWidth={2}
                          opacity={0.8}
                        />
                        
                        {/* 球门边界矩形 - 这是overlap检测的关键矩形！*/}
                        <Rect
                          x={goalBoundingRect.x1}
                          y={goalBoundingRect.y1}
                          width={goalBoundingRect.x2 - goalBoundingRect.x1}
                          height={goalBoundingRect.y2 - goalBoundingRect.y1}
                          stroke="#FF4500"
                          strokeWidth={3}
                          fill="transparent"
                          opacity={1.0}
                          strokeDasharray="8,4"
                        />
                        
                        {/* 角点标记 */}
                        {manualGoalArea.map((point, index) => (
                          <G key={`goal-corner-${index}`}>
                            <Circle
                              cx={point.x}
                              cy={point.y}
                              r={8}
                              fill="#0064C8"
                              stroke="#ffffff"
                              strokeWidth={2}
                              opacity={1.0}
                            />
                            <SvgText
                              x={point.x}
                              y={point.y - 15}
                              fontSize={12}
                              fill="#87CEEB"
                              textAnchor="middle"
                              fontWeight="bold"
                            >
                              {`${Math.round(point.x)}, ${Math.round(point.y)}`}
                            </SvgText>
                          </G>
                        ))}
                      </G>
                    );
                  })()}
                  
                  {/* 标注过程中的临时角点显示 */}
                  {isAnnotatingGoal && goalCorners.map((point, index) => (
                    <G key={`temp-corner-${index}`}>
                      <Circle
                        cx={point.x}
                        cy={point.y}
                        r={6}
                        fill="#87CEEB"
                        stroke="#ffffff"
                        strokeWidth={2}
                        opacity={1.0}
                      />
                      <SvgText
                        x={point.x}
                        y={point.y - 15}
                        fontSize={12}
                        fill="#87CEEB"
                        textAnchor="middle"
                        fontWeight="bold"
                      >
                        {`${Math.round(point.x)}, ${Math.round(point.y)}`}
                      </SvgText>
                    </G>
                  ))}
                  
                </G>
              );
            })()}
            
          </Svg>

          {/* —— AI检测状态显示 —— */}
          {isGoalMoment && (
            <View style={styles.goalAlert}>
              <Text style={styles.goalAlertText}>⚽ 进球!</Text>
            </View>
          )}


          
          {/* —— 足球检测状态按钮 —— */}
          <View style={styles.detectionStatusButton}>
            <View style={[
              styles.statusIndicator,
              hasGoalOverlap ? styles.statusOrange : (detectionStatus.hasFootball ? styles.statusGreen : styles.statusRed)
            ]}>
              <Text style={styles.statusText}>
                {hasGoalOverlap 
                  ? '进球了！⚽🥅'
                  : (detectionStatus.hasFootball 
                    ? `⚽ 已识别到足球 ${(detectionStatus.confidence * 100).toFixed(1)}%`
                    : '⚽ 未识别到足球'
                  )
                }
              </Text>
            </View>
          </View>

          {/* —— 球门标注控制按钮 —— */}
          <View style={styles.goalAnnotationControls}>
            {!isAnnotatingGoal && !manualGoalArea && (
              <TouchableOpacity 
                style={[styles.statusIndicator, styles.goalAnnotationBtn]} 
                onPress={startGoalAnnotation}
              >
                <Text style={styles.statusText}>🥅 标注球门</Text>
              </TouchableOpacity>
            )}
            
            {isAnnotatingGoal && (
              <View style={[styles.statusIndicator, styles.goalAnnotationProgress]}>
                <Text style={styles.statusText}>
                  点击角点 ({goalCorners.length}/4) - 标注模式激活
                </Text>
                <TouchableOpacity 
                  style={styles.cancelAnnotationBtn} 
                  onPress={clearGoalAnnotation}
                >
                  <Text style={styles.cancelAnnotationText}>取消</Text>
                </TouchableOpacity>
              </View>
            )}
            
            {manualGoalArea && (
              <View style={styles.goalControlRow}>
                <TouchableOpacity 
                  style={[styles.statusIndicator, styles.goalClearBtn, styles.smallBtn]} 
                  onPress={clearGoalAnnotation}
                >
                  <Text style={styles.statusText}>清除球门</Text>
                </TouchableOpacity>
                
                {/* 临时添加手动录制按钮用于测试 */}
                {!isRecording && (
                  <TouchableOpacity 
                    style={[styles.statusIndicator, styles.testBtn, styles.smallBtn]} 
                    onPress={() => {
                      console.log('📹 手动触发录制测试');
                      startVideoRecording();
                    }}
                  >
                    <Text style={styles.statusText}>📹 测试录制</Text>
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>



          {/* —— 重新连接按钮 —— */}
          {connectionStatus === 'error' && (
            <TouchableOpacity 
              style={styles.reconnectBtn} 
              onPress={reconnectWebSocket}
            >
              <Text style={styles.reconnectBtnText}>🔄 重新连接</Text>
            </TouchableOpacity>
          )}

        </Animated.View>
      )}
      
      {/* 球门标注触摸层 - 移到外层避免覆盖其他UI */}
      {isAnnotatingGoal && isFocused && (
        <Pressable 
          style={[StyleSheet.absoluteFill, styles.annotationTouchLayer]} 
          onPress={handleGoalAnnotation}
        >
          <View style={StyleSheet.absoluteFill} />
        </Pressable>
      )}
      
      {/* —— 录制指示器 - 放在最顶层 —— */}
      {isRecording && isFocused && (
        <TouchableOpacity 
          style={styles.recordingIndicator}
          onPress={stopVideoRecording}
          activeOpacity={0.8}
        >
          <View style={styles.recordingDot} />
          <Text style={styles.recordingText}>REC</Text>
          <Text style={styles.recordingStopText}> (点击停止)</Text>
        </TouchableOpacity>
      )}

      {/* —— 大型红色圆形录制按钮 —— */}
      {isFocused && (
        <TouchableOpacity 
          style={[
            styles.mainRecordButton,
            isRecording && styles.mainRecordButtonRecording
          ]}
          onPress={isRecording ? stopVideoRecording : startVideoRecording}
          activeOpacity={0.8}
        >
          <View style={[
            styles.recordButtonInner,
            isRecording && styles.recordButtonInnerRecording
          ]} />
        </TouchableOpacity>
      )}
    </View>
  );
}

/* ---------- 样式 ---------- */
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  cameraWrapper: { flex: 1, backgroundColor: '#000' },
  noPerm: { flex: 1, textAlign: 'center', textAlignVertical: 'center', color: '#fff' },

  /* 进球提醒 */
  goalAlert: {
    position: 'absolute',
    top: '40%',
    alignSelf: 'center',
    backgroundColor: 'rgba(255, 0, 0, 0.9)',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 20,
    elevation: 10,
  },
  goalAlertText: {
    color: '#fff',
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
  },

  /* 检测信息面板 */
  detectionPanel: {
    position: 'absolute',
    top: 60,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  detectionText: {
    color: '#fff',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 5,
  },
  connectionStatus: {
    fontSize: 12,
    textAlign: 'center',
    color: '#ccc',
  },
  connectedStatus: {
    color: '#00ff00',
  },
  errorStatus: {
    color: '#ff4444',
  },
  debugInfo: {
    fontSize: 10,
    textAlign: 'center',
    color: '#888',
    marginTop: 2,
  },
  collisionInfo: {
    fontSize: 12,
    textAlign: 'center',
    color: '#ffaa00',
    marginTop: 3,
    fontWeight: 'bold',
  },
  annotationInfo: {
    fontSize: 12,
    textAlign: 'center',
    color: '#333',
    fontWeight: 'bold',
  },
  annotationModePanel: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginTop: 60,
    alignSelf: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  annotationProgress: {
    fontSize: 14,
    textAlign: 'center',
    color: '#333',
    fontWeight: 'bold',
    marginTop: 2,
  },
  /* 足球检测状态按钮 */
  detectionStatusButton: {
    position: 'absolute',
    top: 80,
    alignSelf: 'center',
  },
  statusIndicator: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
  statusGreen: {
    backgroundColor: 'rgba(0, 200, 0, 0.9)',
    borderColor: '#00cc00',
  },
  statusRed: {
    backgroundColor: 'rgba(200, 0, 0, 0.9)',
    borderColor: '#cc0000',
  },
  statusOrange: {
    backgroundColor: 'rgba(255, 165, 0, 0.9)',
    borderColor: '#ff8800',
  },
  statusText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  annotationOverlay: {
    backgroundColor: 'rgba(255, 255, 0, 0.05)',
  },
  detectingInfo: {
    fontSize: 11,
    textAlign: 'center',
    color: '#00ff88',
    marginTop: 2,
    fontWeight: 'bold',
  },

  /* 控制按钮组 */
  controlButtons: {
    position: 'absolute',
    bottom: 120,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  controlBtn: {
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    flex: 1,
    marginHorizontal: 5,
  },
  controlBtnActive: {
    backgroundColor: 'rgba(0, 150, 255, 0.8)',
    borderColor: '#0096ff',
  },
  controlBtnText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
  },
  controlBtnTextActive: {
    color: '#fff',
  },
  clearGoalBtn: {
    backgroundColor: 'rgba(255, 100, 100, 0.7)',
    borderColor: '#ff6666',
  },

  /* 重新连接按钮 */
  reconnectBtn: {
    position: 'absolute',
    bottom: 60,
    alignSelf: 'center',
    backgroundColor: 'rgba(255, 100, 100, 0.8)',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ff6666',
  },
  reconnectBtnText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },

  /* 检测成功消息 */
  detectionMessage: {
    position: 'absolute',
    top: 100,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(0, 200, 0, 0.9)',
    borderRadius: 12,
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderWidth: 2,
    borderColor: '#00ff00',
    shadowColor: '#00ff00',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.5,
    shadowRadius: 8,
    elevation: 5,
  },
  detectionMessageText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },

  /* 球门标注控制 */
  goalAnnotationControls: {
    position: 'absolute',
    bottom: 80,
    alignSelf: 'center',
  },
  goalAnnotationBtn: {
    backgroundColor: 'rgba(30, 144, 255, 0.9)',
    borderColor: '#1E90FF',
  },
  goalAnnotationProgress: {
    backgroundColor: 'rgba(30, 144, 255, 0.8)',
    borderColor: '#1E90FF',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 15,
  },
  goalClearBtn: {
    backgroundColor: 'rgba(100, 100, 100, 0.8)',
    borderColor: '#666666',
  },
  cancelAnnotationBtn: {
    backgroundColor: 'rgba(255, 100, 100, 0.8)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginLeft: 10,
  },
  cancelAnnotationText: {
    color: '#fff',
    fontSize: 10,
    fontWeight: 'bold',
  },
  annotationTouchLayer: {
    backgroundColor: 'transparent',
    zIndex: 1000,
  },
  goalControlRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  smallBtn: {
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  testBtn: {
    backgroundColor: 'rgba(255, 193, 7, 0.8)',
    borderColor: '#ffc107',
  },
  
  /* 录制指示器样式 */
  recordingIndicator: {
    position: 'absolute',
    top: 130, // 在导航栏上边一点
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#FF0000',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
  },
  recordingDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#FF0000',
    marginRight: 8,
  },
  recordingText: {
    color: '#FF0000',
    fontSize: 14,
    fontWeight: 'bold',
  },
  recordingStopText: {
    color: '#666',
    fontSize: 12,
    fontWeight: 'normal',
  },

  /* 大型录制按钮样式 */
  mainRecordButton: {
    position: 'absolute',
    bottom: 120, // 在底部导航栏上方
    alignSelf: 'center',
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#FF0000',
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    borderWidth: 3,
    borderColor: '#FFFFFF',
  },
  mainRecordButtonRecording: {
    backgroundColor: '#FF4444',
    borderColor: '#FFCCCC',
  },
  recordButtonInner: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
  },
  recordButtonInnerRecording: {
    width: 16,
    height: 16,
    borderRadius: 2, // 变成方形表示停止
    backgroundColor: '#FFFFFF',
  },

});
