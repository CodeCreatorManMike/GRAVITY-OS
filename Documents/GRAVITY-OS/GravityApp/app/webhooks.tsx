import { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'expo-router';

import { API_BASE } from '../constants/api';
import { BG, BORDER, DIM, FAINT, SURFACE, SURFACE2, T, WHITE } from '../constants/theme';
import { useAuthStore } from '../store/authStore';

type Direction = 'inbound' | 'outbound';

interface WebhookConfig {
  id: number;
  name: string;
  direction: Direction;
  event_type: string;
  target_url: string | null;
  token: string | null;
  signing_secret_configured: boolean;
  enabled: boolean;
  last_triggered_at: string | null;
  last_status: number | null;
  last_error: string;
}

interface CreateWebhook {
  name: string;
  direction: Direction;
  event_type: string;
  target_url?: string;
  signing_secret?: string;
}

const OUTBOUND_EVENTS = ['HABIT_COMPLETED', 'NUDGE', 'CYCLE_REVIEW_READY', '*'];
const INBOUND_EVENTS = ['DESK_SESSION_STARTED', 'FOCUS_STARTED', 'CUSTOM'];

async function apiRequest<T>(path: string, token: string | null, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export default function WebhooksScreen() {
  const token = useAuthStore(state => state.token);
  const userId = useAuthStore(state => state.userId);
  const router = useRouter();
  const queryClient = useQueryClient();
  const [direction, setDirection] = useState<Direction>('inbound');
  const [name, setName] = useState('');
  const [eventType, setEventType] = useState(INBOUND_EVENTS[0]);
  const [targetUrl, setTargetUrl] = useState('');
  const [signingSecret, setSigningSecret] = useState('');
  const webhooksQueryKey = ['webhooks', userId] as const;

  const webhooks = useQuery<WebhookConfig[]>({
    queryKey: webhooksQueryKey,
    queryFn: () => apiRequest('/integrations/webhooks', token),
    enabled: !!token,
    gcTime: 0,
  });

  const create = useMutation({
    mutationFn: (payload: CreateWebhook) => apiRequest<WebhookConfig>(
      '/integrations/webhooks',
      token,
      { method: 'POST', body: JSON.stringify(payload) },
    ),
    onSuccess: () => {
      setName('');
      setTargetUrl('');
      setSigningSecret('');
      queryClient.invalidateQueries({ queryKey: webhooksQueryKey });
    },
    onError: (error: Error) => Alert.alert('Could not create webhook', error.message),
  });

  const update = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Partial<WebhookConfig> }) => apiRequest<WebhookConfig>(
      `/integrations/webhooks/${id}`,
      token,
      { method: 'PUT', body: JSON.stringify(patch) },
    ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: webhooksQueryKey }),
    onError: (error: Error) => Alert.alert('Could not update webhook', error.message),
  });

  const remove = useMutation({
    mutationFn: (id: number) => apiRequest<void>(`/integrations/webhooks/${id}`, token, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: webhooksQueryKey }),
    onError: (error: Error) => Alert.alert('Could not delete webhook', error.message),
  });

  const selectDirection = (next: Direction) => {
    setDirection(next);
    setEventType(next === 'inbound' ? INBOUND_EVENTS[0] : OUTBOUND_EVENTS[0]);
  };

  const submit = () => {
    if (!name.trim()) {
      Alert.alert('Name required', 'Give this webhook a recognizable name.');
      return;
    }
    if (direction === 'outbound' && !targetUrl.trim()) {
      Alert.alert('Destination required', 'Paste the HTTPS URL from IFTTT or Zapier.');
      return;
    }
    create.mutate({
      name: name.trim(),
      direction,
      event_type: eventType.trim(),
      ...(direction === 'outbound' ? {
        target_url: targetUrl.trim(),
        signing_secret: signingSecret.trim() || undefined,
      } : {}),
    });
  };

  const confirmDelete = (hook: WebhookConfig) => {
    Alert.alert('Delete webhook?', hook.name, [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Delete', style: 'destructive', onPress: () => remove.mutate(hook.id) },
    ]);
  };

  return (
    <ScrollView
      style={s.container}
      contentContainerStyle={s.content}
      keyboardShouldPersistTaps="handled"
      showsVerticalScrollIndicator={false}
    >
      <View style={s.header}>
        <TouchableOpacity onPress={() => router.back()} style={s.backButton}>
          <Text style={s.back}>‹</Text>
        </TouchableOpacity>
        <View>
          <Text style={s.heading}>Webhooks</Text>
          <Text style={s.subtitle}>IFTTT · ZAPIER · SHORTCUTS</Text>
        </View>
      </View>

      <Text style={s.explainer}>
        Inbound URLs let external automations trigger Gravity events. Outbound hooks send Gravity events to another app.
      </Text>

      <View style={s.segment}>
        {(['inbound', 'outbound'] as Direction[]).map(item => (
          <TouchableOpacity
            key={item}
            style={[s.segmentButton, direction === item && s.segmentButtonOn]}
            onPress={() => selectDirection(item)}
          >
            <Text style={[s.segmentText, direction === item && s.segmentTextOn]}>{item.toUpperCase()}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={s.form}>
        <Field label="NAME" value={name} onChangeText={setName} placeholder="Desk plug" />
        <Field
          label="EVENT"
          value={eventType}
          onChangeText={setEventType}
          placeholder="DESK_SESSION_STARTED"
          autoCapitalize="characters"
        />
        <View style={s.chips}>
          {(direction === 'inbound' ? INBOUND_EVENTS : OUTBOUND_EVENTS).map(event => (
            <TouchableOpacity key={event} style={s.chip} onPress={() => setEventType(event)}>
              <Text style={s.chipText}>{event}</Text>
            </TouchableOpacity>
          ))}
        </View>
        {direction === 'outbound' && (
          <>
            <Field
              label="IFTTT / ZAPIER HTTPS URL"
              value={targetUrl}
              onChangeText={setTargetUrl}
              placeholder="https://hooks.zapier.com/..."
              autoCapitalize="none"
              keyboardType="url"
            />
            <Field
              label="SIGNING SECRET (OPTIONAL)"
              value={signingSecret}
              onChangeText={setSigningSecret}
              placeholder="Used for X-Gravity-Signature"
              autoCapitalize="none"
              secureTextEntry
            />
          </>
        )}
        <TouchableOpacity style={s.createButton} onPress={submit} disabled={create.isPending}>
          {create.isPending
            ? <ActivityIndicator color={BG} />
            : <Text style={s.createText}>CREATE {direction.toUpperCase()} WEBHOOK</Text>}
        </TouchableOpacity>
      </View>

      <Text style={s.sectionTitle}>CONFIGURED</Text>
      {webhooks.isLoading && <ActivityIndicator color={WHITE} style={{ marginTop: 24 }} />}
      {webhooks.isError && (
        <TouchableOpacity style={s.empty} onPress={() => webhooks.refetch()}>
          <Text style={s.errorText}>Could not load webhooks. Tap to retry.</Text>
        </TouchableOpacity>
      )}
      {!webhooks.isLoading && !webhooks.isError && (webhooks.data?.length ?? 0) === 0 && (
        <View style={s.empty}><Text style={s.emptyText}>No webhooks configured yet.</Text></View>
      )}
      {(webhooks.data ?? []).map(hook => {
        const inboundUrl = hook.token
          ? `${API_BASE}/integrations/webhooks/inbound/${encodeURIComponent(hook.token)}`
          : null;
        return (
          <View key={hook.id} style={s.card}>
            <View style={s.cardTop}>
              <View style={{ flex: 1 }}>
                <Text style={s.cardName}>{hook.name}</Text>
                <Text style={s.cardMeta}>{hook.direction.toUpperCase()} · {hook.event_type}</Text>
              </View>
              <Switch
                value={hook.enabled}
                onValueChange={enabled => update.mutate({ id: hook.id, patch: { enabled } })}
                trackColor={{ false: FAINT, true: WHITE }}
                thumbColor={BG}
                ios_backgroundColor={FAINT}
              />
            </View>
            {inboundUrl && (
              <View style={s.urlBox}>
                <Text style={s.urlLabel}>POST JSON TO THIS PRIVATE URL</Text>
                <Text selectable style={s.url}>{inboundUrl}</Text>
                <Text style={s.payloadHint}>{'{ "data": { "value": "..." } }'}</Text>
              </View>
            )}
            {hook.target_url && <Text numberOfLines={2} style={s.destination}>{hook.target_url}</Text>}
            <View style={s.statusRow}>
              <Text style={s.statusText}>
                {hook.last_triggered_at
                  ? `LAST ${new Date(hook.last_triggered_at).toLocaleString()}`
                  : 'NOT TRIGGERED YET'}
                {hook.last_status ? ` · HTTP ${hook.last_status}` : ''}
              </Text>
              <TouchableOpacity onPress={() => confirmDelete(hook)}>
                <Text style={s.deleteText}>DELETE</Text>
              </TouchableOpacity>
            </View>
            {!!hook.last_error && <Text style={s.errorText}>{hook.last_error}</Text>}
          </View>
        );
      })}
      <View style={{ height: 48 }} />
    </ScrollView>
  );
}

function Field(props: React.ComponentProps<typeof TextInput> & { label: string }) {
  const { label, ...inputProps } = props;
  return (
    <View style={s.field}>
      <Text style={s.fieldLabel}>{label}</Text>
      <TextInput
        {...inputProps}
        style={s.input}
        placeholderTextColor={FAINT}
        selectionColor={WHITE}
      />
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: BG },
  content: { paddingBottom: 60 },
  header: { paddingTop: 64, paddingHorizontal: 20, paddingBottom: 12, flexDirection: 'row', alignItems: 'center' },
  backButton: { width: 40, height: 40, justifyContent: 'center' },
  back: { color: WHITE, fontSize: 36, lineHeight: 38 },
  heading: { ...T.heading },
  subtitle: { color: DIM, fontSize: 9, letterSpacing: 2, marginTop: 4, fontWeight: '700' },
  explainer: { color: DIM, fontSize: 13, lineHeight: 20, marginHorizontal: 20, marginBottom: 20 },
  segment: { flexDirection: 'row', marginHorizontal: 20, backgroundColor: SURFACE, borderRadius: 12, padding: 4 },
  segmentButton: { flex: 1, alignItems: 'center', paddingVertical: 10, borderRadius: 9 },
  segmentButtonOn: { backgroundColor: WHITE },
  segmentText: { color: DIM, fontSize: 10, letterSpacing: 1.5, fontWeight: '700' },
  segmentTextOn: { color: BG },
  form: { margin: 20, padding: 16, borderRadius: 16, backgroundColor: SURFACE },
  field: { marginBottom: 14 },
  fieldLabel: { color: DIM, fontSize: 9, letterSpacing: 1.5, fontWeight: '700', marginBottom: 7 },
  input: { backgroundColor: SURFACE2, borderWidth: 1, borderColor: BORDER, color: WHITE, paddingHorizontal: 12, paddingVertical: 12, borderRadius: 10, fontFamily: 'JetBrainsMono_400Regular', fontSize: 12 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: -5, marginBottom: 14 },
  chip: { borderWidth: 1, borderColor: BORDER, borderRadius: 6, paddingHorizontal: 8, paddingVertical: 6 },
  chipText: { color: DIM, fontSize: 8, letterSpacing: 0.5, fontWeight: '700' },
  createButton: { minHeight: 48, backgroundColor: WHITE, alignItems: 'center', justifyContent: 'center', borderRadius: 12, marginTop: 2 },
  createText: { color: BG, fontSize: 10, letterSpacing: 1.5, fontWeight: '800' },
  sectionTitle: { color: DIM, fontSize: 10, letterSpacing: 2, fontWeight: '700', marginHorizontal: 20, marginBottom: 12 },
  card: { marginHorizontal: 20, marginBottom: 12, padding: 16, borderRadius: 16, backgroundColor: SURFACE },
  cardTop: { flexDirection: 'row', alignItems: 'center' },
  cardName: { color: WHITE, fontSize: 15, fontWeight: '600' },
  cardMeta: { color: DIM, fontSize: 9, letterSpacing: 1.2, marginTop: 4, fontWeight: '700' },
  urlBox: { backgroundColor: SURFACE2, borderRadius: 10, padding: 12, marginTop: 14 },
  urlLabel: { color: DIM, fontSize: 8, letterSpacing: 1.2, fontWeight: '700', marginBottom: 7 },
  url: { color: WHITE, fontFamily: 'JetBrainsMono_400Regular', fontSize: 10, lineHeight: 16 },
  payloadHint: { color: FAINT, fontFamily: 'JetBrainsMono_400Regular', fontSize: 9, marginTop: 8 },
  destination: { color: DIM, fontFamily: 'JetBrainsMono_400Regular', fontSize: 10, lineHeight: 15, marginTop: 12 },
  statusRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 14 },
  statusText: { color: FAINT, fontSize: 8, letterSpacing: 0.5, flex: 1 },
  deleteText: { color: DIM, fontSize: 9, letterSpacing: 1.2, fontWeight: '700', marginLeft: 12 },
  empty: { marginHorizontal: 20, padding: 20, borderRadius: 16, backgroundColor: SURFACE },
  emptyText: { color: DIM, fontSize: 13, textAlign: 'center' },
  errorText: { color: DIM, fontSize: 11, marginTop: 8 },
});
