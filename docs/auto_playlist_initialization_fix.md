# AutoPlaylistService 初始化修复

## 问题描述
在之前的版本中，AutoPlaylistService在应用启动时不会自动初始化，导致在处理新内容时可能会出现初始化失败的问题。

## 修复方案
1. 在SyncService中添加了`initialize_auto_playlist_service`方法，用于在应用启动时初始化AutoPlaylistService。
2. 在main.py的lifespan函数中调用该方法，确保AutoPlaylistService在应用启动时就能正确初始化。

## 验证
通过运行测试脚本验证了AutoPlaylistService能够成功初始化，并且应用能够正常启动。