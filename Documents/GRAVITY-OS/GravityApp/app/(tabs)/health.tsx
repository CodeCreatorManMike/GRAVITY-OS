/**
 * Apple Health integration screen.
 *
 * Reads HealthKit data (steps, sleep, workouts) and syncs it to the backend.
 * Requires react-native-health — this works with EAS Build / bare workflow.
 * Run `npx expo prebuild` then build with Xcode or EAS Build.
 *
 * Setup: npx expo install react-native-health
 * Then add to app.json plugins:
 *   ["react-native-health", {
 *     "NSHealthShareUsageDescription": "Gravity reads your health data to support your goals.",
 *     "NSHealthUpdateUsageDescription": "Gravity does not write health data."
 *   }]
 */
import { useState, useEffect } from 'react';
import {
  View, Text, TouchableOpacity, StyleSheet, ScrollView,
  ActivityIndicator, Platform, Alert,
} from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

interface HealthSnapshot {
  date: string;
  steps: number;
  sleep_hours: number;
  sleep_quality: string;
  workout_minutes: number;
  workout_type: string;
  heart_rate_avg: number;
  calories_active: number;
  synced: boolean;
}

// Conditionally import react-native-health — gracefully handle missing native module
let AppleHealthKit: any = null;
let HealthKitPermissions: any = null;
try {
  const rnh = require('react-native-health');
  AppleHealthKit = rnh.default;
  HealthKitPermissions = rnh.HealthKitPermissions;
} catch {}

