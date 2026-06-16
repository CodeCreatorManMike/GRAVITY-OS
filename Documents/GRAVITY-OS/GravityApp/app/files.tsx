/**
 * File manager — upload documents to MinIO, download generated files.
 *
 * Upload flow:  expo-document-picker → multipart POST /files/upload → backend → MinIO
 * Download flow: GET /files → presigned URL → open in browser
 * Delete: DELETE /files/{id}
 */
import { useState, useCallback } from 'react';
import {
  View, Text, FlatList, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, RefreshControl, Linking,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { useRouter } from 'expo-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '../store/authStore';
import { API_BASE } from '../constants/api';

const INK = '#14130d';
const PAPER = '#f4f2ea';

interface GravityFile {
  id: number;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
  download_url: string | null;
}

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function fmtDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })} ${d.getFullYear()}`;
}

export default function FilesScreen() {
  const router = useRouter();
  const token = useAuthStore(s => s.token);
  const queryClient = useQueryClient();
  const [uploading, setUploading] = useState(false);

  const { data: files, isLoading, refetch, isRefetching } = useQuery<GravityFile[]>({
    queryKey: ['files'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/files`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Failed to load files');
      return res.json();
    },
    enabled: !!token,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const res = await fetch(`${API_BASE}/files/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error('Delete failed');
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['files'] }),
    onError: () => Alert.alert('Error', 'Could not delete file.'),
  });

  const confirmDelete = (file: GravityFile) => {
    Alert.alert(
      'Delete file',
      `Remove "${file.filename}"? This cannot be undone.`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: () => deleteMutation.mutate(file.id) },
      ],
    );
  };

  const pickAndUpload = useCallback(async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*', 'text/*'],
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets?.[0]) return;

      const asset = result.assets[0];
      setUploading(true);

      const formData = new FormData();
      formData.append('file', {
        uri: asset.uri,
        name: asset.name,
        type: asset.mimeType ?? 'application/octet-stream',
      } as any);

      const res = await fetch(`${API_BASE}/files/upload`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? 'Upload failed');
      }

      await queryClient.invalidateQueries({ queryKey: ['files'] });
    } catch (e: any) {
      Alert.alert('Upload failed', e.message ?? 'Unknown error');
    } finally {
      setUploading(false);
    }
  }, [token]);

  const openFile = async (file: GravityFile) => {
    if (!file.download_url) {
      Alert.alert('No download link', 'File URL unavailable.');
      return;
    }
    try {
      await Linking.openURL(file.download_url);
    } catch {
      Alert.alert('Error', 'Could not open file.');
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: PAPER }]}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
          <Text style={[styles.back, { color: INK }]}>← BACK</Text>
        </TouchableOpacity>
        <Text style={[styles.title, { color: INK }]}>FILES</Text>
        <TouchableOpacity onPress={pickAndUpload} disabled={uploading}>
          {uploading
            ? <ActivityIndicator color={INK} size="small" />
            : <Text style={[styles.uploadBtn, { color: INK }]}>UPLOAD</Text>}
        </TouchableOpacity>
      </View>

      <FlatList
        data={files ?? []}
        keyExtractor={f => String(f.id)}
        refreshControl={
          <RefreshControl refreshing={isLoading || isRefetching} onRefresh={refetch} tintColor={INK} />
        }
        ListEmptyComponent={
          !isLoading ? (
            <View style={styles.empty}>
              <Text style={[styles.emptyTitle, { color: INK }]}>NO FILES YET</Text>
              <Text style={[styles.emptySub, { color: INK }]}>
                Upload PDFs, study notes, or syllabuses.{'\n'}
                Gravity reads them and uses them to help you.
              </Text>
            </View>
          ) : null
        }
        renderItem={({ item }) => (
          <View style={styles.fileRow}>
            <TouchableOpacity style={styles.fileMain} onPress={() => openFile(item)} activeOpacity={0.7}>
              <View style={styles.fileIcon}>
                <Text style={[styles.fileExt, { color: INK }]}>
                  {item.filename.split('.').pop()?.toUpperCase().slice(0, 3) ?? '—'}
                </Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[styles.fileName, { color: INK }]} numberOfLines={1}>{item.filename}</Text>
                <Text style={[styles.fileMeta, { color: INK }]}>
                  {fmtSize(item.size_bytes)} · {fmtDate(item.created_at)}
                </Text>
              </View>
            </TouchableOpacity>
            <TouchableOpacity onPress={() => confirmDelete(item)} style={styles.deleteBtn} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
              <Text style={[styles.deleteText, { color: INK }]}>✕</Text>
            </TouchableOpacity>
          </View>
        )}
        contentContainerStyle={{ paddingHorizontal: 20, paddingBottom: 60 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingTop: 60, paddingHorizontal: 20, paddingBottom: 16,
    borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.1)',
  },
  back: { fontSize: 11, letterSpacing: 1 },
  title: { fontSize: 11, letterSpacing: 3, fontWeight: '700' },
  uploadBtn: { fontSize: 11, letterSpacing: 2, fontWeight: '700' },
  empty: { paddingTop: 60, alignItems: 'center', paddingHorizontal: 40 },
  emptyTitle: { fontSize: 12, letterSpacing: 3, fontWeight: '600', marginBottom: 12 },
  emptySub: { fontSize: 13, lineHeight: 20, textAlign: 'center', opacity: 0.45 },
  fileRow: {
    flexDirection: 'row', alignItems: 'center',
    paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: 'rgba(20,19,13,0.07)',
  },
  fileMain: { flex: 1, flexDirection: 'row', alignItems: 'center' },
  fileIcon: {
    width: 38, height: 38, borderWidth: 1, borderColor: 'rgba(20,19,13,0.2)',
    borderRadius: 2, justifyContent: 'center', alignItems: 'center', marginRight: 12,
  },
  fileExt: { fontSize: 9, fontWeight: '700', letterSpacing: 0.5 },
  fileName: { fontSize: 14, fontWeight: '500', marginBottom: 2 },
  fileMeta: { fontSize: 11, opacity: 0.4 },
  deleteBtn: { padding: 4 },
  deleteText: { fontSize: 14, opacity: 0.35 },
});
