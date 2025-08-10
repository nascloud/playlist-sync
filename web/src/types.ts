export type Server = {
  id: number;
  name: string;
  server_type: 'plex' | 'emby' | 'jellyfin';
  url: string;
  // token is sensitive and not sent to the client
};

export type Task = {
  id: number;
  name: string;
  playlist_url: string;
  platform: string;
  status: 'pending' | 'queued' | 'syncing' | 'matching' | 'importing' | 'success' | 'failed';
  last_sync_time: string | null;
  cron_schedule: string;
  unmatched_songs: string; // JSON string
  total_songs: number;
  matched_songs: number;
  created_at: string;
  updated_at: string;
  server_id: number;
  auto_download?: boolean;
};

export type UnmatchedTrack = {
  title: string;
  artist: string;
  album?: string;
  song_id?: string;
  platform?: string;
};

export type SyncProgress = {
  status: string;
  message: string;
  progress?: number;
  total?: number;
};

export interface DownloadSettingsData {
  api_key: string | null;
  download_path: string;
  preferred_quality: string;
  download_lyrics: boolean;
  auto_download: boolean;
  max_concurrent_downloads: number;
}

export interface DownloadSession {
  id: number;
  task_id: number;
  task_name?: string; // Add task_name
  session_type: 'batch' | 'individual' | 'auto';
  total_songs: number;
  success_count: number;
  failed_count: number;
  status: 'active' | 'completed' | 'cancelled' | 'paused'; // Add 'paused'
  created_at: string;
  completed_at: string | null;
  items?: DownloadQueueItem[]; // Add items
}

export interface DownloadQueueItem {
  id: number;
  session_id: number;
  title: string;
  artist: string;
  status: 'pending' | 'downloading' | 'success' | 'failed';
  quality: string;
  error_message: string | null;
}
