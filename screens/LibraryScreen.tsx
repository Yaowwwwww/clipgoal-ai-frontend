// frontend/screens/LibraryScreen.tsx
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ImageBackground,
} from 'react-native';

/* ---------- 静态图片 ---------- */
const imgs = [
  require('../assets/highlight/basketball1.jpg'),
  require('../assets/highlight/basketball2.jpg'),
  require('../assets/highlight/basketball3.jpg'),
  require('../assets/highlight/basketball4.jpg'),
];

/* ---------- 数据 ---------- */
const DATA = imgs.map((img, i) => ({
  img,
  date: `06/${21 - i}/2024`,
  sport: 'Basketball',
}));

export default function LibraryScreen() {
  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      showsVerticalScrollIndicator={false}
    >
      <Text style={styles.title}>Library</Text>

      {DATA.map(({ img, date, sport }, idx) => (
        <View key={idx} style={styles.card}>
          <ImageBackground source={img} style={StyleSheet.absoluteFill} />
          <View style={styles.badge}>
            <Text style={styles.badgeText}>
              {date} • {sport}
            </Text>
          </View>
        </View>
      ))}
    </ScrollView>
  );
}

/* ---------- 样式 ---------- */
const CARD_H = 220;
const RADIUS = 28;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',        // ❶ 黑色背景
  },
  content: { paddingBottom: 80 },
  title: {
    fontSize: 34,
    fontWeight: '900',
    color: '#fff',                  // ❷ 标题白字
    marginTop: 48,
    marginBottom: 24,
    marginHorizontal: 24,
  },
  card: {
    height: CARD_H,
    marginHorizontal: 24,
    marginBottom: 32,
    borderRadius: RADIUS,
    overflow: 'hidden',
  },
  /* 徽章保持白底黑字，突出信息 */
  badge: {
    position: 'absolute',
    bottom: 15,
    alignSelf: 'center',
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 4,
    borderRadius: 999,
  },
  badgeText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
  },
});
