import React, { useState, useEffect, useCallback } from 'react';
import { format, formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { toast } from 'sonner';
import { fetchFromApi } from '../lib/api';
import Button from '../components/Button';
import Modal from '../components/Modal';
import Input from '../components/Input';
import CronGenerator from '../components/CronGenerator';
import { Task, UnmatchedTrack, SyncProgress, Server } from '../types';
import TaskCard from '../components/TaskCard';
import { PlusCircle } from 'lucide-react';

// A small component to render time in a user-friendly format
export const TimeDisplay: React.FC<{ timeString: string | null }> = ({ timeString }) => {
  if (!timeString) {
    return <span className="font-semibold text-gray-500">从未</span>;
  }
  try {
    const date = new Date(timeString);
    const absoluteTime = format(date, 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
    const relativeTime = formatDistanceToNow(date, { addSuffix: true, locale: zhCN });
    return <span className="font-semibold text-gray-800" title={absoluteTime}>{relativeTime}</span>;
  } catch (e) {
    return <span className="font-semibold text-red-500">日期无效</span>;
  }
};

// 获取API请求头
const getHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Authorization': `Bearer ${token}`,
  };
};

const DashboardPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [servers, setServers] = useState<Server[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  
  // Form and async state
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [platform, setPlatform] = useState<'netease' | 'qq'>('netease');
  const [selectedServerId, setSelectedServerId] = useState<number | null>(null);
  const [addModalError, setAddModalError] = useState('');
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const [newSyncSchedule, setNewSyncSchedule] = useState('');
  const [taskAutoDownload, setTaskAutoDownload] = useState(false);
  const [syncingTaskId, setSyncingTaskId] = useState<number | null>(null);
  
  // Preview state
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [previewData, setPreviewData] = useState<{title: string, track_count: number} | null>(null);
  
  // Expandable row state
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null);
  const [unmatchedSongs, setUnmatchedSongs] = useState<Record<number, UnmatchedTrack[]>>({});
  const [syncProgress, setSyncProgress] = useState<Record<number, SyncProgress>>({});

  const fetchInitialData = useCallback(async () => {
    setLoading(true);
    try {
      const [tasksData, settingsData] = await Promise.all([
        fetchFromApi('/tasks'),
        fetchFromApi('/settings')
      ]);

      if (tasksData.success) {
        setTasks(tasksData.tasks);
      }

      if (settingsData.success && settingsData.servers.length > 0) {
        setServers(settingsData.servers);
      }
    } catch (error) {
      console.error('Failed to fetch initial data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTasksOnly = useCallback(async () => {
    try {
      const data = await fetchFromApi('/tasks');
      if (data.success) {
        setTasks(data.tasks);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
  }, []);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);
  
  useEffect(() => {
    if (servers.length > 0 && selectedServerId === null) {
      setSelectedServerId(servers[0].id);
    }
  }, [servers]);

  useEffect(() => {
    const interval = setInterval(fetchTasksOnly, 5000);
    return () => clearInterval(interval);
  }, [fetchTasksOnly]);

  const handleOpenAddModal = () => {
    setPlaylistUrl('');
    setPlatform('netease');
    setAddModalError('');
    setIsAddModalOpen(true);
  };

  const handleCloseAddModal = useCallback(() => {
    setIsAddModalOpen(false);
  }, []);

  const handleCloseEditModal = useCallback(() => {
    setIsEditModalOpen(false);
  }, []);

  
  const handleAddPlaylist = async () => {
    if (!playlistUrl) {
      setAddModalError('请输入歌单 URL。');
      return;
    }
    if (!selectedServerId) {
      setAddModalError('请选择一个服务器。');
      return;
    }
    setAddModalError('');
    setIsAdding(true);

    try {
      // 第一步：预览歌单信息
      const previewResponse = await fetch('/api/preview-playlist', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getHeaders(),
        },
        body: JSON.stringify({
          playlist_url: playlistUrl,
          platform: platform
        }),
      });

      const previewData = await previewResponse.json();

      if (!previewResponse.ok) {
        // 预览失败，显示详细错误信息
        let errorMsg = '解析歌单失败，请检查输入。';
        if (previewData.detail) {
          if (typeof previewData.detail === 'string') {
            errorMsg = previewData.detail;
          } else if (Array.isArray(previewData.detail)) {
            errorMsg = previewData.detail.map((e: any) => `${e.loc.join('.')} - ${e.msg}`).join('; ');
          }
        }
        setAddModalError(errorMsg);
        setIsAdding(false);
        return;
      }

      // 预览成功，显示歌单信息并确认添加
      setPreviewData(previewData);
      setIsPreviewModalOpen(true);
      setIsAdding(false);
    } catch (err) {
      setAddModalError('无法连接到后端服务。');
      setIsAdding(false);
    }
  };

  const handleConfirmAddPlaylist = async () => {
    if (!previewData || !selectedServerId) return;
    
    setIsAdding(true);
    setIsPreviewModalOpen(false);

    try {
      // 创建同步任务（传递预览数据以避免重复解析）
      const createResponse = await fetch('/api/tasks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getHeaders(),
        },
        body: JSON.stringify({
          name: newPlaylistName || previewData.title, // 使用用户输入的名称或歌单标题
          playlist_url: playlistUrl,
          platform: platform,
          server_id: selectedServerId,
          cron_schedule: '0 2 * * *', // Default to daily
          preview_data: previewData // 传递预览数据以避免重复解析
        }),
      });

      const createData = await createResponse.json();

      if (createResponse.ok && createData.id) {
        // 成功创建任务
        setIsAddModalOpen(false);
        setNewPlaylistName('');
        setPlaylistUrl('');
        setPreviewData(null);
        fetchInitialData();
        // 显示成功提示
        toast.success(`成功添加歌单 "${createData.name}" 到同步列表！`);
      } else {
        // 处理创建任务时的错误
        let errorMsg = '添加任务失败，请重试。';
        if (createData.detail) {
          if (typeof createData.detail === 'string') {
            errorMsg = createData.detail;
          } else if (Array.isArray(createData.detail)) {
            errorMsg = createData.detail.map((e: any) => `${e.loc.join('.')} - ${e.msg}`).join('; ');
          }
        }
        setAddModalError(errorMsg);
      }
    } catch (err) {
      setAddModalError('无法连接到后端服务。');
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (window.confirm('您确定要删除这个任务吗？')) {
      try {
        const data = await fetchFromApi(`/tasks/${taskId}`, { method: 'DELETE' });
        if (data.success) {
          // Manually filter out the deleted task from the state
          setTasks(prevTasks => prevTasks.filter(task => task.id !== taskId));
        } else {
          console.error('Failed to delete task');
        }
      } catch (error) {
        console.error('Error deleting task:', error);
      }
    }
  };

  const handleOpenEditModal = (task: Task) => {
    setEditingTask(task);
    setNewSyncSchedule(task.cron_schedule);
    setTaskAutoDownload(task.auto_download || false);
    setIsEditModalOpen(true);
  };
  
  const handleUpdateTask = async () => {
    if (!editingTask) return;
    
    await fetchFromApi(`/tasks/${editingTask.id}`, {
      method: 'PUT',
      body: JSON.stringify({ 
        cron_schedule: newSyncSchedule,
        auto_download: taskAutoDownload 
      }),
    });
    setIsEditModalOpen(false);
    fetchTasksOnly();
  };

  const handleSyncTask = (taskId: number) => {
    setSyncingTaskId(taskId);
    setSyncProgress(prev => ({ ...prev, [taskId]: { status: 'starting', message: '正在连接...' } }));

    const eventSource = new EventSource(`/api/tasks/${taskId}/sync/stream?token=${localStorage.getItem('token')}`);

    eventSource.addEventListener('progress', (event) => {
      try {
        const progressData: SyncProgress = JSON.parse(event.data);
        setSyncProgress(prev => ({ ...prev, [taskId]: progressData }));
      } catch (e) {
        console.error("Failed to parse progress event", e);
      }
    });

    eventSource.addEventListener('error', (event) => {
      console.error('EventSource failed:', event);
      setSyncProgress(prev => ({
        ...prev,
        [taskId]: { status: 'failed', message: '连接错误，同步中断' }
      }));
      eventSource.close();
      // 在短暂延迟后清除状态，并刷新列表
      setTimeout(() => {
        setSyncingTaskId(null);
        setSyncProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[taskId];
          return newProgress;
        });
        fetchInitialData();
      }, 5000);
    });

    eventSource.addEventListener('close', () => {
      eventSource.close();
      setSyncingTaskId(null);
       // 在短暂延迟后清除状态，并刷新列表
      setTimeout(() => {
        setSyncProgress(prev => {
          const newProgress = { ...prev };
          delete newProgress[taskId];
          return newProgress;
        });
        fetchInitialData();
      }, 2000);
    });
  };

  const fetchUnmatchedSongs = async (taskId: number) => {
    try {
      const data = await fetchFromApi(`/tasks/${taskId}/unmatched`);
      if (data.success) {
        setUnmatchedSongs(prev => ({
          ...prev,
          [taskId]: data.unmatched_songs
        }));
      }
    } catch (error) {
      console.error(`Failed to fetch unmatched songs for task ${taskId}:`, error);
    }
  };

  const toggleExpandRow = (taskId: number) => {
    const isOpening = expandedTaskId !== taskId;
    setExpandedTaskId(isOpening ? taskId : null);

    // 如果是展开操作，则总是获取最新的未匹配列表
    if (isOpening) {
      fetchUnmatchedSongs(taskId);
    }
  };

  const handleDownloadAll = async (task: Task) => {
    try {
      const result = await fetchFromApi('/download/all-missing', {
        method: 'POST',
        body: JSON.stringify({ task_id: task.id }),
      });
      if (result.success) {
        toast.success(`已为任务 "${task.name}" 创建批量下载会话。`);
      } else {
        toast.error(`批量下载失败: ${result.message || '未知错误'}`);
      }
    } catch (error) {
      toast.error('请求批量下载失败，请检查网络连接。');
    }
  };

  const handleDownloadSingle = async (task: Task, song: UnmatchedTrack) => {
    try {
      toast.info(`正在将《${song.title}》加入下载队列...`);
      const result = await fetchFromApi('/download/single', {
        method: 'POST',
        body: JSON.stringify({
          task_id: task.id,
          song_id: song.song_id,
          title: song.title,
          artist: song.artist,
          album: song.album,
        }),
      });
      if (result.success) {
        toast.success(`《${song.title}》已成功加入下载队列。`);
      } else {
        toast.error(`下载《${song.title}》失败: ${result.message || '未知错误'}`);
      }
    } catch (error) {
      toast.error('请求下载失败，请检查网络连接。');
    }
  };

  if (loading) {
    // You can implement a skeleton loader here for better UX
    return <div className="text-center p-8 text-gray-500">正在加载任务...</div>;
  }

  return (
    <div className="p-4 sm:p-8">
      <header className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">同步任务</h1>
        <Button onClick={handleOpenAddModal} className="flex items-center gap-2 flex-shrink-0 whitespace-nowrap">
          <PlusCircle className="h-5 w-5" />
          <span className="whitespace-nowrap">添加歌单</span>
        </Button>
      </header>

      {tasks.length > 0 ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              servers={servers}
              isSyncing={syncingTaskId === task.id || !!syncProgress[task.id] || ['syncing', 'matching', 'importing', 'queued'].includes(task.status)}
              isExpanded={expandedTaskId === task.id}
              unmatchedSongs={unmatchedSongs[task.id] || []}
              syncProgress={syncProgress[task.id]}
              onSync={handleSyncTask}
              onDelete={handleDeleteTask}
              onEdit={handleOpenEditModal}
              onToggleExpand={toggleExpandRow}
              onDownloadAll={handleDownloadAll}
              onDownloadSingle={handleDownloadSingle}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 border-2 border-dashed border-gray-300 rounded-lg bg-white">
          <h3 className="text-lg font-medium text-gray-900">没有同步任务</h3>
          <p className="mt-1 text-sm text-gray-500">点击右上角的“添加歌单”来开始你的第一个同步任务吧！</p>
        </div>
      )}

      {/* Add Task Modal */}
      <Modal isOpen={isAddModalOpen} onClose={handleCloseAddModal} title="添加新歌单">
        <div className="space-y-4">
          <Input
            id="playlist-name"
            label="歌单名称 (可选)"
            value={newPlaylistName}
            onChange={(e) => setNewPlaylistName(e.target.value)}
            placeholder="未填写则使用源歌单标题"
          />
          <Input
            id="playlist-url"
            label="歌单 URL"
            value={playlistUrl}
            onChange={(e) => setPlaylistUrl(e.target.value)}
            placeholder="请输入歌单的分享链接"
            required
          />
          <div>
            <label className="block text-sm font-medium text-gray-700">平台</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value as 'netease' | 'qq')}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              <option value="netease">网易云音乐</option>
              <option value="qq">QQ音乐</option>
            </select>
          </div>
          <div>
            <label htmlFor="server-select" className="block text-sm font-medium text-gray-700 mt-4">同步到服务器</label>
            <select
              id="server-select"
              value={selectedServerId ?? ''}
              onChange={(e) => setSelectedServerId(Number(e.target.value))}
              disabled={servers.length === 0}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            >
              {servers.length > 0 ? (
                servers.map(server => (
                  <option key={server.id} value={server.id}>
                    {server.name} ({server.server_type})
                  </option>
                ))
              ) : (
                <option disabled>
                  {loading ? '正在加载服务器...' : '未找到服务器，请先在设置中添加'}
                </option>
              )}
            </select>
          </div>
        </div>
        {addModalError && <p className="text-red-500 text-sm mt-2">{addModalError}</p>}
        <div className="flex justify-end gap-4 mt-6">
          <Button variant="secondary" onClick={handleCloseAddModal}>取消</Button>
          <Button onClick={handleAddPlaylist} loading={isAdding}>添加</Button>
        </div>
      </Modal>
      
      {/* Preview Confirmation Modal */}
      <Modal isOpen={isPreviewModalOpen} onClose={() => setIsPreviewModalOpen(false)} title="确认歌单信息">
        {previewData && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900">歌单标题</h3>
              <p className="mt-1 text-gray-700">{previewData.title}</p>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="font-medium text-gray-900">歌曲数量</h3>
              <p className="mt-1 text-gray-700">{previewData.track_count} 首</p>
            </div>
            <p className="text-sm text-gray-500">请确认以上歌单信息是否正确，确认后将添加到同步列表。</p>
          </div>
        )}
        <div className="flex justify-end gap-4 mt-6">
          <Button 
            variant="secondary" 
            onClick={() => setIsPreviewModalOpen(false)}
          >
            取消
          </Button>
          <Button 
            onClick={handleConfirmAddPlaylist}
            loading={isAdding}
          >
            确认添加
          </Button>
        </div>
      </Modal>
      
      {/* Edit Task Modal */}
      <Modal isOpen={isEditModalOpen} onClose={handleCloseEditModal} title="编辑任务">
        <div>
          <label htmlFor="sync-schedule" className="block text-sm font-medium text-gray-700">同步计划</label>
          <CronGenerator 
            value={newSyncSchedule} 
            onChange={setNewSyncSchedule} 
          />
        </div>
        <div className="mt-4 flex items-center">
          <input
            id="auto-download-checkbox"
            type="checkbox"
            checked={taskAutoDownload}
            onChange={(e) => setTaskAutoDownload(e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="auto-download-checkbox" className="ml-2 block text-sm text-gray-900">
            同步后自动下载缺失歌曲
          </label>
        </div>
        <div className="flex justify-end gap-4 mt-6">
          <Button variant="secondary" onClick={() => setIsEditModalOpen(false)}>取消</Button>
          <Button onClick={handleUpdateTask}>保存</Button>
        </div>
      </Modal>
    </div>
  );
};

export default DashboardPage;
