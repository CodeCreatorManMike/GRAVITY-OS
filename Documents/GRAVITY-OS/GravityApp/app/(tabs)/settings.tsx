import type { ReactNode } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Switch, Alert } from 'react-native';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';
import { useAuthStore } from '../../store/authStore';
import { API_BASE } from '../../constants/api';
import { BG, SURFACE, SURFACE2, WHITE, DIM, FAINT, BORDER, T } from '../../constants/theme';

interface NudgeSettings {
  quiet_hours_start: string;
  quiet_hours_end: string;
  rest_days: string[];
  sensitivity_habit: number;
  sensitivity_focus: number;
  sensitivity_fitness: number;
  sensitivity_sleep: number;
}

interface IntegrationStatus {
  name: string;
  connected: boolean;
  last_sync: string | null;
}

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const NUDGE_LABELS: Record<string, string> = {
  sensitivity_habit:   'Habit nudges',
  sensitivity_focus:   'Focus nudges',
  sensitivity_fitness: 'Fitness nudges',
  sensitivity_sleep:   'Sleep nudges',
};
const INTEGRATION_NAMES: Record<string, string> = {
  apple_health:    'Apple Health',
  apple_calendar:  'Apple Calendar',
  google_calendar: 'Google Calendar',
};

export default function SettingsScreen() {
  const token       = useAuthStore(s => s.token);
  const name        = useAuthStore(s => s.name);
  const clearAuth   = useAuthStore(s => s.clearAuth);
  const router      = useRouter();
  const queryClient = useQueryClient();

  const { data: nudge } = useQuery<NudgeSettings>({
    queryKey: ['nudge_settings'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/nudges/settings`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
  });

  const { data: integrations } = useQuery<IntegrationStatus[]>({
    queryKey: ['integration_status'],
    queryFn: async () => {
      const r = await fetch(`${API_BASE}/integrations/status`, { headers: { Authorization: `Bearer ${token}` } });
      if (!r.ok) throw new Error();
      return r.json();
    },
    enabled: !!token,
  });

  const updateNudge = useMutation({
    mutationFn: async (patch: Partial<NudgeSettings>) => {
      const r = await fetch(`${API_BASE}/nudges/settings`, {
        method: 'PUT',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      });
      if (!r.ok) throw new Error();
      return r.json();
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['nudge_settings'] }),
  });

  const toggleRestDay = (day: string) => {
    if (!nudge) return;
    const current = nudge.rest_days ?? [];
    const updated = current.includes(day) ? current.filter(d => d !== day) : [...current, day];
    updateNudge.mutate({ rest_days: updated });
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

  return (
    <ScrollView style={s.container} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={s.header}>
        <Text style={s.heading}>Settings</Text>
        {name && <Text style={s.userName}>{name}</Text>}
      </View>

      {/* Device card */}
      <View style={s.deviceCard}>
        <View style={s.deviceLeft}>
          <Text style={s.deviceLabel}>GRAVITY DEVICE</Text>
          <Text style={s.deviceSub}>Round display · ESP32-S3</Text>
        </View>
        <View style={s.deviceDot} />
      </View>

      {/* Device section */}
      <Section title="DEVICE">
        <Row label="Face editor" onPress={() => router.push('/faces' as any)} arrow />
        <Row label="Files"       onPress={() => router.push('/files' as any)} arrow />
      </Section>

      {/* Integrations */}
      {(integrations?.length ?? 0) > 0 && (
        <Section title="INTEGRATIONS">
          {(integrations ?? []).map(i => (
            <View key={i.name} style={s.row}>
              <View style={{ flex: 1 }}>
                <Text style={s.rowLabel}>{INTEGRATION_NAMES[i.name] ?? i.name}</Text>
                {i.last_sync && (
                  <Text style={s.rowSub}>Synced {new Date(i.last_sync).toLocaleDateString()}</Text>
                )}
              </View>
              <View style={[s.badge, i.connected && s.badgeOn]}>
                <Text style={[s.badgeText, i.connected && s.badgeTextOn]}>
                  {i.connected ? 'ON' : 'OFF'}
                </Text>
              </View>
            </View>
          ))}
        </Section>
      )}

      {/* Quiet hours */}
      {nudge && (
        <>
          <Section title="QUIET HOURS">
            <View style={s.row}>
              <Text style={s.rowLabel}>From</Text>
              <Text style={s.rowValue}>{nudge.quiet_hours_start}</Text>
            </View>
            <View style={s.row}>
              <Text style={s.rowLabel}>To</Text>
              <Text style={s.rowValue}>{nudge.quiet_hours_end}</Text>
            </View>
          </Section>

          <Section title="REST DAYS">
            {DAYS.map(day => (
              <TouchableOpacity key={day} style={s.row} onPress={() => toggleRestDay(day)} activeOpacity={0.7}>
                <Text style={s.rowLabel}>{day}</Text>
                <View style={[s.badge, (nudge.rest_days ?? []).includes(day) && s.badgeOn]}>
                  <Text style={[s.badgeText, (nudge.rest_days ?? []).includes(day) && s.badgeTextOn]}>
                    {(nudge.rest_days ?? []).includes(day) ? 'REST' : '—'}
                  </Text>
                </View>
              </TouchableOpacity>
            ))}
          </Section>

          <Section title="NUDGE SENSITIVITY">
            {Object.entries(NUDGE_LABELS).map(([key, label]) => {
              const val = nudge[key as keyof NudgeSettings] as number;
              return (
                <View key={key} style={s.row}>
                  <Text style={s.rowLabel}>{label}</Text>
                  <Switch
                    value={val > 0}
                    onValueChange={on => updateNudge.mutate({ [key]: on ? 1.0 : 0.0 })}
                    trackColor={{ false: FAINT, true: WHITE }}
                    thumbColor={BG}
                    ios_backgroundColor={FAINT}
                  />
                </View>
              );
            })}
          </Section>
        </>
      )}

      {/* Log out */}
      <View style={{ paddingHorizontal: 20, paddingTop: 8 }}>
        <TouchableOpacity style={s.logoutBtn} onPress={handleLogout}>
          <Text style={s.logoutText}>LOG OUT</Text>
        </TouchableOpacity>
      </View>

      <View style={{ height: 48 }} />
    </ScrollView>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <View style={s.section}>
      <Text style={s.sectionTitle}>{title}</Text>
      <View style={s.sectionBody}>{children}</View>
    </View>
  );
}

function Row({ label, onPress, arrow }: { label: string; onPress?: () => void; arrow?: boolean }) {
  return (
    <TouchableOpacity style={s.row} onPress={onPress} activeOpacity={0.7}>
      <Text style={s.rowLabel}>{label}</Text>
      {arrow && <Text style={s.arrow}>›</Text>}
    </TouchableOpacity>
  );
}

const s = StyleSheet.create({
  container:    { flex: 1, backgroundColor: BG },
  content:      { paddingBottom: 60 },
  header:       { paddingTop: 64, paddingHorizontal: 24, paddingBottom: 20 },
  heading:      { ...T.heading },
  userName:     { fontSize: 14, color: DIM, marginTop: 6 },

  deviceCard:   {
    flexDirection: 'row', alignItems: 'center',
    backgroundColor: SURFACE, borderRadius: 16,
    marginHorizontal: 20, padding: 20, marginBottom: 24,
  },
  deviceLeft:   { flex: 1 },
  deviceLabel:  { fontSize: 10, letterSpacing: 2, color: WHITE, fontWeight: '700', marginBottom: 4 },
  deviceSub:    { fontSize: 12, color: DIM },
  deviceDot:    {
    width: 10, height: 10, borderRadius: 5,
    backgroundColor: 'rgba(255,255,255,0.25)',
  },

  section:      { marginHorizontal: 20, marginBottom: 24 },
  sectionTitle: { fontSize: 10, letterSpacing: 2, color: DIM, fontWeight: '700', marginBottom: 12 },
  sectionBody:  {
    backgroundColor: SURFACE, borderRadius: 16, overflow: 'hidden',
  },

  row:          {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 16, paddingVertical: 14,
    borderBottomWidth: 1, borderBottomColor: BORDER,
  },
  rowLabel:     { ...T.body, fontSize: 15 },
  rowSub:       { fontSize: 11, color: DIM, marginTop: 2 },
  rowValue:     { fontFamily: 'JetBrainsMono_400Regular', fontSize: 13, color: DIM },
  arrow:        { fontSize: 20, color: DIM },

  badge:        {
    borderWidth: 1, borderColor: FAINT, borderRadius: 6,
    paddingHorizontal: 10, paddingVertical: 4,
  },
  badgeOn:      { backgroundColor: WHITE, borderColor: WHITE },
  badgeText:    { fontSize: 9, letterSpacing: 1, color: DIM, fontWeight: '700' },
  badgeTextOn:  { color: BG },

  logoutBtn:    {
    borderWidth: 1, borderColor: FAINT,
    paddingVertical: 16, alignItems: 'center', borderRadius: 16,
  },
  logoutText:   { color: DIM, fontWeight: '600', letterSpacing: 2, fontSize: 13 },
});
