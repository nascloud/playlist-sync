# 下载功能完整设计文档

## 概述

本文档详细描述了Plex音乐同步工具中下载功能的完整设计，包括三种下载方式、下载管理界面以及相关的技术架构。

## 1. 功能定位

### 1.1 主要目标
- 为同步任务中未匹配的歌曲提供下载功能
- 支持多种下载触发方式，满足不同用户需求
- 提供完整的下载管理和监控界面
- 实现自动化的下载流程

### 1.2 核心价值
- **补充缺失**：下载Plex库中缺失的歌曲
- **灵活控制**：支持批量下载和单个下载
- **智能管理**：提供下载队列和进度监控
- **用户体验**：简化的操作流程和实时反馈

## 2. 下载方式设计

### 2.1 三种下载触发方式

#### 方式一：一键下载全部缺失歌曲
- **触发位置**：任务卡片上的"下载全部缺失"按钮
- **适用场景**：用户希望一次性下载所有未匹配歌曲
- **操作流程**：
  1. 获取任务所有未匹配歌曲
  2. 批量添加到下载队列
  3. 显示总体进度
  4. 下载完成后，调用Plex API触发媒体库扫描，待扫描完成后自动触发一次新的同步

#### 方式二：单个歌曲下载
- **触发位置**：缺失歌曲列表中的"下载"按钮
- **适用场景**：用户只想下载特定歌曲
- **操作流程**：
  1. 选择单个歌曲
  2. 立即开始下载
  3. 显示下载状态
  4. 完成后更新列表

#### 方式三：自动下载（歌单）
- **触发位置**：歌单编辑页面
- **适用场景**：同步完成后自动开始下载
- **操作流程**：
  1. 同步完成
  2. 检查未匹配歌曲
  3. 自动开始下载
  4. 后台处理
  5. 下载完毕后，调用Plex API触发媒体库扫描，待扫描完成后自动触发一次新的同步

## 3. 数据模型设计

### 3.1 数据库表结构

