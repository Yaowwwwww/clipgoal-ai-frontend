import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  Image,
  TouchableOpacity,
  ScrollView,
} from 'react-native';

/* ---------- 数据 ---------- */
type SportItem = { name: string; image: any; likes: string };
type Highlight  = { date: string; image: any; sport: string };

const goalOriented: SportItem[] = [
  { name: 'Soccer',     image: require('../assets/sports/Soccer.png'),     likes: '4.91K' },
  { name: 'Basketball', image: require('../assets/sports/Basketball.jpg'), likes: '3.87K' },
  { name: 'Hockey',     image: require('../assets/sports/Hockey.png'),     likes: '1.80K' },
];

const groundOriented: SportItem[] = [
  { name: 'Badminton',  image: require('../assets/sports/Badminton.png'),  likes: '2.99K' },
  { name: 'Volleyball', image: require('../assets/sports/Volleyball.png'), likes: '3.12K' },
  { name: 'Tennis',     image: require('../assets/sports/Tennis.png'),     likes: '2.30K' },
];

const highlights: Highlight[] = [
  { date: '06/21/2024', image: require('../assets/highlight/basketball1.jpg'), sport: 'Basketball' },
  { date: '06/21/2024', image: require('../assets/highlight/basketball2.jpg'), sport: 'Basketball' },
  { date: '06/21/2024', image: require('../assets/highlight/basketball3.jpg'), sport: 'Basketball' },
  { date: '06/21/2024', image: require('../assets/highlight/basketball4.jpg'), sport: 'Basketball' },
];

/* ---------- 组件 ---------- */
export default function HomeScreen() {
  /* 点击回调（此处仅打印，可替换为导航） */
  const handleSelectSport = (sport: string) => console.log('Sport:', sport);
  const handleSelectHL    = (item: Highlight) => console.log('Highlight:', item);

  /* 通用卡片渲染 -------- */
  const renderSportCard = ({ item }: { item: SportItem }) => (
    <TouchableOpacity style={styles.card} onPress={() => handleSelectSport(item.name)}>
      <Image source={item.image} style={styles.cardImg} resizeMode="cover" />
      <View style={styles.cardFooter}>
        <Text style={styles.cardName}>{item.name}</Text>
        <View style={styles.cardLikes}>
          <Text style={styles.heart}>♡</Text>
          <Text style={styles.likesTxt}>{item.likes}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const renderHighlight = ({ item }: { item: Highlight }) => (
    <TouchableOpacity style={styles.hlCard} onPress={() => handleSelectHL(item)}>
      <Image source={item.image} style={styles.hlImg} resizeMode="cover" />
      <View style={styles.hlBadge}>
        <Text style={styles.hlBadgeTxt}>{item.date} · {item.sport}</Text>
      </View>
    </TouchableOpacity>
  );

  /* ---------------------- */
  return (
    <View style={styles.container}>
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* 头部标题 */}
        <Text style={styles.pageTitle}>Home</Text>

        {/* ---- Goal Oriented ---- */}
        <Text style={styles.sectionTitle}>Goal Orientated</Text>
        <FlatList
          data={goalOriented}
          horizontal
          renderItem={renderSportCard}
          keyExtractor={i => i.name}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.rowList}
        />

        {/* ---- Court Oriented ---- */}
        <Text style={styles.sectionTitle}>Court Orientated</Text>
        <FlatList
          data={groundOriented}
          horizontal
          renderItem={renderSportCard}
          keyExtractor={i => i.name}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.rowList}
        />

        {/* ---- Highlights ---- */}
        <Text style={styles.sectionTitle}>Recent Highlights</Text>
        <FlatList
          data={highlights}
          horizontal
          renderItem={renderHighlight}
          keyExtractor={(_, idx) => String(idx)}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.hlList}
        />
      </ScrollView>
    </View>
  );
}

/* ---------- 样式 ---------- */
const CARD_W = 160;
const CARD_H = 180;
const HL_W   = 260;
const HL_H   = 150;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },

  pageTitle: {
    color: '#fff',
    fontSize: 35,
    fontWeight: '900',
    marginTop: 45,
    marginBottom: 19,
    marginLeft: 16,
  },

  sectionTitle: {
    color: '#fff',
    fontSize: 30,
    fontWeight: '700',
    marginTop: 4,
    marginBottom: 8,
    marginLeft: 16,
  },

  /* 横滑行外层 padding */
  rowList: { paddingLeft: 16, paddingBottom: 8 },

  /* —— 运动卡片 —— */
  card: {
    width: CARD_W,
    height: CARD_H,
    marginRight: 16,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#111',
  },
  cardImg: { width: '100%', height: 120 },
  cardFooter: {
    flex: 1,
    backgroundColor: '#111',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 10,
  },
  cardName:  { color: '#fff', fontWeight: '600', fontSize: 14 },
  cardLikes: { flexDirection: 'row', alignItems: 'center' },
  heart:     { color: '#fff', fontSize: 13, marginRight: 4 },
  likesTxt:  { color: '#fff', fontSize: 13 },

  /* —— Highlight —— */
  hlList: { paddingLeft: 16, paddingBottom: 32 },
  hlCard: {
    width: HL_W,
    height: HL_H,
    borderRadius: 20,
    overflow: 'hidden',
    marginRight: 20,
  },
  hlImg: { width: '100%', height: '100%' },
  hlBadge: {
    position: 'absolute',
    bottom: 8,
    left: 8,
    backgroundColor: '#fff',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 999,
  },
  hlBadgeTxt: { color: '#000', fontWeight: '600', fontSize: 12 },
});
