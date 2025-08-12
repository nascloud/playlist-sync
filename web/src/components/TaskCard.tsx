import React from 'react';
import Button from './Button';
import { Task, UnmatchedTrack, SyncProgress, Server } from '../types';
import StatusIndicator from './StatusIndicator';
import TimeDisplay from './TimeDisplay';
import ProgressBar from './ProgressBar';
import IconButton from './IconButton';
import { Eye, EyeOff, RefreshCw, Settings2, Trash2, Music, Users, Calendar, Clock, Share2, AlertTriangle, DownloadCloud } from 'lucide-react';
import { parseExpression } from 'cron-parser';
import cronstrue from 'cronstrue/i18n';

const cronToLabel = (cron: string) => {
  if (!cron || cron.toLowerCase() === 'off' || cron === '关闭') {
    return '已关闭';
  }
  try {
    // 尝试处理6位带秒的cron表达式
    const parts = cron.split(' ');
    const cronForCronstrue = parts.length === 6 ? parts.slice(1).join(' ') : cron;
    return cronstrue.toString(cronForCronstrue, { locale: "zh_CN" });
  } catch (e) {
    return cron; // 如果解析失败，返回原始表达式
  }
};

const NextSyncTimeDisplay: React.FC<{ cronExpression: string }> = ({ cronExpression }) => {
  try {
    if (!cronExpression || cronExpression.toLowerCase() === 'off' || cronExpression === '关闭') {
      return <span className="font-semibold text-gray-500">已关闭</span>;
    }

    // 统一处理6位表达式，确保两个库使用相同的输入
    const parts = cronExpression.split(' ');
    const cronToParse = parts.length === 6 ? parts.slice(1).join(' ') : cronExpression;
    
    // 再次验证表达式，以防万一
    cronstrue.toString(cronToParse, { locale: "zh_CN" });

    const interval = parseExpression(cronToParse, { utc: true });
    const nextDate = interval.next().toDate();
    
    return <TimeDisplay timeString={nextDate.toISOString()} />;
  } catch (err) {
    console.error(`[Final Attempt] Cron parsing failed for expression: "${cronExpression}"`, err);
    return <span className="font-semibold text-red-500 flex items-center gap-1"><AlertTriangle className="w-4 h-4" /> 表达式无效</span>;
  }
};

interface TaskCardProps {
  task: Task;
  servers: Server[];
  isSyncing: boolean;
  isExpanded: boolean;
  unmatchedSongs: UnmatchedTrack[];
  syncProgress?: SyncProgress;
  onSync: (id: number) => void;
  onDelete: (id: number) => void;
  onEdit: (task: Task) => void;
  onToggleExpand: (id: number) => void;
  onDownloadAll: (task: Task) => void;
  onDownloadSingle: (task: Task, song: UnmatchedTrack) => void;
}

const PlatformLogo = ({ platform }: { platform: string }) => {
  // Simple text-based logo for now
  const platformMap: Record<string, { label: string; color: string }> = {
    netease: { label: 'N', color: 'bg-red-500' },
    qq: { label: 'Q', color: 'bg-green-500' },
  };
  const { label, color } = platformMap[platform] || { label: '?', color: 'bg-gray-400' };

  return (
    <div className={`w-6 h-6 ${color} rounded-full flex items-center justify-center text-white text-sm font-bold`}>
      {label}
    </div>
  );
};

