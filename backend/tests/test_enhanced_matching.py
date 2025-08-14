import unittest
import json
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
import logging

# 添加 backend 目录到 Python 路径，以便导入 PlexService
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.plex_service import PlexService, Track, MusicSection

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestEnhancedMatching(unittest.TestCase):
    """测试增强版匹配策略"""

    def setUp(self):
        """初始化测试环境"""
        # 读取未匹配的歌曲列表
        unmatched_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'unmatched.json')
        with open(unmatched_file_path, 'r', encoding='utf-8') as f:
            self.unmatched_data = json.load(f)
        self.unmatched_songs: List[Dict[str, Any]] = self.unmatched_data.get('unmatched_songs', [])

        # 从环境变量获取 Plex 配置
        self.plex_url = os.getenv('PLEX_URL')
        self.plex_token = os.getenv('PLEX_TOKEN')
        self.verify_ssl = os.getenv('PLEX_VERIFY_SSL', 'true').lower() == 'true'

        if not self.plex_url or not self.plex_token:
            self.skipTest("PLEX_URL 或 PLEX_TOKEN 未设置，跳过需要 Plex 连接的测试。")

        try:
            # 初始化 PlexService
            self.plex_service = PlexService(self.plex_url, self.plex_token, self.verify_ssl)
            # 获取音乐库
            self.library: Optional[MusicSection] = self.plex_service._get_music_library_sync()
            if not self.library:
                self.skipTest("无法获取 Plex 音乐库，跳过测试。")
        except Exception as e:
            self.skipTest(f"Plex 初始化失败: {e}")

    def test_find_track_with_enhanced_strategy(self):
        """针对 unmatched.json 中的歌曲，测试增强版匹配策略"""
        
        # 收集分析结果
        analysis_results = []

        # 分析所有未匹配的歌曲
        total_songs = len(self.unmatched_songs)
        matched_songs = 0
        
        for i, song in enumerate(self.unmatched_songs):
            title = song['title']
            artist = song['artist']
            album = song['album']
            
            logger.info(f"[{i+1}/{total_songs}] 正在匹配: '{title}' by '{artist}'")
            
            # 调用被测试的方法
            try:
                track, score = self.plex_service._find_track_with_score_sync(title, artist, album, self.library)
            except Exception as e:
                logger.error(f"匹配过程中出错: {e}", exc_info=True)
                track, score = None, 0
            
            # 记录分析结果
            result = {
                'title': title,
                'artist': artist,
                'album': album,
                'matched': track is not None,
                'match_score': score,
                'matched_title': track.title if track else None,
                'matched_artist': track.grandparentTitle if track else None,
                'matched_album': track.parentTitle if track else None,
            }
            analysis_results.append(result)
            
            if track:
                matched_songs += 1
                logger.info(f"  -> 匹配成功: '{track.title}' by '{track.grandparentTitle}' (分数: {score})")
            else:
                logger.info(f"  -> 匹配失败")
        
        # 打印汇总分析
        logger.info(f"\n--- 匹配结果汇总 ---")
        logger.info(f"总歌曲数: {total_songs}")
        logger.info(f"匹配成功数: {matched_songs}")
        logger.info(f"匹配成功率: {matched_songs/total_songs*100:.2f}%")

        # 分析未匹配歌曲的艺术家特征
        unmatched_results = [r for r in analysis_results if not r['matched']]
        multi_artist_count = 0
        for r in unmatched_results:
            original_artist = r['artist']
            # 简单判断是否为多艺术家（包含逗号或常见连接词）
            if ',' in original_artist or '和' in original_artist or '&' in original_artist:
                multi_artist_count += 1
        
        logger.info(f"\n--- 未匹配歌曲艺术家分析 ---")
        logger.info(f"未匹配歌曲数: {len(unmatched_results)}")
        logger.info(f"其中疑似多艺术家歌曲数: {multi_artist_count}")
        if len(unmatched_results) > 0:
            logger.info(f"多艺术家歌曲占比: {multi_artist_count/len(unmatched_results)*100:.2f}% (如果高，说明这是一个关键问题)")
        else:
            logger.info("未匹配歌曲数为 0，无法计算多艺术家歌曲占比。")

        # 将详细结果保存到文件，供进一步分析
        output_file = os.path.join(os.path.dirname(__file__), 'enhanced_matching_analysis_output.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=4)
        logger.info(f"\n详细分析结果已保存到: {output_file}")

        # 基于分析提出初步结论
        self._generate_conclusion(matched_songs, total_songs, multi_artist_count, len(unmatched_results))

    def _generate_conclusion(self, matched_count, total_count, multi_artist_unmatched_count, total_unmatched_count):
        """根据分析结果生成结论"""
        logger.info(f"\n--- 测试结论 ---")
        match_rate = matched_count / total_count if total_count > 0 else 0
        multi_artist_rate = multi_artist_unmatched_count / total_unmatched_count if total_unmatched_count > 0 else 0

        if match_rate > 0.7:
            logger.info("1. 增强版匹配策略效果显著，匹配成功率较高。")
        elif match_rate > 0.5:
            logger.info("1. 增强版匹配策略有一定效果，匹配成功率尚可。")
        else:
            logger.info("1. 增强版匹配策略效果有限，匹配成功率较低，需要进一步优化。")

        if multi_artist_rate > 0.5:
            logger.info("2. 大量未匹配歌曲是多艺术家歌曲，这表明多艺术家处理仍是关键优化点。")
        else:
            logger.info("2. 多艺术家问题不是主要瓶颈。")

        logger.info("3. 建议根据详细分析结果，针对匹配失败的歌曲进行个案分析，找出具体原因。")
        logger.info("4. 可以调整评分阈值或权重，进一步优化匹配效果。")


if __name__ == '__main__':
    # 设置标准输出编码为UTF-8，以正确显示Unicode字符
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    unittest.main()