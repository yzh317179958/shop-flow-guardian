"""
商品爬虫缓存模块

提供商品数据缓存功能，避免重复爬取，提升性能。
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CrawlerCache:
    """爬虫缓存管理器"""

    def __init__(
        self,
        cache_dir: str = "data/cache",
        ttl_hours: int = 24
    ):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存有效期（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict:
        """加载缓存元数据"""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {}

    def _save_metadata(self):
        """保存缓存元数据"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _get_cache_key(self, url: str) -> str:
        """
        生成缓存键

        Args:
            url: 商品 URL

        Returns:
            缓存键（URL 的 MD5 哈希）
        """
        return hashlib.md5(url.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"

    def _is_expired(self, cache_key: str) -> bool:
        """
        检查缓存是否过期

        Args:
            cache_key: 缓存键

        Returns:
            是否过期
        """
        if cache_key not in self.metadata:
            return True

        cached_time = datetime.fromisoformat(
            self.metadata[cache_key]['cached_at']
        )
        return datetime.now() - cached_time > self.ttl

    def get(self, url: str) -> Optional[Dict[str, Any]]:
        """
        从缓存获取数据

        Args:
            url: 商品 URL

        Returns:
            缓存的商品数据，如果不存在或已过期则返回 None
        """
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        # 检查缓存是否存在且未过期
        if not cache_path.exists() or self._is_expired(cache_key):
            return None

        # 读取缓存数据
        try:
            with open(cache_path) as f:
                data = json.load(f)

            # 更新访问时间
            self.metadata[cache_key]['last_accessed'] = datetime.now().isoformat()
            self._save_metadata()

            print(f"✅ 缓存命中: {url}")
            return data

        except Exception as e:
            print(f"⚠️ 读取缓存失败: {e}")
            return None

    def set(self, url: str, data: Dict[str, Any]):
        """
        保存数据到缓存

        Args:
            url: 商品 URL
            data: 商品数据
        """
        cache_key = self._get_cache_key(url)
        cache_path = self._get_cache_path(cache_key)

        # 保存数据
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # 更新元数据
            self.metadata[cache_key] = {
                'url': url,
                'cached_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'size_bytes': cache_path.stat().st_size
            }
            self._save_metadata()

            print(f"💾 已缓存: {url}")

        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")

    def clear(self, url: Optional[str] = None):
        """
        清除缓存

        Args:
            url: 如果指定，仅清除该 URL 的缓存；否则清除所有缓存
        """
        if url:
            # 清除单个缓存
            cache_key = self._get_cache_key(url)
            cache_path = self._get_cache_path(cache_key)

            if cache_path.exists():
                cache_path.unlink()

            if cache_key in self.metadata:
                del self.metadata[cache_key]
                self._save_metadata()

            print(f"🗑️ 已清除缓存: {url}")

        else:
            # 清除所有缓存
            for cache_file in self.cache_dir.glob("*.json"):
                if cache_file.name != "cache_metadata.json":
                    cache_file.unlink()

            self.metadata = {}
            self._save_metadata()

            print("🗑️ 已清除所有缓存")

    def cleanup_expired(self):
        """清理过期的缓存"""
        expired_keys = []

        for cache_key in list(self.metadata.keys()):
            if self._is_expired(cache_key):
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    cache_path.unlink()
                expired_keys.append(cache_key)

        for key in expired_keys:
            del self.metadata[key]

        if expired_keys:
            self._save_metadata()
            print(f"🗑️ 已清理 {len(expired_keys)} 个过期缓存")

    def get_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        total_size = sum(
            meta.get('size_bytes', 0)
            for meta in self.metadata.values()
        )

        expired_count = sum(
            1 for key in self.metadata.keys()
            if self._is_expired(key)
        )

        return {
            'total_items': len(self.metadata),
            'total_size_mb': total_size / (1024 * 1024),
            'expired_items': expired_count,
            'valid_items': len(self.metadata) - expired_count,
            'cache_dir': str(self.cache_dir),
            'ttl_hours': self.ttl.total_seconds() / 3600
        }

    def print_stats(self):
        """打印缓存统计信息"""
        stats = self.get_stats()

        print("\n📊 缓存统计:")
        print(f"  总缓存项: {stats['total_items']}")
        print(f"  有效缓存: {stats['valid_items']}")
        print(f"  过期缓存: {stats['expired_items']}")
        print(f"  总大小: {stats['total_size_mb']:.2f} MB")
        print(f"  有效期: {stats['ttl_hours']} 小时")
        print(f"  缓存目录: {stats['cache_dir']}")
