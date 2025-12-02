#!/usr/bin/env python3
"""
商品变更检测工具

比较当前商品数据与历史数据，识别新增、修改、删除的商品。
用于增量测试，仅对变更的商品执行 E2E 测试。
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
import argparse


class ProductChangeDetector:
    """商品变更检测器"""

    def __init__(
        self,
        current_products_file: str = "data/products.json",
        history_dir: str = "data/history",
        changes_file: str = "data/product_changes.json"
    ):
        """
        初始化变更检测器

        Args:
            current_products_file: 当前商品数据文件
            history_dir: 历史数据目录
            changes_file: 变更结果输出文件
        """
        self.current_products_file = Path(current_products_file)
        self.history_dir = Path(history_dir)
        self.changes_file = Path(changes_file)

        # 确保历史目录存在
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _load_products(self, file_path: Path) -> Dict[str, Dict]:
        """
        加载商品数据

        Args:
            file_path: 商品数据文件路径

        Returns:
            商品字典，key 为商品 ID
        """
        if not file_path.exists():
            return {}

        with open(file_path) as f:
            products_list = json.load(f)

        # 转换为字典，以 ID 为 key
        products_dict = {}
        for product in products_list:
            product_id = product.get('id') or product.get('url', '').split('/')[-1]
            products_dict[product_id] = product

        return products_dict

    def _get_latest_history_file(self) -> Path | None:
        """
        获取最新的历史数据文件

        Returns:
            最新历史文件路径，如果不存在返回 None
        """
        history_files = sorted(self.history_dir.glob("products_*.json"), reverse=True)
        return history_files[0] if history_files else None

    def _calculate_product_hash(self, product: Dict) -> str:
        """
        计算商品数据的哈希值

        用于检测商品内容是否发生变化。
        只包含关键字段，忽略不重要的元数据。

        Args:
            product: 商品数据

        Returns:
            SHA256 哈希值
        """
        # 提取关键字段
        key_fields = {
            'name': product.get('name', ''),
            'price_min': product.get('price_min', 0),
            'price_max': product.get('price_max', 0),
            'variants': product.get('variants', []),
            'selectors': product.get('selectors', {}),
            'available': product.get('metadata', {}).get('available', True)
        }

        # 转换为规范化的 JSON 字符串
        normalized_json = json.dumps(key_fields, sort_keys=True)

        # 计算 SHA256 哈希
        return hashlib.sha256(normalized_json.encode()).hexdigest()

    def detect_changes(self) -> Dict:
        """
        检测商品变更

        Returns:
            变更报告，包含新增、修改、删除的商品列表
        """
        # 加载当前商品数据
        current_products = self._load_products(self.current_products_file)

        # 加载历史商品数据
        latest_history_file = self._get_latest_history_file()
        if latest_history_file:
            history_products = self._load_products(latest_history_file)
        else:
            # 如果没有历史数据，所有商品都是新增
            print("⚠️ 未找到历史数据，所有商品将被视为新增")
            history_products = {}

        # 计算变更
        current_ids = set(current_products.keys())
        history_ids = set(history_products.keys())

        # 1. 新增的商品
        added_ids = current_ids - history_ids
        added_products = [
            {
                'id': pid,
                'name': current_products[pid].get('name', ''),
                'url': current_products[pid].get('url', ''),
                'reason': 'new_product'
            }
            for pid in added_ids
        ]

        # 2. 删除的商品
        removed_ids = history_ids - current_ids
        removed_products = [
            {
                'id': pid,
                'name': history_products[pid].get('name', ''),
                'url': history_products[pid].get('url', ''),
                'reason': 'removed_product'
            }
            for pid in removed_ids
        ]

        # 3. 修改的商品（内容发生变化）
        modified_products = []
        for pid in current_ids & history_ids:
            current_hash = self._calculate_product_hash(current_products[pid])
            history_hash = self._calculate_product_hash(history_products[pid])

            if current_hash != history_hash:
                # 分析具体变更原因
                reason = self._analyze_modification(
                    current_products[pid],
                    history_products[pid]
                )

                modified_products.append({
                    'id': pid,
                    'name': current_products[pid].get('name', ''),
                    'url': current_products[pid].get('url', ''),
                    'reason': reason,
                    'changes': self._get_field_changes(
                        current_products[pid],
                        history_products[pid]
                    )
                })

        # 生成变更报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'current_products_file': str(self.current_products_file),
            'history_file': str(latest_history_file) if latest_history_file else None,
            'summary': {
                'total_current': len(current_products),
                'total_history': len(history_products),
                'added': len(added_products),
                'removed': len(removed_products),
                'modified': len(modified_products),
                'unchanged': len(current_ids & history_ids) - len(modified_products)
            },
            'changes': {
                'added': added_products,
                'removed': removed_products,
                'modified': modified_products
            },
            'test_targets': self._generate_test_targets(
                added_products,
                modified_products
            )
        }

        return report

    def _analyze_modification(self, current: Dict, history: Dict) -> str:
        """
        分析商品修改的具体原因

        Args:
            current: 当前商品数据
            history: 历史商品数据

        Returns:
            修改原因描述
        """
        reasons = []

        # 价格变化
        if (current.get('price_min') != history.get('price_min') or
            current.get('price_max') != history.get('price_max')):
            reasons.append('price_changed')

        # 名称变化
        if current.get('name') != history.get('name'):
            reasons.append('name_changed')

        # 变体变化
        current_variants = len(current.get('variants', []))
        history_variants = len(history.get('variants', []))
        if current_variants != history_variants:
            reasons.append('variants_changed')

        # 可用性变化
        current_available = current.get('metadata', {}).get('available', True)
        history_available = history.get('metadata', {}).get('available', True)
        if current_available != history_available:
            reasons.append('availability_changed')

        # 选择器变化
        if current.get('selectors') != history.get('selectors'):
            reasons.append('selectors_changed')

        return ', '.join(reasons) if reasons else 'content_changed'

    def _get_field_changes(self, current: Dict, history: Dict) -> Dict:
        """
        获取字段级别的变更详情

        Args:
            current: 当前商品数据
            history: 历史商品数据

        Returns:
            字段变更字典
        """
        changes = {}

        # 价格变化
        if current.get('price_min') != history.get('price_min'):
            changes['price_min'] = {
                'old': history.get('price_min'),
                'new': current.get('price_min')
            }

        if current.get('price_max') != history.get('price_max'):
            changes['price_max'] = {
                'old': history.get('price_max'),
                'new': current.get('price_max')
            }

        # 名称变化
        if current.get('name') != history.get('name'):
            changes['name'] = {
                'old': history.get('name'),
                'new': current.get('name')
            }

        # 变体数量变化
        current_variants = len(current.get('variants', []))
        history_variants = len(history.get('variants', []))
        if current_variants != history_variants:
            changes['variants_count'] = {
                'old': history_variants,
                'new': current_variants
            }

        return changes

    def _generate_test_targets(
        self,
        added_products: List[Dict],
        modified_products: List[Dict]
    ) -> List[Dict]:
        """
        生成测试目标列表

        仅包含需要测试的商品（新增 + 修改）

        Args:
            added_products: 新增商品列表
            modified_products: 修改商品列表

        Returns:
            测试目标列表，包含商品 ID 和测试原因
        """
        test_targets = []

        # 新增商品（高优先级）
        for product in added_products:
            test_targets.append({
                'id': product['id'],
                'url': product['url'],
                'reason': 'new_product',
                'priority': 'P0'
            })

        # 修改商品（根据修改原因确定优先级）
        for product in modified_products:
            reason = product['reason']

            # 高优先级变更：价格、可用性、选择器
            if any(keyword in reason for keyword in ['price', 'availability', 'selectors']):
                priority = 'P0'
            # 中优先级变更：变体、名称
            elif any(keyword in reason for keyword in ['variants', 'name']):
                priority = 'P1'
            # 低优先级变更：其他内容变更
            else:
                priority = 'P2'

            test_targets.append({
                'id': product['id'],
                'url': product['url'],
                'reason': reason,
                'priority': priority,
                'changes': product.get('changes', {})
            })

        # 按优先级排序
        priority_order = {'P0': 0, 'P1': 1, 'P2': 2}
        test_targets.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return test_targets

    def save_changes(self, report: Dict):
        """
        保存变更报告

        Args:
            report: 变更报告
        """
        with open(self.changes_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"💾 变更报告已保存: {self.changes_file}")

    def save_current_as_history(self):
        """
        将当前商品数据保存为历史记录

        用于下次比对
        """
        if not self.current_products_file.exists():
            print(f"❌ 当前商品数据文件不存在: {self.current_products_file}")
            return

        # 生成历史文件名（带时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        history_file = self.history_dir / f"products_{timestamp}.json"

        # 复制当前数据到历史目录
        with open(self.current_products_file) as f:
            data = json.load(f)

        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"📁 当前数据已保存为历史记录: {history_file}")

        # 清理旧的历史文件（保留最近 30 个）
        self._cleanup_old_history(keep=30)

    def _cleanup_old_history(self, keep: int = 30):
        """
        清理旧的历史文件

        Args:
            keep: 保留最近 N 个历史文件
        """
        history_files = sorted(self.history_dir.glob("products_*.json"), reverse=True)

        if len(history_files) > keep:
            for old_file in history_files[keep:]:
                old_file.unlink()
                print(f"🗑️ 已删除旧历史文件: {old_file.name}")

    def print_report(self, report: Dict):
        """
        打印变更报告

        Args:
            report: 变更报告
        """
        print("\n📊 商品变更检测报告")
        print("=" * 60)

        # 摘要
        summary = report['summary']
        print(f"\n📈 摘要:")
        print(f"  当前商品数: {summary['total_current']}")
        print(f"  历史商品数: {summary['total_history']}")
        print(f"  新增商品: {summary['added']}")
        print(f"  删除商品: {summary['removed']}")
        print(f"  修改商品: {summary['modified']}")
        print(f"  未变更: {summary['unchanged']}")

        # 新增商品
        if report['changes']['added']:
            print(f"\n✨ 新增商品 ({len(report['changes']['added'])} 个):")
            for product in report['changes']['added'][:10]:
                print(f"  - {product['name']} ({product['id']})")
            if len(report['changes']['added']) > 10:
                print(f"  ... 还有 {len(report['changes']['added']) - 10} 个")

        # 修改商品
        if report['changes']['modified']:
            print(f"\n🔄 修改商品 ({len(report['changes']['modified'])} 个):")
            for product in report['changes']['modified'][:10]:
                print(f"  - {product['name']} ({product['id']})")
                print(f"    原因: {product['reason']}")
                if product.get('changes'):
                    for field, change in product['changes'].items():
                        print(f"    {field}: {change['old']} → {change['new']}")
            if len(report['changes']['modified']) > 10:
                print(f"  ... 还有 {len(report['changes']['modified']) - 10} 个")

        # 测试目标
        test_targets = report['test_targets']
        if test_targets:
            print(f"\n🎯 需要测试的商品 ({len(test_targets)} 个):")

            # 按优先级分组
            p0_targets = [t for t in test_targets if t['priority'] == 'P0']
            p1_targets = [t for t in test_targets if t['priority'] == 'P1']
            p2_targets = [t for t in test_targets if t['priority'] == 'P2']

            if p0_targets:
                print(f"  🔴 P0 (高优先级): {len(p0_targets)} 个")
                for target in p0_targets[:5]:
                    print(f"    - {target['id']}: {target['reason']}")

            if p1_targets:
                print(f"  🟡 P1 (中优先级): {len(p1_targets)} 个")

            if p2_targets:
                print(f"  🟢 P2 (低优先级): {len(p2_targets)} 个")
        else:
            print("\n✅ 无需测试，所有商品未变更")

        print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='商品变更检测')
    parser.add_argument(
        '--current',
        default='data/products.json',
        help='当前商品数据文件'
    )
    parser.add_argument(
        '--history-dir',
        default='data/history',
        help='历史数据目录'
    )
    parser.add_argument(
        '--output',
        default='data/product_changes.json',
        help='变更报告输出文件'
    )
    parser.add_argument(
        '--save-history',
        action='store_true',
        help='将当前数据保存为历史记录'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='输出 JSON 格式'
    )

    args = parser.parse_args()

    detector = ProductChangeDetector(
        current_products_file=args.current,
        history_dir=args.history_dir,
        changes_file=args.output
    )

    # 检测变更
    report = detector.detect_changes()

    # 保存报告
    detector.save_changes(report)

    # 打印报告
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        detector.print_report(report)

    # 保存当前数据为历史记录
    if args.save_history:
        detector.save_current_as_history()


if __name__ == '__main__':
    main()