#### download_settings表
```sql
CREATE TABLE download_settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    api_key TEXT,                    -- 加密的API Key
    download_path TEXT,              -- 下载路径
    preferred_quality TEXT,          -- 首选音质
    download_lyrics BOOLEAN,         -- 是否下载歌词
    auto_download BOOLEAN DEFAULT 0, -- 全局自动下载开关
    max_concurrent_downloads INTEGER DEFAULT 3, -- 最大并发下载数
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### download_queue表
```sql
CREATE TABLE download_queue (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,                 -- [新增] 关联的下载会话
    task_id INTEGER,                 -- 关联的同步任务
    song_id TEXT,                    -- 歌曲唯一标识
    title TEXT,                      -- 歌曲标题
    artist TEXT,                     -- 艺术家
    album TEXT,                      -- 专辑
    platform TEXT,                   -- 来源平台
    status TEXT DEFAULT 'pending',   -- 状态：pending/downloading/success/failed
    download_path TEXT,              -- 下载文件路径
    file_size INTEGER,               -- 文件大小
    quality TEXT,                    -- 下载音质
    error_message TEXT,              -- 错误信息
    retry_count INTEGER DEFAULT 0,   -- 重试次数
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

#### download_sessions表
```sql
CREATE TABLE download_sessions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,                 -- 关联的同步任务
    session_type TEXT,               -- 会话类型：batch/individual/auto
    total_songs INTEGER,             -- 总歌曲数
    success_count INTEGER DEFAULT 0, -- 成功数
    failed_count INTEGER DEFAULT 0,  -- 失败数
    status TEXT DEFAULT 'active',    -- 状态：active/completed/cancelled
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 3.2 状态流转设计

#### 下载状态流转
```
pending → queued → downloading → success/failed
                ↓
            cancelled
```

#### 会话状态流转
```
active → completed/cancelled
```

## 4. 核心服务架构

### 4.1 DownloadService（核心服务）

现有backend/service/downloader_core.py已实现基础下载，查看downloader_core_usage.md说明文档

```python
class DownloadService:
    def __init__(self):
        self.downloader = None
        self.active_sessions = {}  # 活跃下载会话
    
    # 方式一：批量下载全部缺失歌曲
    async def download_all_missing(self, task_id: int) -> int:
        """下载任务中所有缺失歌曲，返回下载会话ID"""
        
    # 方式二：下载单个歌曲
    async def download_single_song(self, task_id: int, song_info: dict) -> bool:
        """下载单个歌曲"""
        
    # 方式三：自动下载（同步后触发）
    async def auto_download_missing(self, task_id: int) -> int:
        """同步完成后自动下载缺失歌曲"""
        
    # 下载队列管理
    async def get_download_queue(self, task_id: int = None) -> List[dict]:
        """获取下载队列"""
        
    async def cancel_download(self, session_id: int) -> bool:
        """取消下载会话"""
        
    async def retry_failed_download(self, queue_id: int) -> bool:
        """重试失败的下载"""
```

### 4.2 DownloadQueueManager（队列管理器）
```python
class DownloadQueueManager:
    def __init__(self):
        self.max_concurrent = 3
        self.active_downloads = {}
        self.download_semaphore = asyncio.Semaphore(3)
    
    async def add_to_queue(self, download_items: List[dict]) -> int:
        """添加下载项到队列"""
        
    async def process_queue(self):
        """处理下载队列"""
        
    async def get_queue_status(self) -> dict:
        """获取队列状态"""
```
```

## 5. API接口设计

### 5.1 下载设置API
```
GET /api/download-settings          # 获取下载设置
POST /api/download-settings         # 保存下载设置
POST /api/download-settings/test    # 测试API连接
```

### 5.2 下载操作API
```
POST /api/download/all-missing      # 一键下载全部缺失
POST /api/download/single           # 下载单个歌曲
POST /api/download/auto             # 全局启用/禁用自动下载 (主开关)
POST /api/download/auto/{taskid}    # 歌单启用/禁用自动下载 (受主开关约束)
GET /api/download/queue             # 获取下载队列
POST /api/download/cancel           # 取消下载会话
POST /api/download/retry            # 重试失败下载
```

### 5.3 下载管理API
```
GET /api/download/sessions          # 获取下载会话列表
GET /api/download/sessions/{id}     # 获取会话详情
DELETE /api/download/sessions/{id}  # 删除会话记录
GET /api/download/stats             # 获取下载统计
```

## 6. 前端界面架构

### 6.1 设置页面扩展
```
设置页面新增标签页：
├── 服务器设置（现有）
├── 下载设置（新增）
│   ├── API Key配置
│   ├── 下载路径设置
│   ├── 音质偏好选择
│   ├── 歌词下载选项
│   ├── 自动下载开关
│   └── 并发下载数量
└── 高级设置
```

### 6.2 任务卡片扩展
```
任务卡片新增元素：
├── 同步状态（现有）
├── 匹配统计（现有）
├── 缺失歌曲列表（扩展）

├── 下载全部缺失（新增）

|── 下载进度条（新增）

│   ├── 歌曲信息
│   ├── 下载按钮（单个）
│   └── 下载状态指示
├── 操作按钮组
│   ├── 编辑任务
│   ├── 立即同步
│   └── 查看下载队列（新增）

```

### 6.3 下载管理页面（新增）
```
下载管理页面结构：
├── 页面标题和统计
├── 筛选和搜索
│   ├── 按任务筛选
│   ├── 按状态筛选
│   └── 搜索框
├── 下载会话列表
│   ├── 会话信息
│   ├── 进度显示
│   ├── 操作按钮
│   └── 详细信息
├── 实时队列状态
│   ├── 活跃下载
│   ├── 等待队列
│   └── 完成统计
└── 批量操作
    ├── 暂停所有
    ├── 恢复所有
    └── 清理完成
```

## 7. 状态管理设计

### 7.1 全局状态管理
```typescript
interface DownloadState {
  // 全局设置
  settings: DownloadSettings;
  
  // 活跃会话
  activeSessions: DownloadSession[];
  
  // 下载队列
  downloadQueue: DownloadItem[];
  
  // 实时统计
  stats: DownloadStats;
  
  // 全局控制
  isAutoDownloadEnabled: boolean;
  isQueueProcessing: boolean;
}
```

### 7.2 通信设计

#### 轮询事件
## 8. 核心算法逻辑

### 8.1 歌曲搜索算法
```
输入：歌曲信息（songID，标题、艺术家、专辑）
步骤：
1. 优先使用songID直接下载
失败后：
1. 构建搜索关键词（标题 + 艺术家）
2. 调用搜索接口
3. 对搜索结果进行相似度评分
4. 选择评分最高的匹配结果
输出：最佳匹配的歌曲ID和下载信息
```

### 8.2 相似度评分算法
```
评分权重：
- 标题匹配度：60%
- 艺术家匹配度：30%
- 专辑匹配度：10%

评分方法：
- 精确匹配：100分
- 包含关系：80分
- 模糊匹配：使用编辑距离计算
```

### 8.3 音质选择算法
```
用户偏好音质优先级：
1. 无损 (lossless)
2. 高品 (high quality)
3. 标准 (standard)

选择逻辑：
- 优先选择用户偏好的音质
- 如果不可用，自动降级到下一级
- 如果都不可用，选择最高可用音质
```

## 9. 用户体验流程

### 9.1 一键下载流程
```
用户点击"下载全部缺失" → 显示确认对话框 → 开始下载会话 → 显示进度条 → 完成提示
```

### 9.2 单个下载流程
```
用户点击歌曲旁的"下载"按钮 → 立即开始下载 → 显示下载状态 → 完成后更新列表
```

### 9.3 自动下载流程
```
同步完成 → 检查自动下载设置 → 如果启用则自动开始下载 → 后台处理 → 通知用户
```

## 10. 错误处理和重试机制

### 10.1 错误分类
- **网络错误**：连接超时、API限制
- **文件错误**：磁盘空间不足、文件权限
- **API错误**：无效Key、配额超限
- **匹配错误**：找不到合适歌曲

### 10.2 重试策略
```
重试次数：最多3次
重试间隔：指数退避（5s, 30s, 90s）
重试条件：网络错误、API限制
跳过条件：文件错误、匹配错误
```

## 11. 性能优化策略

### 11.1 并发控制
- **全局并发限制**：通过全局信号量（Semaphore）实现，默认3个同时下载。此限制应用于所有任务，确保系统总负载可控。
- **资源监控**：CPU、内存、网络使用率

### 11.2 队列优化
- **优先级队列**：单个下载优先于批量下载
- **智能调度**：根据文件大小和网络状况调整

## 12. 安全考虑

### 12.1 API Key安全
- **加密存储**：使用AES-256加密存储API Key
- **访问控制**：限制API Key的访问权限
- **定期轮换**：支持API Key的定期更新

### 12.2 文件安全
- **路径验证**：防止路径遍历攻击
- **文件类型检查**：只允许下载音频文件
- **病毒扫描**：可选的下载文件安全检查

## 13. 扩展性考虑

### 13.1 多平台支持
- **平台抽象**：支持多个音乐平台
- **统一接口**：标准化的下载接口
- **插件机制**：支持第三方下载源

### 13.2 功能扩展
- **批量下载**：支持批量歌曲下载
- **智能匹配**：AI辅助的歌曲匹配
- **质量检测**：下载后的音质检测

## 14. 实施计划

### 14.1 第一阶段：基础功能
- [ ] 数据库表结构创建
- [ ] DownloadService核心服务实现
- [ ] 基础API接口开发
- [ ] 设置页面扩展

### 14.2 第二阶段：用户界面
- [ ] 任务卡片下载按钮
- [ ] 单个歌曲下载功能
- [ ] 下载进度显示
- [ ] 基础错误处理

### 14.3 第三阶段：高级功能
- [ ] 下载管理页面
- [ ] 批量下载功能
- [ ] 自动下载选项
- [ ] 实时通信实现

### 14.4 第四阶段：优化完善
- [ ] 性能优化
- [ ] 错误处理完善
- [ ] 用户体验优化
- [ ] 测试和文档

## 15. 技术栈要求

### 15.1 后端技术
- Python 3.8+
- FastAPI
- SQLite/PostgreSQL
- asyncio
- WebSocket支持

### 15.2 前端技术
- React 18+
- TypeScript
- Tailwind CSS
- WebSocket客户端

### 15.3 依赖库
- requests（HTTP请求）
- aiofiles（异步文件操作）
- cryptography（加密）
- fuzzywuzzy（模糊匹配）

## 16. 测试策略

### 16.1 单元测试
- DownloadService方法测试
- API接口测试
- 数据库操作测试

### 16.2 集成测试
- 端到端下载流程测试
- 错误处理测试
- 并发下载测试

### 16.3 性能测试
- 并发下载性能测试
- 大文件下载测试
- 内存使用测试

## 17. 监控和日志

### 17.1 监控指标
- 下载成功率
- 平均下载时间
- 队列长度
- API调用频率

### 17.2 日志记录
- 下载开始/完成日志
- 错误详情记录
- 性能指标记录
- 用户操作日志

## 18. 部署和运维

### 18.1 环境配置
- 下载路径配置
- API Key管理
- 并发限制设置
- 日志级别配置

### 18.2 备份策略
- 下载设置备份
- 下载历史备份
- 文件存储备份

### 18.3 监控告警
- 下载失败告警
- 磁盘空间告警
- API配额告警

---

**文档版本**：v1.0  
**最后更新**：2024年12月  
**维护者**：开发团队