export default function HealthScreen() {
  const token = useAuthStore(s => s.token);
  const queryClient = useQueryClient();
  const [healthAvailable, setHealthAvailable] = useState(false);
  const [permissionsGranted, setPermissionsGranted] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Check if HealthKit native module is available
  useEffect(() => {
    if (Platform.OS === 'ios' && AppleHealthKit) {
      setHealthAvailable(true);
    }
  }, []);

  // Load today's synced health data from backend
  const { data: todayHealth, isLoading } = useQuery<HealthSnapshot | null>({
    queryKey: ['health_today'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/integrations/health/today`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return null;
      return res.json();
    },
    enabled: !!token,
  });

  const syncMutation = useMutation({
    mutationFn: async (data: Omit<HealthSnapshot, 'synced'>) => {
      const res = await fetch(`${API_BASE}/integrations/health/sync`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('Sync failed');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health_today'] });
    },
  });

  const requestPermissionsAndSync = async () => {
    if (!AppleHealthKit) {
      Alert.alert(
        'Native module required',
        'Apple Health requires a native build. Run "npx expo prebuild" then build with Xcode or EAS Build.',
      );
      return;
    }

    setSyncing(true);
    try {
      const permissions = {
        permissions: {
          read: [
            AppleHealthKit.Constants.Permissions.Steps,
            AppleHealthKit.Constants.Permissions.SleepAnalysis,
            AppleHealthKit.Constants.Permissions.ActiveEnergyBurned,
            AppleHealthKit.Constants.Permissions.HeartRate,
            AppleHealthKit.Constants.Permissions.Workout,
          ],
          write: [],
        },
      };

      // Request HealthKit permissions
      await new Promise<void>((resolve, reject) => {
        AppleHealthKit.initHealthKit(permissions, (err: Error) => {
          if (err) reject(err);
          else resolve();
        });
      });

      setPermissionsGranted(true);
      await syncHealthData();
    } catch (err) {
      Alert.alert('Health access denied', 'Please allow Health access in Settings to sync your data.');
    } finally {
      setSyncing(false);
    }
  };

  const syncHealthData = async () => {
    if (!AppleHealthKit) return;
    setSyncing(true);

    const today = new Date();
    const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const startOfYesterday = new Date(startOfDay);
    startOfYesterday.setDate(startOfYesterday.getDate() - 1);

    const dateStr = startOfDay.toISOString().split('T')[0];
    const yesterdayStr = startOfYesterday.toISOString().split('T')[0];

    try {
      // Read steps (today)
      const steps = await new Promise<number>((resolve) => {
        AppleHealthKit.getStepCount(
          { date: startOfDay.toISOString() },
          (_err: any, result: any) => resolve(result?.value ?? 0)
        );
      });

      // Read sleep (last night = yesterday 20:00 → today 12:00)
      const sleepData = await new Promise<{ hours: number; quality: string }>((resolve) => {
        const opts = {
          startDate: new Date(startOfYesterday.getTime() + 20 * 3600 * 1000).toISOString(),
          endDate: new Date(startOfDay.getTime() + 12 * 3600 * 1000).toISOString(),
        };
        AppleHealthKit.getSleepSamples(opts, (_err: any, results: any[]) => {
          if (!results || results.length === 0) {
            resolve({ hours: 0, quality: 'unknown' });
            return;
          }
          // Sum "asleep" samples
          const asleepMs = results
            .filter((s: any) => s.value === 'ASLEEP' || s.value === 'CORE' || s.value === 'DEEP' || s.value === 'REM')
            .reduce((acc: number, s: any) => {
              return acc + (new Date(s.endDate).getTime() - new Date(s.startDate).getTime());
            }, 0);
          const hours = asleepMs / (1000 * 3600);
          const quality = hours >= 7 ? 'good' : hours >= 5.5 ? 'fair' : 'poor';
          resolve({ hours: Math.round(hours * 10) / 10, quality });
        });
      });

      // Read active energy (today)
      const calories = await new Promise<number>((resolve) => {
        const opts = {
          startDate: startOfDay.toISOString(),
          endDate: today.toISOString(),
          unit: 'kilocalorie',
        };
        AppleHealthKit.getActiveEnergyBurned(opts, (_err: any, results: any[]) => {
          const total = (results ?? []).reduce((acc: number, r: any) => acc + (r.value ?? 0), 0);
          resolve(Math.round(total));
        });
      });

      // Read heart rate avg (today)
      const hrAvg = await new Promise<number>((resolve) => {
        const opts = {
          startDate: startOfDay.toISOString(),
          endDate: today.toISOString(),
          ascending: false,
          limit: 100,
        };
        AppleHealthKit.getHeartRateSamples(opts, (_err: any, results: any[]) => {
          if (!results || results.length === 0) { resolve(0); return; }
          const avg = results.reduce((acc: number, r: any) => acc + (r.value ?? 0), 0) / results.length;
          resolve(Math.round(avg));
        });
      });

      // Sync to backend (today's data)
      await syncMutation.mutateAsync({
        date: dateStr,
        steps,
        sleep_hours: sleepData.hours,
        sleep_quality: sleepData.quality,
        workout_minutes: 0,  // workout parsing is complex — Phase 2
        workout_type: '',
        heart_rate_avg: hrAvg,
        calories_active: calories,
      });

    } catch (err) {
      Alert.alert('Sync error', 'Some health data could not be read.');
    } finally {
      setSyncing(false);
    }
  };

  const renderStat = (label: string, value: string) => (
    <View style={styles.statRow} key={label}>
      <Text style={[styles.statLabel, { color: INK }]}>{label}</Text>
      <Text style={[styles.statValue, { color: INK }]}>{value}</Text>
    </View>
  );

  return (
    <ScrollView style={[styles.container, { backgroundColor: PAPER }]} contentContainerStyle={styles.content}>
      <Text style={[styles.header, { color: INK }]}>HEALTH</Text>

      {/* Connection status */}
      <View style={[styles.section, { borderColor: INK }]}>
        <Text style={[styles.sectionTitle, { color: INK }]}>APPLE HEALTH</Text>
        <Text style={[styles.sectionStatus, { color: INK }]}>
          {!healthAvailable
            ? 'Not available — requires native build'
            : todayHealth
            ? 'Connected — synced today'
            : 'Not synced today'}
        </Text>
        <TouchableOpacity
          style={[styles.btn, { backgroundColor: INK, opacity: syncing ? 0.5 : 1 }]}
          onPress={permissionsGranted ? syncHealthData : requestPermissionsAndSync}
          disabled={syncing}
        >
          {syncing
            ? <ActivityIndicator color={PAPER} />
            : <Text style={{ color: PAPER, fontWeight: '600', letterSpacing: 1, fontSize: 13 }}>
                {permissionsGranted ? 'SYNC NOW' : 'CONNECT APPLE HEALTH'}
              </Text>
          }
        </TouchableOpacity>
      </View>

      {/* Today's data */}
      {isLoading ? (
        <ActivityIndicator color={INK} style={{ marginTop: 32 }} />
      ) : todayHealth ? (
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: INK }]}>TODAY</Text>
          {renderStat('Steps', todayHealth.steps.toLocaleString())}
          {renderStat('Sleep last night', todayHealth.sleep_hours > 0 ? `${todayHealth.sleep_hours}h (${todayHealth.sleep_quality})` : '—')}
          {renderStat('Active calories', todayHealth.calories_active > 0 ? `${todayHealth.calories_active} kcal` : '—')}
          {renderStat('Avg heart rate', todayHealth.heart_rate_avg > 0 ? `${todayHealth.heart_rate_avg} bpm` : '—')}
        </View>
      ) : (
        <View style={styles.emptyState}>
          <Text style={[styles.emptyText, { color: INK }]}>
            Connect Apple Health to track your steps, sleep, and workouts alongside your goals.
          </Text>
        </View>
      )}

      {/* Phase 2 integrations — coming soon */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: INK }]}>COMING SOON</Text>
        {['Apple Calendar', 'Workouts detail', 'Screen Time'].map(name => (
          <View style={styles.comingSoonRow} key={name}>
            <Text style={[styles.comingSoonLabel, { color: INK }]}>{name}</Text>
            <Text style={[styles.comingSoonBadge, { color: INK }]}>PHASE 2</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { paddingBottom: 60 },
  header: { paddingTop: 60, paddingHorizontal: 20, paddingBottom: 24, fontSize: 12, letterSpacing: 3, fontWeight: '700' },
  section: { marginHorizontal: 20, marginBottom: 20, borderTopWidth: 1, paddingTop: 16 },
  sectionTitle: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginBottom: 12 },
  sectionStatus: { fontSize: 13, opacity: 0.6, marginBottom: 16 },
  btn: { paddingVertical: 14, alignItems: 'center', borderRadius: 2 },
  statRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.06)' },
  statLabel: { fontSize: 13, opacity: 0.6 },
  statValue: { fontSize: 13, fontWeight: '600' },
  emptyState: { marginHorizontal: 20, marginTop: 8, marginBottom: 20 },
  emptyText: { fontSize: 14, lineHeight: 22, opacity: 0.5 },
  comingSoonRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.06)' },
  comingSoonLabel: { fontSize: 13, opacity: 0.5 },
  comingSoonBadge: { fontSize: 9, letterSpacing: 1.5, opacity: 0.35 },
});
