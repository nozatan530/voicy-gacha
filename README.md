# Voicy アーカイブガチャ

Voicyの過去放送をガチャで掘り起こす遊び場ツールです。
パーソナリティの皆さんが自分のチャンネルでも動かせる構成になっています。

---

## このセットの中身

| ファイル | 役割 |
|---|---|
| `gacha.html` | ガチャ本体（外部JSON読み込み版） |
| `gacha-standalone.html` | ガチャ本体（JSON埋め込み済み、1ファイル完結版） |
| `episodes.json` | 放送データ（変換後の状態） |
| `convert.py` | Voicyアナリティクス CSV → JSON への変換スクリプト |
| `fetch_episode_ids.py` | 埋め込み用の数値ID取得スクリプト（**1回だけ実行**） |
| `README.md` | この手順書 |

---

## セットアップの流れ（自分のチャンネル用にする）

### ステップ1：CSV → JSON 変換

Voicyのパーソナリティ管理画面 → アナリティクス → 放送 → 全期間のCSVを出力。

```bash
python3 convert.py アナリティクス_放送__全期間.csv
```

`episodes.json` が生成されます。

### ステップ2：埋め込み用の数値IDを取得（初回のみ・20〜30分）

Voicyの埋め込みプレイヤー（iframe）はエピソードごとの数値IDが必要ですが、
CSVには含まれていません。このスクリプトで各エピソードページから自動取得します。

```bash
pip install requests
python3 fetch_episode_ids.py
```

1300件で約20〜30分かかります。途中で中断しても、再実行すれば続きから再開します。
完了すると `episodes.json` に各エピソードの `embed_id` が追加されます。

**新しい放送が増えた時の運用**：
1. 新CSVをダウンロードして `convert.py` を実行（embed_id以外を更新）
2. `fetch_episode_ids.py` を再実行（新しいエピソード分のみ取得される）

### ステップ3：HTMLのCONFIGを編集

HTMLの後半、`<script>` の中に `CONFIG` という設定オブジェクトがあります。
最低限、以下の3か所だけ変えれば自分のチャンネル用になります：

```javascript
const CONFIG = {
  dataUrl: './episodes.json',     // そのままでOK

  rarityWeights: {                 // 出現確率（合計100で調整）
    SSR: 5,
    SR: 15,
    R: 30,
    N: 50,
  },

  rarityLabels: {                  // 自分のチャンネル向けに文言変更可
    SSR: 'プレミアム回',
    SR: '神回',
    R: '良回',
    N: '日常回',
  },

  shareTextTemplate: (rarity, title) =>
    `〇〇ガチャを引いたら ${rarity} が出ました！\n「${title}」`,
                                   // ↑ 自分の番組名に書き換え
  shareHashtag: '〇〇ガチャ',      // ↑ ハッシュタグも
};
```

さらに、HTMLの上の方にあるタイトル・サブタイトル・footerの番組名・
Voicyチャンネル番号も自分用に書き換えてください（検索置換で5分）。

### ステップ4：アップロードして公開

以下のいずれかで公開できます：

- WordPressの固定ページに「カスタムHTML」ブロックとして `gacha.html` の中身を貼り、
  `episodes.json` はメディアライブラリにアップロードして CONFIG の dataUrl に
  そのURLを指定
- GitHub PagesやNetlifyに2ファイルまとめて配置
- 自分のサイトの任意のディレクトリに2ファイルを置く

---

## レア度の判定ロジック

`convert.py` 内の `RARITY_CONFIG` で調整できます：

| レア度 | 条件 | 想定 |
|---|---|---|
| SSR | プレミアム放送・有料放送 | アーカイブの宝。プレミアム会員導線 |
| SR  | レギュラー放送 × いいね15以上 | 神回 |
| R   | レギュラー放送 × いいね10〜14 | 良回 |
| N   | それ以外のレギュラー放送 | 日常回（これも味） |

チャンネル規模が小さい場合や大きい場合は、`sr_likes_threshold` と
`r_likes_threshold` を調整してください。

---

## 新しい放送が追加されたら

1. Voicyから最新CSVをダウンロード
2. `python3 convert.py 新しいCSV.csv`
3. `python3 fetch_episode_ids.py`（新規分の数値IDのみ取得：数十秒〜数分）
4. 新しい `episodes.json` を配置先にアップロードして上書き

これだけで反映されます。HTMLは触る必要なし。

---

## ライセンス

自由に改変・転用してください。クレジット表記も不要です。
ただし、Voicyの利用規約は各自で遵守してください。
