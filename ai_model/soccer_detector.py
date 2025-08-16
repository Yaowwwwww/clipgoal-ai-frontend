"""
足球检测模型 - 基于YOLOv11
专门用于检测足球和方形球门
"""

import torch
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Dict, Tuple, Optional
import json
import time


class SoccerDetector:
    """
    足球检测器 - 检测足球和球门
    """
    
    def __init__(self, model_path: str = 'yolo11s.pt'):
        """
        初始化足球检测器
        
        Args:
            model_path: YOLO模型路径
        """
        self.model = YOLO(model_path)
        
        # COCO数据集扩展类别映射 - 识别所有球类
        self.ball_classes = {
            0: 'person',           # 人（球员、裁判）
            32: 'sports ball',     # 主要运动球类
            # 扩展的球类检测类别
            37: 'frisbee',         # 飞盘（圆形物体）
            # 增加更多可能的球类目标
        }
        
        # 检测置信度阈值 - 适配iOS视频和小足球
        self.confidence_threshold = 0.3  # 适合iOS视频的置信度
        self.iou_threshold = 0.4  # 降低IoU阈值
        
        # 球门检测参数
        self.goal_detection_history = []
        self.goal_stable_frames = 5
        
        # 各种球类颜色范围（HSV）- 支持更多球类
        self.ball_colors = {
            'white': ([0, 0, 180], [180, 40, 255]),      # 白色球类
            'black': ([0, 0, 0], [180, 255, 80]),        # 黑色球类
            'orange': ([5, 80, 80], [25, 255, 255]),     # 橙色球类
            'red': ([160, 120, 120], [180, 255, 255]),   # 红色球类
            'blue': ([100, 120, 120], [130, 255, 255]), # 蓝色球类
            'green': ([40, 120, 120], [80, 255, 255]),   # 绿色球类
            'yellow': ([20, 120, 120], [40, 255, 255]),  # 黄色球类
            'purple': ([130, 120, 120], [160, 255, 255]) # 紫色球类
        }
        
    def detect_ball_by_color(self, frame: np.ndarray) -> List[Dict]:
        """
        基于颜色检测各种运动球类
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        balls = []
        
        # 检测各种颜色的球类
        for color_name, (lower, upper) in self.ball_colors.items():
            if color_name in ['white', 'black']:
                lower = np.array(lower)
                upper = np.array(upper)
                mask = cv2.inRange(hsv, lower, upper)
                
                # 形态学操作去噪
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                
                # 检测圆形轮廓
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 100 < area < 8000:  # 扩大足球大小范围
                        # 检查圆度
                        perimeter = cv2.arcLength(contour, True)
                        if perimeter > 0:
                            circularity = 4 * np.pi * area / (perimeter * perimeter)
                            if circularity > 0.4:  # 降低圆度要求
                                x, y, w, h = cv2.boundingRect(contour)
                                aspect_ratio = w / h
                                if 0.5 < aspect_ratio < 2.0:  # 放宽宽高比要求
                                    balls.append({
                                        'bbox': [int(x), int(y), int(x + w), int(y + h)],
                                        'confidence': float(circularity),
                                        'class_name': f'{color_name}_ball',
                                        'center': [float(x + w/2), float(y + h/2)],
                                        'detection_method': f'color_{color_name}'
                                    })
        
        return balls

    def detect_goal_advanced(self, frame: np.ndarray) -> List[Dict]:
        """
        先进的球门检测算法 - 支持任意角度和颜色（实时优化版）
        """
        goals = []
        
        # 方法1: 改进的边缘+直线检测（快速版）
        goals.extend(self._detect_goal_by_edges_fast(frame))
        
        # 方法2: 轮廓检测法（简化版）
        goals.extend(self._detect_goal_by_contours_fast(frame))
        
        # 去重和筛选
        return self._filter_goal_detections(goals)
    
    def _detect_goal_by_edges(self, frame: np.ndarray) -> List[Dict]:
        """使用边缘检测找球门"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        goals = []
        
        # 多尺度边缘检测
        for low_threshold in [30, 50, 80]:
            for high_threshold in [low_threshold * 2, low_threshold * 3]:
                edges = cv2.Canny(gray, low_threshold, high_threshold)
                
                # 霍夫直线检测 - 更灵敏的参数
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, 
                                       minLineLength=30, maxLineGap=15)
                
                if lines is not None:
                    goal_rects = self._analyze_lines_for_rectangles(lines, frame.shape)
                    for rect in goal_rects:
                        goals.append({
                            'bbox': rect['bbox'],
                            'confidence': rect['confidence'],
                            'class_name': 'goal',
                            'center': rect['center'],
                            'detection_method': 'edge_lines',
                            'corners': rect.get('corners', [])
                        })
        return goals
    
    def _detect_goal_by_contours(self, frame: np.ndarray) -> List[Dict]:
        """使用轮廓检测找球门"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        goals = []
        
        # 多种预处理方式
        for blur_size in [3, 5, 7]:
            blurred = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
            
            # 自适应阈值
            for block_size in [11, 15, 21]:
                thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                             cv2.THRESH_BINARY, block_size, 2)
                
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if 1000 < area < 50000:  # 球门大小范围
                        # 多边形拟合
                        epsilon = 0.02 * cv2.arcLength(contour, True)
                        approx = cv2.approxPolyDP(contour, epsilon, True)
                        
                        if len(approx) >= 4:  # 至少4个点
                            x, y, w, h = cv2.boundingRect(contour)
                            aspect_ratio = w / h
                            
                            if 0.5 < aspect_ratio < 4.0:  # 球门宽高比范围
                                goals.append({
                                    'bbox': [x, y, x + w, y + h],
                                    'confidence': min(0.9, area / 10000),
                                    'class_name': 'goal',
                                    'center': [x + w/2, y + h/2],
                                    'detection_method': 'contour',
                                    'corners': approx.reshape(-1, 2).tolist()
                                })
        return goals
    
    def _detect_goal_by_corners(self, frame: np.ndarray) -> List[Dict]:
        """使用角点检测找球门"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        goals = []
        
        # Harris角点检测
        corners = cv2.goodFeaturesToTrack(gray, 100, 0.01, 10)
        
        if corners is not None:
            corners = corners.astype(int)
            # 尝试从角点组合中找到矩形结构
            goal_rects = self._find_rectangles_from_corners(corners, frame.shape)
            for rect in goal_rects:
                goals.append({
                    'bbox': rect['bbox'],
                    'confidence': rect['confidence'],
                    'class_name': 'goal',
                    'center': rect['center'],
                    'detection_method': 'corners',
                    'corners': rect['corners']
                })
        
        return goals
    
    def _analyze_lines_for_rectangles(self, lines, frame_shape) -> List[Dict]:
        """从直线中分析出矩形结构"""
        rectangles = []
        
        # 分类直线为垂直和水平线
        vertical_lines = []
        horizontal_lines = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            
            if abs(angle) < 15 or abs(angle) > 165:  # 水平线
                horizontal_lines.append(((x1, y1, x2, y2), length))
            elif 75 < abs(angle) < 105:  # 垂直线
                vertical_lines.append(((x1, y1, x2, y2), length))
        
        # 尝试组合垂直和水平线形成矩形
        for v_line, v_len in vertical_lines:
            for h_line, h_len in horizontal_lines:
                if v_len > 30 and h_len > 30:  # 足够长的线段
                    rect = self._try_form_rectangle(v_line, h_line, frame_shape)
                    if rect:
                        rectangles.append(rect)
        
        return rectangles
    
    def _try_form_rectangle(self, v_line, h_line, frame_shape):
        """尝试从垂直线和水平线形成矩形"""
        # 简化的矩形识别逻辑
        vx1, vy1, vx2, vy2 = v_line
        hx1, hy1, hx2, hy2 = h_line
        
        # 计算可能的矩形区域
        x_coords = [vx1, vx2, hx1, hx2]
        y_coords = [vy1, vy2, hy1, hy2]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # 验证矩形是否合理
        if 50 < width < frame_shape[1] * 0.8 and 30 < height < frame_shape[0] * 0.8:
            return {
                'bbox': [int(min_x), int(min_y), int(max_x), int(max_y)],
                'confidence': 0.7,
                'center': [float((min_x + max_x) / 2), float((min_y + max_y) / 2)],
                'corners': [[int(min_x), int(min_y)], [int(max_x), int(min_y)], 
                           [int(max_x), int(max_y)], [int(min_x), int(max_y)]]
            }
        return None
    
    def _find_rectangles_from_corners(self, corners, frame_shape) -> List[Dict]:
        """从角点中寻找矩形结构"""
        rectangles = []
        
        # 简化实现：寻找4个角点组成的矩形
        if len(corners) >= 4:
            # 选取距离合适的4个点
            for i in range(len(corners) - 3):
                for j in range(i + 1, len(corners) - 2):
                    for k in range(j + 1, len(corners) - 1):
                        for l in range(k + 1, len(corners)):
                            pts = [corners[i][0], corners[j][0], corners[k][0], corners[l][0]]
                            rect = self._check_four_points_rectangle(pts, frame_shape)
                            if rect:
                                rectangles.append(rect)
        
        return rectangles
    
    def _check_four_points_rectangle(self, points, frame_shape):
        """检查4个点是否能形成合理的矩形"""
        # 简化的矩形验证
        if len(points) != 4:
            return None
        
        # 计算边界框
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        width = max_x - min_x
        height = max_y - min_y
        
        # 验证尺寸合理性
        if 50 < width < frame_shape[1] * 0.8 and 30 < height < frame_shape[0] * 0.8:
            return {
                'bbox': [int(min_x), int(min_y), int(max_x), int(max_y)],
                'confidence': 0.6,
                'center': [float((min_x + max_x) / 2), float((min_y + max_y) / 2)],
                'corners': [[int(p[0]), int(p[1])] for p in points]
            }
        return None
    
    def _filter_goal_detections(self, goals) -> List[Dict]:
        """过滤和去重球门检测结果"""
        if not goals:
            return []
        
        # 按置信度排序
        goals.sort(key=lambda x: x['confidence'], reverse=True)
        
        # 去重：移除重叠度过高的检测
        filtered = []
        for goal in goals:
            is_duplicate = False
            for existing in filtered:
                if self._calculate_overlap(goal['bbox'], existing['bbox']) > 0.5:
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered.append(goal)
        
        return filtered[:3]  # 最多返回3个球门
    
    def _calculate_overlap(self, bbox1, bbox2) -> float:
        """计算两个边界框的重叠度"""
        x1_1, y1_1, x2_1, y2_1 = bbox1
        x1_2, y1_2, x2_2, y2_2 = bbox2
        
        # 计算交集
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i <= x1_i or y2_i <= y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        
        union = area1 + area2 - intersection
        return intersection / union if union > 0 else 0.0
    
    def _detect_goal_by_edges_fast(self, frame: np.ndarray) -> List[Dict]:
        """快速边缘检测球门"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        goals = []
        
        # 只使用一组参数进行检测以提高速度
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=80, 
                               minLineLength=50, maxLineGap=20)
        
        if lines is not None:
            goal_rects = self._analyze_lines_for_rectangles(lines, frame.shape)
            for rect in goal_rects:
                goals.append({
                    'bbox': rect['bbox'],
                    'confidence': rect['confidence'],
                    'class_name': 'goal',
                    'center': rect['center'],
                    'detection_method': 'edge_lines_fast',
                    'corners': rect.get('corners', [])
                })
        return goals
    
    def _detect_goal_by_contours_fast(self, frame: np.ndarray) -> List[Dict]:
        """快速轮廓检测球门"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        goals = []
        
        # 只使用一组预处理参数
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 15, 2)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if 1000 < area < 50000:  # 球门大小范围
                # 多边形拟合
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) >= 4:  # 至少4个点
                    x, y, w, h = cv2.boundingRect(contour)
                    aspect_ratio = w / h
                    
                    if 0.8 < aspect_ratio < 3.0:  # 球门宽高比范围
                        goals.append({
                            'bbox': [int(x), int(y), int(x + w), int(y + h)],
                            'confidence': float(min(0.8, area / 15000)),
                            'class_name': 'goal',
                            'center': [float(x + w/2), float(y + h/2)],
                            'detection_method': 'contour_fast',
                            'corners': [[int(point[0]), int(point[1])] for point in approx.reshape(-1, 2)]
                        })
                        break  # 只取第一个满足条件的
        return goals

    def detect_objects(self, frame: np.ndarray) -> Dict:
        """
        只检测足球，不检测球门
        """
        # 只使用YOLO检测足球
        yolo_results = self._yolo_detect(frame)
        
        # 彻底禁用所有球门检测
        # 只检测足球，并严格限制为1个
        all_balls = self._filter_duplicate_balls(yolo_results['soccer_balls'])
        all_goals = []  # 完全不检测球门
        
        return {
            'detections': yolo_results['detections'],
            'soccer_balls': all_balls,
            'goal_areas': all_goals,
            'frame_shape': frame.shape
        }

    def _yolo_detect(self, frame: np.ndarray) -> Dict:
        """
        使用YOLO进行基础检测
        """
        results = self.model.predict(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        detections = []
        soccer_balls = []
        goal_areas = []
        
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()
                
                for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                    x1, y1, x2, y2 = box
                    class_id = int(cls)
                    
                    detection = {
                        'bbox': [float(x1), float(y1), float(x2), float(y2)],
                        'confidence': float(conf),
                        'class_id': int(class_id),
                        'class_name': self.ball_classes.get(class_id, f'class_{class_id}'),
                        'center': [float((x1 + x2) / 2), float((y1 + y2) / 2)],
                        'detection_method': 'yolo'
                    }
                    
                    detections.append(detection)
                    
                    # 检测运动球类，适配iOS视频中的小足球
                    if class_id == 32 and conf > 0.3:  # 适配iOS视频的置信度要求
                        # 验证边界框的合理性
                        box_width = x2 - x1
                        box_height = y2 - y1
                        aspect_ratio = box_width / box_height
                        box_area = box_width * box_height
                        
                        # 放宽足球检测条件以适配iOS视频
                        if (0.5 < aspect_ratio < 2.5 and      # 放宽宽高比要求
                            300 < box_area < 10000 and        # 适配小足球面积
                            box_width > 15 and box_height > 15):  # 降低最小尺寸
                            soccer_balls.append(detection)
        
        return {
            'detections': detections,
            'soccer_balls': soccer_balls,
            'goal_areas': goal_areas
        }
    
    def detect_rectangular_goal(self, goal_posts: List[Dict]) -> Optional[Dict]:
        """
        基于球门柱检测方形球门区域
        
        Args:
            goal_posts: 检测到的球门柱列表
            
        Returns:
            球门区域信息或None
        """
        if len(goal_posts) < 2:
            return None
        
        # 按X坐标排序球门柱
        goal_posts_sorted = sorted(goal_posts, key=lambda x: x['center'][0])
        
        # 取最左和最右的球门柱
        left_post = goal_posts_sorted[0]
        right_post = goal_posts_sorted[-1]
        
        # 计算球门区域
        left_x = left_post['bbox'][0]
        right_x = right_post['bbox'][2]
        top_y = min(left_post['bbox'][1], right_post['bbox'][1])
        bottom_y = max(left_post['bbox'][3], right_post['bbox'][3])
        
        # 扩展球门区域（包含横梁）
        goal_width = right_x - left_x
        goal_height = bottom_y - top_y
        
        # 假设横梁在顶部
        crossbar_y = top_y - goal_height * 0.1  # 横梁位置
        
        goal_area = {
            'bbox': [left_x, crossbar_y, right_x, bottom_y],
            'width': goal_width,
            'height': goal_height + (top_y - crossbar_y),
            'posts': [left_post, right_post],
            'center': [(left_x + right_x) / 2, (crossbar_y + bottom_y) / 2],
            'confidence': min(left_post['confidence'], right_post['confidence'])
        }
        
        return goal_area
    
    def calculate_ball_trajectory(self, ball_history: List[Dict]) -> Optional[Dict]:
        """
        计算足球轨迹
        
        Args:
            ball_history: 球的历史位置
            
        Returns:
            轨迹信息
        """
        if len(ball_history) < 3:
            return None
        
        # 提取球心坐标
        positions = np.array([ball['center'] for ball in ball_history])
        times = np.array([ball.get('timestamp', i) for i, ball in enumerate(ball_history)])
        
        # 计算速度和加速度
        velocities = np.diff(positions, axis=0) / np.diff(times).reshape(-1, 1)
        
        if len(velocities) > 1:
            accelerations = np.diff(velocities, axis=0) / np.diff(times[1:]).reshape(-1, 1)
        else:
            accelerations = np.array([[0, 0]])
        
        return {
            'positions': positions.tolist(),
            'velocities': velocities.tolist(),
            'accelerations': accelerations.tolist(),
            'speed': np.linalg.norm(velocities[-1]) if len(velocities) > 0 else 0
        }
    
    def check_ball_goal_collision(self, soccer_balls: List[Dict], goal_areas: List[Dict]) -> Dict:
        """
        检测足球与球门的碰撞 - 修复版
        
        Args:
            soccer_balls: 检测到的足球列表
            goal_areas: 球门区域列表
            
        Returns:
            碰撞检测结果
        """
        collision_info = {
            'has_collision': False,
            'collision_type': None,
            'ball_info': None,
            'goal_info': None,
            'distance': float('inf')
        }
        
        # 严格检查：必须同时有球和球门才能检测碰撞
        if not soccer_balls or not goal_areas:
            return collision_info
            
        # 最终验证：只接受极高置信度的结果
        valid_balls = [ball for ball in soccer_balls if ball['confidence'] > 0.95]  # 极高置信度要求
        valid_goals = []  # 不检测球门
        
        if not valid_balls or not valid_goals:
            return collision_info
        
        min_distance = float('inf')
        best_ball = None
        best_goal = None
        collision_type = None
        
        for ball in valid_balls:
            ball_x, ball_y = ball['center']
            ball_bbox = ball['bbox']
            
            for goal in valid_goals:
                goal_bbox = goal['bbox']
                goal_center_x, goal_center_y = goal['center']
                
                # 1. 检查球是否在球门内（进球）
                if (goal_bbox[0] <= ball_x <= goal_bbox[2] and 
                    goal_bbox[1] <= ball_y <= goal_bbox[3]):
                    return {
                        'has_collision': True,
                        'collision_type': 'goal_scored',
                        'ball_info': ball,
                        'goal_info': goal,
                        'distance': 0
                    }
                
                # 2. 检查球是否与球门边框碰撞 - 更严格的判断
                # 计算球心到球门边框的最短距离
                closest_x = max(goal_bbox[0], min(ball_x, goal_bbox[2]))
                closest_y = max(goal_bbox[1], min(ball_y, goal_bbox[3]))
                
                distance = np.sqrt((ball_x - closest_x)**2 + (ball_y - closest_y)**2)
                
                # 球的半径估算
                ball_radius = max(ball_bbox[2] - ball_bbox[0], ball_bbox[3] - ball_bbox[1]) / 2
                
                # 更严格的碰撞阈值：只有非常近的距离才认为碰撞
                collision_threshold = max(5, ball_radius * 0.3)  # 更严格的阈值
                
                if distance <= collision_threshold and distance < min_distance:
                    min_distance = distance
                    best_ball = ball
                    best_goal = goal
                    collision_type = 'goal_contact'
        
        # 只有在非常近的距离才认为碰撞
        if best_ball and best_goal and min_distance < 20:  # 最大允许距离20像素
            collision_info = {
                'has_collision': True,
                'collision_type': collision_type,
                'ball_info': best_ball,
                'goal_info': best_goal,
                'distance': min_distance
            }
        
        return collision_info
    
    def _filter_duplicate_balls(self, balls: List[Dict]) -> List[Dict]:
        """
        筛选球类，适配iOS视频中的小足球
        """
        if not balls:
            return []
        
        # 适配iOS视频的球类验证
        valid_balls = []
        for ball in balls:
            bbox = ball['bbox']
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            area = width * height
            aspect_ratio = width / height
            confidence = ball['confidence']
            
            # 适配iOS视频的验证条件
            if (confidence > 0.3 and                   # 适配iOS视频的置信度
                0.5 < aspect_ratio < 2.5 and          # 放宽宽高比
                300 < area < 10000 and                # 适配小足球面积
                width > 15 and height > 15 and        # 降低最小尺寸
                width < 300 and height < 300):        # 防止过大的检测框
                valid_balls.append(ball)
        
        if not valid_balls:
            return balls  # 如果没有通过验证的，返回原始检测结果
        
        # 按置信度排序，返回前3个最好的结果
        valid_balls.sort(key=lambda x: x['confidence'], reverse=True)
        return valid_balls[:3]

    def is_goal_scoring_moment(self, soccer_balls: List[Dict], goal_areas: List[Dict]) -> bool:
        """
        判断是否为进球/碰撞时刻
        """
        collision = self.check_ball_goal_collision(soccer_balls, goal_areas)
        return collision['has_collision']
    
    def process_frame(self, frame: np.ndarray, ball_history: List[Dict] = None, 
                     frame_buffer: List[Dict] = None) -> Dict:
        """
        处理单帧图像（禁用碰撞检测和精彩片段）
        
        Args:
            frame: 输入帧
            ball_history: 球的历史位置
            frame_buffer: 帧缓冲区（保留但不使用）
            
        Returns:
            处理结果
        """
        if ball_history is None:
            ball_history = []
        if frame_buffer is None:
            frame_buffer = []
        
        current_time = time.time()
        
        # 简化版本：不再维护帧缓冲区（因为不需要精彩片段）
        # frame_buffer.append({
        #     'frame': frame.copy(),
        #     'timestamp': current_time
        # })
        # 
        # # 保持10秒的帧缓冲（假设30fps）
        # max_buffer_size = 300  # 10秒 * 30fps
        # if len(frame_buffer) > max_buffer_size:
        #     frame_buffer.pop(0)
        
        # 检测物体（只检测球类）
        detection_result = self.detect_objects(frame)
        
        # 更新球的历史位置
        current_balls = detection_result['soccer_balls']
        if current_balls:
            # 选择置信度最高的球
            best_ball = max(current_balls, key=lambda x: x['confidence'])
            best_ball['timestamp'] = current_time
            ball_history.append(best_ball)
            
            # 保持历史记录长度
            if len(ball_history) > 30:  # 保留更多历史用于轨迹分析
                ball_history.pop(0)
        
        # 计算轨迹
        trajectory = self.calculate_ball_trajectory(ball_history)
        
        # 禁用碰撞检测 - 用户不需要进球检测
        # collision_info = self.check_ball_goal_collision(
        #     detection_result['soccer_balls'], 
        #     detection_result['goal_areas']
        # )
        collision_info = {
            'has_collision': False,
            'collision_type': None,
            'ball_info': None,
            'goal_info': None,
            'distance': float('inf')
        }
        
        # 禁用精彩片段保存 - 用户不需要自动片段
        # clip_info = None
        # if collision_info['has_collision']:
        #     # 提取过去10秒的片段
        #     ten_seconds_ago = current_time - 10.0
        #     clip_frames = [f for f in frame_buffer if f['timestamp'] >= ten_seconds_ago]
        #     
        #     if len(clip_frames) > 0:
        #         clip_info = {
        #             'collision_type': collision_info['collision_type'],
        #             'start_time': clip_frames[0]['timestamp'],
        #             'end_time': current_time,
        #             'frame_count': len(clip_frames),
        #             'ball_info': collision_info['ball_info'],
        #             'goal_info': collision_info['goal_info']
        #         }
        clip_info = None  # 不再生成精彩片段
        
        return {
            'detections': detection_result,
            'collision_info': collision_info,
            'trajectory': trajectory,
            'is_goal_moment': False,  # 不再检测进球时刻
            'ball_history': ball_history,
            'frame_buffer': frame_buffer,  # 保留结构但不使用
            'clip_info': clip_info,
            'timestamp': current_time
        }
    
    def draw_detections(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """
        在帧上绘制检测结果
        """
        output_frame = frame.copy()
        
        # 绘制足球
        if 'detections' in result and 'soccer_balls' in result['detections']:
            for ball in result['detections']['soccer_balls']:
                bbox = ball['bbox']
                confidence = ball['confidence']
                method = ball.get('detection_method', 'unknown')
                
                # 根据检测方法选择颜色
                if method.startswith('color'):
                    color = (0, 255, 255)  # 黄色 - 颜色检测
                else:
                    color = (0, 255, 0)    # 绿色 - YOLO检测
                
                # 绘制边框
                cv2.rectangle(output_frame, 
                             (int(bbox[0]), int(bbox[1])), 
                             (int(bbox[2]), int(bbox[3])), 
                             color, 3)
                
                # 绘制中心点
                center = ball['center']
                cv2.circle(output_frame, 
                          (int(center[0]), int(center[1])), 
                          8, color, -1)
                
                # 添加标签
                label = f"Ball {confidence:.2f} ({method})"
                cv2.putText(output_frame, label, 
                           (int(bbox[0]), int(bbox[1]) - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 绘制球门区域
        if 'detections' in result and 'goal_areas' in result['detections']:
            for goal in result['detections']['goal_areas']:
                bbox = goal['bbox']
                confidence = goal['confidence']
                method = goal.get('detection_method', 'unknown')
                
                # 球门用红色
                color = (0, 0, 255)
                
                # 绘制边框
                cv2.rectangle(output_frame, 
                             (int(bbox[0]), int(bbox[1])), 
                             (int(bbox[2]), int(bbox[3])), 
                             color, 4)
                
                # 添加半透明填充
                overlay = output_frame.copy()
                cv2.rectangle(overlay, 
                             (int(bbox[0]), int(bbox[1])), 
                             (int(bbox[2]), int(bbox[3])), 
                             color, -1)
                cv2.addWeighted(output_frame, 0.85, overlay, 0.15, 0, output_frame)
                
                # 添加标签
                label = f"Goal {confidence:.2f} ({method})"
                cv2.putText(output_frame, label, 
                           (int(bbox[0]), int(bbox[1]) - 15), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # 绘制轨迹
        if result.get('trajectory') and len(result['trajectory'].get('positions', [])) > 1:
            positions = result['trajectory']['positions']
            for i in range(len(positions) - 1):
                pt1 = (int(positions[i][0]), int(positions[i][1]))
                pt2 = (int(positions[i+1][0]), int(positions[i+1][1]))
                cv2.line(output_frame, pt1, pt2, (255, 255, 0), 2)
        
        # 碰撞信息显示
        if result.get('collision_info') and result['collision_info']['has_collision']:
            collision_type = result['collision_info']['collision_type']
            if collision_type == 'goal_scored':
                text = "GOAL SCORED!"
                color = (0, 0, 255)
            else:
                text = "COLLISION!"
                color = (0, 165, 255)
            
            cv2.putText(output_frame, text, 
                       (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
        
        # 添加检测统计
        stats_y = frame.shape[0] - 60
        ball_count = len(result.get('detections', {}).get('soccer_balls', []))
        goal_count = len(result.get('detections', {}).get('goal_areas', []))
        
        cv2.putText(output_frame, f"Balls: {ball_count}", 
                   (10, stats_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(output_frame, f"Goals: {goal_count}", 
                   (10, stats_y + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return output_frame


def create_soccer_training_data():
    """
    创建足球检测训练数据配置
    """
    config = {
        'path': './soccer_dataset',
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': 6,
        'names': [
            'soccer_ball',
            'player', 
            'goal_post',
            'goal_area',
            'referee',
            'field_lines'
        ]
    }
    
    with open('./soccer_data.yaml', 'w') as f:
        import yaml
        yaml.dump(config, f)
    
    return './soccer_data.yaml'


if __name__ == "__main__":
    # 测试代码
    detector = SoccerDetector()
    
    # 模拟测试
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detector.process_frame(test_frame)
    
    print("检测结果:")
    print(f"足球数量: {len(result['detections']['soccer_balls'])}")
    print(f"球门检测: {result['goal_area'] is not None}")
    print(f"进球时刻: {result['is_goal_moment']}")