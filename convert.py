#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voicy アナリティクスCSV → ガチャ用JSON 変換スクリプト
========================================================

使い方:
    python3 convert.py アナリティクス_放送__全期間.csv

  → 同じディレクトリに episodes.json が生成されます。

新しい放送を追加するときは:
  1. Voicy管理画面から最新のアナリティクスCSVをダウンロード
  2. このスクリプトを再実行
  3. 生成された episodes.json を差し替える

他のVoicyパーソナリティが使う場合も、CSVのフォーマットさえ同じなら
そのまま使えます。レア度判定の閾値は、各チャンネルの規模に合わせて
下の RARITY_CONFIG を調整してください。
"""

import csv
import json
import sys
from pathlib import Path

# ===========================================================
# レア度判定の設定（チャンネル規模に応じて調整可）
# ===========================================================
RARITY_CONFIG = {
    # プレミアム放送・有料放送は無条件でSSR
    'premium_options': [
        'プレミアム放送(バックナンバー)',
        'プレミアム放送(当月分)',
        '有料放送',
    ],
    # レギュラー放送のいいね数による分類閾値
    'sr_likes_threshold': 15,   # これ以上いいねがあればSR（神回）
    'r_likes_threshold': 10,    # これ以上いいねがあればR（良回）
                                 # それ未満はN（日常回）
}


def determine_rarity(row):
    """1放送のレア度を判定"""
    option = row.get('公開オプション', '')

    if option in RARITY_CONFIG['premium_options']:
        return 'SSR'

    try:
        likes = int(row.get('いいね', 0))
    except (ValueError, TypeError):
        likes = 0

    if likes >= RARITY_CONFIG['sr_likes_threshold']:
        return 'SR'
    if likes >= RARITY_CONFIG['r_likes_threshold']:
        return 'R'
    return 'N'


def convert(csv_path: Path, json_path: Path):
    with csv_path.open('r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    episodes = []
    for row in rows:
        try:
            likes = int(row.get('いいね', 0))
        except (ValueError, TypeError):
            likes = 0

        episodes.append({
            'd': row.get('放送日', ''),         # 放送日
            't': row.get('放送タイトル', ''),   # タイトル
            'u': row.get('放送URL', ''),        # URL
            'l': likes,                          # いいね数
            'o': row.get('公開オプション', ''), # 公開オプション
            'r': determine_rarity(row),          # レア度
            'len': row.get('放送尺', ''),       # 放送尺
        })

    # 件数サマリーを表示
    counts = {'SSR': 0, 'SR': 0, 'R': 0, 'N': 0}
    for ep in episodes:
        counts[ep['r']] = counts.get(ep['r'], 0) + 1

    total = len(episodes)
    print(f"変換完了: {total}件")
    print(f"  SSR (プレミアム):  {counts['SSR']:>4}件 ({counts['SSR']/total*100:.1f}%)")
    print(f"  SR  (神回):       {counts['SR']:>4}件 ({counts['SR']/total*100:.1f}%)")
    print(f"  R   (良回):       {counts['R']:>4}件 ({counts['R']/total*100:.1f}%)")
    print(f"  N   (日常回):     {counts['N']:>4}件 ({counts['N']/total*100:.1f}%)")

    with json_path.open('w', encoding='utf-8') as f:
        json.dump(episodes, f, ensure_ascii=False, separators=(',', ':'))
    print(f"\n出力: {json_path}")


def main():
    if len(sys.argv) < 2:
        print("使い方: python3 convert.py アナリティクス_放送__全期間.csv")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"エラー: {csv_path} が見つかりません")
        sys.exit(1)

    json_path = csv_path.parent / 'episodes.json'
    convert(csv_path, json_path)


if __name__ == '__main__':
    main()
