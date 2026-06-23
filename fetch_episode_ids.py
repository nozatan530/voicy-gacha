#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voicy エピソードの数値ID取得スクリプト
==========================================

各エピソードページから、Voicy埋め込みURL（/embed/）で使われる数値IDを
取得します。1回だけ実行すれば、ガチャの埋め込みプレイヤーが動くようになります。

【前提】
  - convert.py で先に episodes.json を生成しておくこと
  - requests ライブラリが必要：
      pip install requests

【使い方】
    python3 fetch_episode_ids.py

  → 既存の episodes.json に各エピソードの数値ID（embed_id）を追記して
    上書き保存します。1300件で20〜30分程度かかります。

【途中で中断した場合】
  再実行すれば、既に embed_id が取得済みのエピソードはスキップして
  続きから再開します。

【サーバー負荷への配慮】
  リクエスト間に SLEEP_SECONDS の待機を入れています。短くしすぎると
  Voicy側に負荷をかけることになるので、0.5秒以上を推奨します。
"""

import json
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests ライブラリが必要です。以下のコマンドでインストールしてください：")
    print("  pip install requests")
    sys.exit(1)


# ===========================================================
# 設定
# ===========================================================
JSON_PATH = Path(__file__).parent / 'episodes.json'
SLEEP_SECONDS = 0.6                # リクエスト間の待機秒数
TIMEOUT = 15                       # リクエストのタイムアウト秒数
USER_AGENT = 'Mozilla/5.0 (Voicy Gacha Setup Script)'
SAVE_EVERY = 20                    # 何件ごとにJSONを保存するか（中断時の保険）


def extract_numeric_id(html, fallback_url):
    """
    HTMLから数値IDを抽出する。
    canonical URL（meta tag）と og:url の両方を探す。
    """
    # canonical: <link rel="canonical" href="https://voicy.jp/channel/3708/732961">
    m = re.search(
        r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if m:
        nid = extract_id_from_url(m.group(1))
        if nid:
            return nid

    # og:url: <meta property="og:url" content="https://voicy.jp/channel/3708/732961">
    m = re.search(
        r'<meta[^>]*property=["\']og:url["\'][^>]*content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    if m:
        nid = extract_id_from_url(m.group(1))
        if nid:
            return nid

    # og:image: https://ogp-image.voicy.jp/ogp-image/story/0/3708/732961
    m = re.search(
        r'ogp-image\.voicy\.jp/ogp-image/story/\d+/\d+/(\d+)',
        html
    )
    if m:
        return m.group(1)

    return None


def extract_id_from_url(url):
    """URLパスから数値IDを抽出（最後のパスセグメントが数字なら）"""
    m = re.search(r'/channel/\d+/(\d+)(?:[/?#]|$)', url)
    return m.group(1) if m else None


def fetch_one(url, session):
    """1ページfetchして数値IDを返す"""
    try:
        r = session.get(url, timeout=TIMEOUT)
        if r.status_code != 200:
            return None, f'HTTP {r.status_code}'
        nid = extract_numeric_id(r.text, url)
        if not nid:
            return None, 'ID not found in HTML'
        return nid, None
    except Exception as e:
        return None, str(e)


def main():
    if not JSON_PATH.exists():
        print(f"エラー: {JSON_PATH} が見つかりません")
        print("先に convert.py を実行して episodes.json を作成してください")
        sys.exit(1)

    with JSON_PATH.open('r', encoding='utf-8') as f:
        episodes = json.load(f)

    # すでに embed_id を持っているものはスキップ
    todo = [(i, ep) for i, ep in enumerate(episodes)
            if not ep.get('embed_id') and ep.get('u')]
    already_done = len(episodes) - len(todo)

    print(f"全 {len(episodes)} 件のうち、")
    print(f"  取得済み: {already_done} 件")
    print(f"  取得対象: {len(todo)} 件")
    print(f"予想所要時間: 約 {len(todo) * (SLEEP_SECONDS + 1) / 60:.1f} 分")
    print()

    if len(todo) == 0:
        print("すべて取得済みです。")
        return

    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT})

    success = 0
    failed = 0
    failed_urls = []

    for n, (i, ep) in enumerate(todo, 1):
        nid, err = fetch_one(ep['u'], session)
        if nid:
            episodes[i]['embed_id'] = nid
            success += 1
            status = f"✓ {nid}"
        else:
            failed += 1
            failed_urls.append((ep['u'], err))
            status = f"✗ {err}"

        # 進捗表示（毎回）
        print(f"[{n:>4}/{len(todo)}] {status:<40} | {ep['t'][:50]}")

        # 定期保存
        if n % SAVE_EVERY == 0:
            with JSON_PATH.open('w', encoding='utf-8') as f:
                json.dump(episodes, f, ensure_ascii=False, separators=(',', ':'))

        time.sleep(SLEEP_SECONDS)

    # 最終保存
    with JSON_PATH.open('w', encoding='utf-8') as f:
        json.dump(episodes, f, ensure_ascii=False, separators=(',', ':'))

    print()
    print(f"完了: {success} 成功 / {failed} 失敗")
    if failed:
        print("\n失敗したエピソード（5件まで表示）:")
        for url, err in failed_urls[:5]:
            print(f"  {err}: {url}")
        print(f"\n再実行すれば、失敗したものだけ再試行されます。")


if __name__ == '__main__':
    main()
