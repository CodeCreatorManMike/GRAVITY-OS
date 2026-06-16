import { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Switch, Alert } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

interface NudgeSettings {
  quiet_hours_start: string;
  quiet_hours_end: string;
  rest_days: string[];
  sensitivity_habit: number;
  sensitivity_focus: number;
  sensitivity_fitness: number;
  sensitivity_sleep: number;
  sensitivity_spending: number;
}

interface IntegrationStatus {
  name: string;
  connected: boolean;
  last_sync: string | null;
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const SENSITIVITY_LABELS: Record<string, string> = {
  sensitivity_habit: 'Habit nudges',
  sensitivity_focus: 'Focus nudges',
  sensitivity_fitness: 'Fitness nudges',
  sensitivity_sleep: 'Sleep nudges',
};

export default function SettingsScreen() {
  const token = useAuthStore(s => s.token);
  const clearAuth = useAuthStore(s => s.clearAuth);
  const router = useRouter();
  const queryClient = useQueryClient();

  const { data: nudgeSettings } = useQuery<NudgeSettings>({
    queryKey: ['nudge_settings'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/nudges/settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    enabled: !!token,
  });

  const { data: integrations } = useQuery<IntegrationStatus[]>({
    queryKey: ['integration_status'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/integrations/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed');
      return res.json();
    },
    enabled: !!token,
  });

  const updateSettingsMutation = useMutation({
    mutationFn: async (patch: Partial<NudgeSettings>) => {
      const res = await fetch(`${API_BASE}/nudges/settings`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      if (!res.ok) throw new Error('Update failed');
      return res.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['nudge_settings'] }),
  });

  const toggleRestDay = (day: string) => {
    if (!nudgeSettings) return;
    const current = nudgeSettings.rest_days ?? [];
    const updated = current.includes(day)
      ? current.filter(d => d !== day)
      : [...current, day];
    updateSettingsMutation.mutate({ rest_days: updated });
  };

  const handleLogout = () => {
    Alert.alert('Log out', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: async () => {
        await clearAuth();
        router.replace('/login');
      }},
    ]);
  };

  const integrationDisplayName: Record<string, string> = {
    apple_health: 'Apple Health',
    apple_calendar: 'Apple Calendar',
    google_calendar: 'Google Calendar',
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: PAPER }]} contentContainerStyle={styles.content}>
      <Text style={[styles.header, { color: INK }]}>SETTINGS</Text>

      {/* Integrations */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: INK }]}>INTEGRATIONS</Text>
        {(integrations ?? []).map(integration => (
          <View style={styles.row} key={integration.name}>
            <View style={styles.rowLeft}>
              <Text style={[styles.rowLabel, { color: INK }]}>
                {integrationDisplayName[integration.name] ?? integration.name}
              </Text>
              {integration.last_sync && (
                <Text style={[styles.rowSub, { color: INK }]}>
                  Last sync {new Date(integration.last_sync).toLocaleDateString()}
                </Text>
              )}
            </View>
            <View style={[styles.badge, { borderColor: INK, backgroundColor: integration.connected ? INK : 'transparent' }]}>
              <Text style={{ color: integration.connected ? PAPER : INK, fontSize: 9, letterSpacing: 1 }}>
                {integration.connected ? 'ON' : 'OFF'}
              </Text>
            </View>
          </View>
        ))}
      </View>

      {/* Nudge settings */}
      {nudgeSettings && (
        <>
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: INK }]}>QUIET HOURS</Text>
            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: INK }]}>From</Text>
              <Text style={[styles.rowValue, { color: INK }]}>{nudgeSettings.quiet_hours_start}</Text>
            </View>
            <View style={styles.row}>
              <Text style={[styles.rowLabel, { color: INK }]}>To</Text>
              <Text style={[styles.rowValue, { color: INK }]}>{nudgeSettings.quiet_hours_end}</Text>
            </View>
          </View>

          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: INK }]}>REST DAYS</Text>
            {DAYS.map(day => (
              <TouchableOpacity
                key={day}
                style={styles.row}
                onPress={() => toggleRestDay(day)}
                activeOpacity={0.7}
              >
                <Text style={[styles.rowLabel, { color: INK }]}>{day}</Text>
                <View style={[
                  styles.badge,
                  {
                    borderColor: INK,
                    backgroundColor: (nudgeSettings.rest_days ?? []).includes(day) ? INK : 'transparent',
                  },
                ]}>
                  <Text style={{
                    color: (nudgeSettings.rest_days ?? []).includes(day) ? PAPER : INK,
                    fontSize: 9, letterSpacing: 1,
                  }}>
                    {(nudgeSettings.rest_days ?? []).includes(day) ? 'REST' : '—'}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: INK }]}>NUDGE SENSITIVITY</Text>
            <Text style={[styles.sectionSub, { color: INK }]}>
              Toggle to pause a nudge category
            </Text>
            {Object.entries(SENSITIVITY_LABELS).map(([key, label]) => {
              const val = nudgeSettings[key as keyof NudgeSettings] as number;
              const isOn = val > 0;
              return (
                <View style={styles.row} key={key}>
                  <Text style={[styles.rowLabel, { color: INK }]}>{label}</Text>
                  <Switch
                    value={isOn}
                    onValueChange={(on) => updateSettingsMutation.mutate({ [key]: on ? 1.0 : 0.0 })}
                    trackColor={{ false: 'rgba(20,19,13,0.1)', true: INK }}
                    thumbColor={PAPER}
                  />
                </View>
              );
            })}
          </View>
        </>
      )}

      {/* Device */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: INK }]}>DEVICE</Text>
        <TouchableOpacity style={styles.row} onPress={() => router.push('/faces' as any)} activeOpacity={0.7}>
          <Text style={[styles.rowLabel, { color: INK }]}>Face editor</Text>
          <Text style={[styles.rowValue, { color: INK, opacity: 0.4 }]}>→</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.row} onPress={() => router.push('/files' as any)} activeOpacity={0.7}>
          <Text style={[styles.rowLabel, { color: INK }]}>Files</Text>
          <Text style={[styles.rowValue, { color: INK, opacity: 0.4 }]}>→</Text>
        </TouchableOpacity>
      </View>

      {/* Log out */}
      <View style={styles.section}>
        <TouchableOpacity style={[styles.logoutBtn, { borderColor: INK }]} onPress={handleLogout}>
          <Text style={{ color: INK, fontWeight: '600', letterSpacing: 1, fontSize: 13 }}>LOG OUT</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { paddingBottom: 60 },
  header: { paddingTop: 60, paddingHorizontal: 20, paddingBottom: 24, fontSize: 12, letterSpacing: 3, fontWeight: '700' },
  section: { marginHorizontal: 20, marginBottom: 24, borderTopWidth: 1, borderTopColor: 'rgba(20,19,13,0.12)', paddingTop: 16 },
  sectionTitle: { fontSize: 10, letterSpacing: 2, fontWeight: '600', marginBottom: 12 },
  sectionSub: { fontSize: 12, opacity: 0.45, marginBottom: 8, marginTop: -4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 11, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.05)' },
  rowLeft: { flex: 1 },
  rowLabel: { fontSize: 14 },
  rowSub: { fontSize: 11, opacity: 0.4, marginTop: 2 },
  rowValue: { fontSize: 14, fontWeight: '600' },
  badge: { borderWidth: 1, borderRadius: 2, paddingHorizontal: 8, paddingVertical: 4 },
  logoutBtn: { borderWidth: 1, paddingVertical: 14, alignItems: 'center', borderRadius: 2 },
});
