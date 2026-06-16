/**
 * Face editor — configure and reorder the device's 5 faces.
 *
 * Fetches current prefs from GET /device/layout/prefs.
 * Saves to PUT /device/layout.
 * AI fills face content; this screen controls TYPE + ORDER only.
 */
import { useState, useEffect } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

const ALL_FACE_TYPES = [
  { key: 'goal_arc',      label: 'Goal Arc',        desc: 'Perimeter arc showing your goal progress %' },
  { key: 'task_list',     label: 'Task List',       desc: 'Up to 6 tasks with ring-style checkboxes' },
  { key: 'habit_heatmap', label: 'Habit Heatmap',   desc: '7-day completion grid for your habits' },
  { key: 'timer',         label: 'Timer',           desc: 'Depleting arc countdown for focus sessions' },
  { key: 'study_progress',label: 'Study Progress',  desc: 'Module completion arc with lesson counter' },
] as const;

type FaceKey = (typeof ALL_FACE_TYPES)[number]['key'];

export default function FacesScreen() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const [pinned, setPinned] = useState<FaceKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${API_BASE}/device/layout/prefs`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => {
        setPinned((data.face_types ?? []) as FaceKey[]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const toggle = (key: FaceKey) => {
    setPinned(prev => {
      if (prev.includes(key)) return prev.filter(k => k !== key);
      if (prev.length >= 5) {
        Alert.alert('Max 5 faces', 'Remove one before adding another.');
        return prev;
      }
      return [...prev, key];
    });
  };

  const moveUp = (i: number) => {
    if (i === 0) return;
    setPinned(prev => {
      const next = [...prev];
      [next[i - 1], next[i]] = [next[i], next[i - 1]];
      return next;
    });
  };

  const moveDown = (i: number) => {
    setPinned(prev => {
      if (i >= prev.length - 1) return prev;
      const next = [...prev];
      [next[i], next[i + 1]] = [next[i + 1], next[i]];
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_BASE}/device/layout`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ face_types: pinned }),
      });
      if (!res.ok) throw new Error('Save failed');
      router.back();
    } catch {
      Alert.alert('Error', 'Could not save. Try again.');
    } finally {
      setSaving(false);
    }
  };

  const resetToAI = async () => {
    setSaving(true);
    try {
      await fetch(`${API_BASE}/device/layout`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ face_types: [] }),
      });
      setPinned([]);
    } catch {}
    setSaving(false);
  };

  if (loading) {
    return (
      <View style={[styles.center, { backgroundColor: PAPER }]}>
        <ActivityIndicator color={INK} />
      </View>
    );
  }

  const unpinned = ALL_FACE_TYPES.filter(f => !pinned.includes(f.key));

  return (
    <View style={[styles.container, { backgroundColor: PAPER }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
          <Text style={[styles.back, { color: INK }]}>← BACK</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: INK }]}>FACE EDITOR</Text>
        <TouchableOpacity onPress={save} disabled={saving}>
          <Text style={[styles.saveBtn, { color: INK, opacity: saving ? 0.4 : 1 }]}>SAVE</Text>
        </TouchableOpacity>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {/* Active faces — ordered */}
        <Text style={[styles.sectionTitle, { color: INK }]}>ACTIVE ({pinned.length}/5)</Text>
        <Text style={[styles.sectionSub, { color: INK }]}>
          {pinned.length === 0 ? 'No faces pinned — AI picks automatically.' : 'AI fills content. Swipe order on device matches this list.'}
        </Text>

        {pinned.map((key, i) => {
          const meta = ALL_FACE_TYPES.find(f => f.key === key)!;
          return (
            <View key={key} style={[styles.faceRow, { borderColor: INK }]}>
              <View style={styles.faceInfo}>
                <Text style={[styles.faceNum, { color: INK }]}>{i + 1}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.faceLabel, { color: INK }]}>{meta.label}</Text>
                  <Text style={[styles.faceDesc, { color: INK }]}>{meta.desc}</Text>
                </View>
              </View>
              <View style={styles.faceActions}>
                <TouchableOpacity onPress={() => moveUp(i)} disabled={i === 0} style={styles.arrow}>
                  <Text style={[styles.arrowText, { color: INK, opacity: i === 0 ? 0.2 : 0.7 }]}>↑</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => moveDown(i)} disabled={i === pinned.length - 1} style={styles.arrow}>
                  <Text style={[styles.arrowText, { color: INK, opacity: i === pinned.length - 1 ? 0.2 : 0.7 }]}>↓</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => toggle(key)} style={styles.removeBtn}>
                  <Text style={[styles.removeText, { color: INK }]}>✕</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })}

        {/* Available to add */}
        {unpinned.length > 0 && (
          <>
            <Text style={[styles.sectionTitle, { color: INK, marginTop: 24 }]}>ADD FACE</Text>
            {unpinned.map(f => (
              <TouchableOpacity
                key={f.key}
                style={[styles.faceRow, { borderColor: 'rgba(20,19,13,0.2)' }]}
                onPress={() => toggle(f.key)}
                activeOpacity={0.7}
              >
                <View style={styles.faceInfo}>
                  <Text style={[styles.faceNum, { color: INK, opacity: 0.3 }]}>+</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={[styles.faceLabel, { color: INK }]}>{f.label}</Text>
                    <Text style={[styles.faceDesc, { color: INK }]}>{f.desc}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </>
        )}

        {/* Reset to AI */}
        {pinned.length > 0 && (
          <TouchableOpacity style={styles.resetBtn} onPress={resetToAI} disabled={saving}>
            <Text style={[styles.resetText, { color: INK }]}>RESET — LET AI DECIDE</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingTop: 60, paddingHorizontal: 20, paddingBottom: 16,
    borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.1)',
  },
  back: { fontSize: 11, letterSpacing: 1 },
  title: { fontSize: 11, letterSpacing: 3, fontWeight: '700' },
  saveBtn: { fontSize: 11, letterSpacing: 2, fontWeight: '700' },
  content: { padding: 20, paddingBottom: 60 },
  sectionTitle: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginBottom: 6 },
  sectionSub: { fontSize: 12, opacity: 0.45, marginBottom: 14 },
  faceRow: {
    borderWidth: 1, borderRadius: 2, padding: 14, marginBottom: 8,
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
  },
  faceInfo: { flexDirection: 'row', alignItems: 'center', flex: 1, marginRight: 8 },
  faceNum: { fontSize: 18, fontWeight: '700', marginRight: 12, width: 24, textAlign: 'center' },
  faceLabel: { fontSize: 14, fontWeight: '600', marginBottom: 2 },
  faceDesc: { fontSize: 11, opacity: 0.45 },
  faceActions: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  arrow: { padding: 6 },
  arrowText: { fontSize: 16, fontWeight: '600' },
  removeBtn: { padding: 6, marginLeft: 4 },
  removeText: { fontSize: 14 },
  resetBtn: {
    marginTop: 28, borderWidth: 1, borderColor: 'rgba(20,19,13,0.3)',
    paddingVertical: 12, alignItems: 'center', borderRadius: 2,
  },
  resetText: { fontSize: 11, letterSpacing: 2, opacity: 0.5 },
});