const TaskCard: React.FC<TaskCardProps> = ({
  task,
  servers,
  isSyncing,
  isExpanded,
  unmatchedSongs,
  syncProgress,
  onSync,
  onDelete,
  onEdit,
  onToggleExpand,
  onDownloadAll,
  onDownloadSingle,
}) => {
  const hasCounts = task.total_songs != null && task.matched_songs != null;
  const unmatchedCount = hasCounts ? task.total_songs - task.matched_songs : null;

  const isSyncingLive = syncProgress && syncProgress.status !== 'success' && syncProgress.status !== 'failed' && syncProgress.status !== 'error';
  const server = servers.find(s => s.id === task.server_id);

  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden transition-all duration-300 hover:shadow-lg">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-4">
          <div className="flex flex-1 min-w-0 items-center gap-3">
            <PlatformLogo platform={task.platform} />
            <h2 className="text-xl font-bold text-gray-800 truncate" title={task.name}>
              {task.name}
            </h2>
          </div>
          <StatusIndicator status={isSyncingLive ? syncProgress.status as Task['status'] : task.status} />
        </div>

        {/* Body */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Info Section */}
          <div className="md:col-span-2 space-y-3">
            {isSyncingLive ? (
              <>
                <div className="flex items-baseline gap-3 text-sm text-gray-600">
                  <Users className="w-5 h-5 text-gray-400" />
                  <span>同步进度:</span>
                  <span className="font-semibold text-blue-600">{syncProgress.message}</span>
                </div>
                {syncProgress.total != null && syncProgress.progress != null ? (
                  <ProgressBar value={syncProgress.progress} max={syncProgress.total} />
                ) : <ProgressBar value={100} max={100} className="opacity-50 animate-pulse" />}
              </>
            ) : (
              <>
                <div className="flex items-baseline gap-3 text-sm text-gray-600">
                  <Users className="w-5 h-5 text-gray-400" />
                  <span>同步结果:</span>
                  {hasCounts ? (
                    <span className="font-semibold text-gray-800">
                      {task.matched_songs} / {task.total_songs} 首
                    </span>
                  ) : (
                    <span className="text-gray-500">暂无数据</span>
                  )}
                </div>
                {hasCounts && <ProgressBar value={task.matched_songs} max={task.total_songs} />}
              </>
            )}
            
            <div className="flex items-baseline gap-3 text-sm text-gray-600">
              <Calendar className="w-5 h-5 text-gray-400" />
              <span>同步计划:</span>
              <span className="font-semibold text-gray-800">{cronToLabel(task.cron_schedule)}</span>
            </div>
            
            <div className="flex items-baseline gap-3 text-sm text-gray-600">
              <Clock className="w-5 h-5 text-gray-400" />
              <span>下次同步:</span>
              <NextSyncTimeDisplay cronExpression={task.cron_schedule} />
            </div>

            <div className="flex items-baseline gap-3 text-sm text-gray-600">
              <Share2 className="w-5 h-5 text-gray-400" />
              <span>同步到:</span>
              <span className="font-semibold text-gray-800">{server ? server.name : '未知服务器'}</span>
            </div>
            
            <div className="flex items-baseline gap-3 text-sm text-gray-600">
              <Clock className="w-5 h-5 text-gray-400" />
              <span>上次同步:</span>
              <TimeDisplay timeString={task.last_sync_time} />
            </div>
          </div>

          {/* Actions Section */}
          <div className="flex items-center md:justify-end gap-2">
            <IconButton
              size="lg"
              tooltip="立即同步"
              onClick={() => onSync(task.id)}
              disabled={isSyncing}
            >
              <RefreshCw className={`h-5 w-5 ${isSyncing ? 'animate-spin' : ''}`} />
            </IconButton>
            <IconButton size="lg" tooltip="编辑计划" onClick={() => onEdit(task)}>
              <Settings2 className="h-5 w-5" />
            </IconButton>
            <IconButton size="lg" variant="danger" tooltip="删除任务" onClick={() => onDelete(task.id)}>
              <Trash2 className="h-5 w-5" />
            </IconButton>
          </div>
        </div>

        {/* Footer / Expandable trigger */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <button
            onClick={() => onToggleExpand(task.id)}
            className="flex items-center justify-center w-full text-sm font-medium text-blue-600 hover:text-blue-800"
          >
            {isExpanded ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
            {isExpanded ? '隐藏' : '查看'}未匹配曲目
            {unmatchedCount !== null && unmatchedCount > 0 && (
              <span className="ml-2 bg-red-100 text-red-800 text-xs font-semibold px-2 py-0.5 rounded-full">
                {unmatchedCount}
              </span>
            )}
          </button>
        </div>
      </div>
      
      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-6 pb-6 bg-gray-50/50">
           <h3 className="text-md font-semibold text-gray-700 mb-3">未匹配的歌曲:</h3>
           {unmatchedCount !== null && unmatchedCount > 0 ? (
            unmatchedSongs && unmatchedSongs.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-72 overflow-y-auto pr-2">
                {unmatchedSongs.map((song, index) => (
                  <div key={index} className="flex items-center p-3 bg-white rounded-lg shadow-sm border">
                    <Music className="w-5 h-5 text-gray-400 mr-3 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">{song.title}</div>
                      <div className="text-sm text-gray-500 truncate">{song.artist}</div>
                    </div>
                    <IconButton size="sm" tooltip="下载这首歌" onClick={() => onDownloadSingle(task, song)}>
                      <DownloadCloud className="h-4 w-4" />
                    </IconButton>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">正在加载未匹配歌曲列表...</p>
            )
           ) : (
             <p className="text-sm text-gray-500">太棒了！所有歌曲都已成功匹配。</p>
           )}
           <div className="mt-4">
             <Button 
               variant="secondary"
               size="sm"
               onClick={() => onDownloadAll(task)}
               disabled={unmatchedCount === null || unmatchedCount === 0}
             >
               一键下载全部
             </Button>
           </div>
        </div>
      )}
    </div>
  );
};

export default TaskCard;
