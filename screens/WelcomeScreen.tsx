// screens/WelcomeScreen.tsx
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ImageBackground,
  TouchableOpacity,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../App';

const BG = require('../assets/bg.jpg');

type Props = NativeStackScreenProps<RootStackParamList, 'Welcome'>;

export default function WelcomeScreen({ navigation }: Props) {
  const goNext = () => navigation.replace('Main');   // 直接进入主应用

  return (
    <ImageBackground
      source={BG}
      style={styles.bg}
      imageStyle={{ opacity: 0.75 }}
    >
      {/* 主欢迎卡片 */}
      <View style={styles.card}>
        <Text style={styles.h1}>
          Welcome to{'\n'}ClipGoal-AI
        </Text>

        <Text style={styles.desc}>
          An innovative AI app aimed at helping{'\n'}
          amateurs and sports hobbyists{'\n'}
          autonomously film and clip{'\n'}
          in-game highlights.
        </Text>

        <TouchableOpacity style={styles.btn} onPress={goNext}>
          <Text style={styles.btnTxt}>Get Started</Text>
        </TouchableOpacity>
      </View>
    </ImageBackground>
  );
}

/* ---------------- 样式 ---------------- */
const styles = StyleSheet.create({
  bg:   { flex: 1, justifyContent: 'center', backgroundColor: '#000' },
  card: {
    marginHorizontal: '9%',
    backgroundColor: '#fff',
    borderRadius: 22,
    paddingVertical: 44,
    paddingHorizontal: 26,
    elevation: 8,
  },
  h1: {
    fontSize: 30,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 20,
    lineHeight: 38,
  },
  desc: {
    fontSize: 15,
    lineHeight: 22,
    color: '#555',
    textAlign: 'center',
    marginBottom: 32,
  },
  btn: {
    alignSelf: 'center',
    backgroundColor: '#000',
    paddingVertical: 14,
    paddingHorizontal: 46,
    borderRadius: 999,
  },
  btnTxt: { color: '#fff', fontSize: 18, fontWeight: '600' },
});
