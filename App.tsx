// App.tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

/* --------- 你的页面 / 导航 --------- */
import WelcomeScreen  from './screens/WelcomeScreen';   // << 确认路径大小写！
import TabNavigator   from './navigation/TabNavigator'; // << 你的底部 Tab

/* --------- 类型定义（可选但推荐） --------- */
export type RootStackParamList = {
  /** 首屏欢迎页（无参数） */
  Welcome: undefined;
  /** 主应用 — 承载底部 Tab 的那一层（同样无参数） */
  Main: undefined;

  // ➜ 如果以后还想加“选运动”等向导页，直接在这里追加：
  // SelectSport: undefined;
};

/* --------- 创建原生栈 --------- */
const Stack = createNativeStackNavigator<RootStackParamList>();

/* --------- 根组件 --------- */
export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName="Welcome"
        screenOptions={{ headerShown: false }}  // 全局隐藏原生标题栏
      >
        <Stack.Screen name="Welcome" component={WelcomeScreen} />
        <Stack.Screen name="Main"    component={TabNavigator} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
