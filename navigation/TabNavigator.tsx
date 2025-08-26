import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';  // 1. 导入图标库

import HomeScreen from '../screens/HomeScreen';
import RecordScreen from '../screens/RecordScreen';
import LibraryScreen from '../screens/LibraryScreen';

const Tab = createBottomTabNavigator();

export default function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#000',  // 黑色背景
          borderTopColor: '#fff',   // 顶部分隔白线
          borderTopWidth: 0.5,
        },
        tabBarActiveTintColor: 'white',
        tabBarInactiveTintColor: 'gray',
        // 2. 根据路由动态渲染不同图标
        tabBarIcon: ({ color, size, focused }) => {
          let iconName: string;

          if (route.name === 'Home') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'Record') {
            iconName = focused ? 'camera' : 'camera-outline';
          } else if (route.name === 'Library') {
            iconName = focused ? 'book' : 'book-outline';
          } else {
            iconName = 'ellipse';
          }

          return <Ionicons name={iconName as any} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Record" component={RecordScreen} />
      <Tab.Screen name="Library" component={LibraryScreen} />
    </Tab.Navigator>
  );
}
