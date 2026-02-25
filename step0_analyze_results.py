"""
Step 0: 分析スクリプト
手動判定結果 (step0_judged_YYYY-MM-DD.json) を読み込み、分析レポートを出力する。
"""
import sys
import json
import glob
import os
from collections import Counter

# Windows cp932 対策
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def load_latest_judged():
    """最新の判定結果ファイルを読み込む"""
    files = sorted(glob.glob('step0_judged_*.json'))
    if not files:
        print("[ERROR] step0_judged_*.json が見つかりません。")
        print("  step0_interface.html で判定を行い、エクスポートしてください。")
        sys.exit(1)

    latest = files[-1]
    print(f"[INFO] 読み込み: {latest}")

    with open(latest, 'r', encoding='utf-8') as f:
        return json.load(f), latest


def analyze(data):
    """判定結果を分析"""
    entries = data['entries']
    judged = [e for e in entries if e['judgment']['level'] is not None]
    unjudged = [e for e in entries if e['judgment']['level'] is None]

    print("\n" + "=" * 60)
    print("Step 0: 概念化レベル分析レポート")
    print("=" * 60)

    # 基本統計
    print(f"\n--- 基本統計 ---")
    print(f"  全エントリー: {len(entries)}件")
    print(f"  判定済み: {len(judged)}件")
    print(f"  未判定: {len(unjudged)}件")

    if not judged:
        print("\n[WARN] 判定済みエントリーがありません。")
        return

    # レベル分布
    levels = Counter(e['judgment']['level'] for e in judged)
    print(f"\n--- レベル分布 ---")
    level_names = {1: "Lv.1 事実記述(点)", 2: "Lv.2 文脈理解(線)", 3: "Lv.3 職能一般化(面)"}
    for lv in [1, 2, 3]:
        cnt = levels.get(lv, 0)
        pct = cnt / len(judged) * 100 if judged else 0
        bar = '#' * int(pct / 2)
        print(f"  {level_names[lv]}: {cnt}件 ({pct:.1f}%) {bar}")

    # 自信度分布
    confs = Counter(e['judgment']['confidence'] for e in judged if e['judgment']['confidence'])
    print(f"\n--- 自信度分布 ---")
    conf_names = {1: "迷った", 2: "やや迷った", 3: "確信"}
    for c in [1, 2, 3]:
        cnt = confs.get(c, 0)
        print(f"  {c} ({conf_names.get(c, '?')}): {cnt}件")

    # Concept Source 分布と Level × Source クロス集計
    sources = Counter(e['judgment'].get('concept_source', 'UNKNOWN') for e in judged)
    print(f"\n--- Concept Source (概念の主体) 分布 ---")
    for s in ["SELF", "ECHO", "MIXED", "UNKNOWN"]:
        cnt = sources.get(s, 0)
        if cnt > 0 or s != "UNKNOWN":
            print(f"  {s}: {cnt}件")
            
    print(f"\n--- Level × Concept Source クロス集計 ---")
    crosstab = {1: {"SELF": 0, "ECHO": 0, "MIXED": 0, "UNKNOWN": 0},
                2: {"SELF": 0, "ECHO": 0, "MIXED": 0, "UNKNOWN": 0},
                3: {"SELF": 0, "ECHO": 0, "MIXED": 0, "UNKNOWN": 0},
                "Total": {"SELF": 0, "ECHO": 0, "MIXED": 0, "UNKNOWN": 0}}
    
    for e in judged:
        lv = e['judgment']['level']
        src = e['judgment'].get('concept_source', 'UNKNOWN')
        if lv in crosstab:
            crosstab[lv][src] += 1
            crosstab["Total"][src] += 1
            
    print(f"        SELF  ECHO  MIXED  UNKNOWN  合計")
    for lv in [1, 2, 3]:
        row = crosstab[lv]
        total = sum(row.values())
        print(f"Level {lv}   {row['SELF']:<4}  {row['ECHO']:<4}  {row['MIXED']:<5}  {row['UNKNOWN']:<7}  {total}")
    row = crosstab['Total']
    total = sum(row.values())
    print(f"合計      {row['SELF']:<4}  {row['ECHO']:<4}  {row['MIXED']:<5}  {row['UNKNOWN']:<7}  {total}")

    lv3_self = crosstab[3]["SELF"]
    lv3_echo = crosstab[3]["ECHO"]
    if crosstab[3]["SELF"] + crosstab[3]["ECHO"] + crosstab[3]["MIXED"] > 0:
        print(f"\n  [Level 3 の内訳]")
        print(f"    - SELF (真の一般化): {lv3_self}件")
        print(f"    - ECHO (指導の受け売り): {lv3_echo}件")
        if lv3_echo > lv3_self:
            print(f"    ⚠ 注意: Level 3 の多くが ECHO です。学生の自発的概念化はまだ発達途上の可能性があります。")

    # 学生別レベル分布
    print(f"\n--- 学生別レベル分布 ---")
    students = {}
    for e in judged:
        name = e['context']['student_name']
        week = e['context']['week_number']
        lv = e['judgment']['level']
        if name not in students:
            students[name] = {'levels': [], 'weeks': []}
        students[name]['levels'].append(lv)
        students[name]['weeks'].append((week, lv))

    for name, info in sorted(students.items()):
        avg = sum(info['levels']) / len(info['levels'])
        dist = Counter(info['levels'])
        dist_str = ', '.join(f"Lv{k}:{v}" for k, v in sorted(dist.items()))
        print(f"  {name}: 平均={avg:.2f} ({dist_str})")

    # 期間別（前半 vs 後半）
    print(f"\n--- 期間別比較 ---")
    early = [e for e in judged if e['context']['week_number'] <= 5]
    late = [e for e in judged if e['context']['week_number'] > 5]
    if early:
        avg_early = sum(e['judgment']['level'] for e in early) / len(early)
        print(f"  前半 (Week 1-5): 平均={avg_early:.2f} (n={len(early)})")
    if late:
        avg_late = sum(e['judgment']['level'] for e in late) / len(late)
        print(f"  後半 (Week 6-11): 平均={avg_late:.2f} (n={len(late)})")
    if early and late:
        diff = avg_late - avg_early
        trend = "上昇" if diff > 0 else ("低下" if diff < 0 else "変化なし")
        print(f"  差分: {diff:+.2f} ({trend})")

    # 迷ったケース（自信度1のエントリー）
    low_conf = [e for e in judged if e['judgment']['confidence'] == 1]
    if low_conf:
        print(f"\n--- 迷ったケース (自信度=1) ---")
        for e in low_conf:
            print(f"  #{e['id']} {e['context']['student_name']} Week{e['context']['week_number']}")
            print(f"    -> Lv.{e['judgment']['level']}")
            if e['judgment']['notes']:
                print(f"    メモ: {e['judgment']['notes'][:80]}...")

    # AI実装への示唆
    print(f"\n--- AI実装への示唆 ---")
    print(f"  1. 最頻レベル: Lv.{levels.most_common(1)[0][0]} ({levels.most_common(1)[0][1]}件)")
    if low_conf:
        print(f"  2. 判定困難ケース: {len(low_conf)}件 -> AIプロンプト設計の重点")
    if early and late:
        print(f"  3. 成長トレンド: {trend}")
        if diff > 0:
            print(f"     -> AIには時系列を考慮したプロンプトが有効")

    # CSV出力
    csv_file = 'step0_analysis_result.csv'
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write("ID,学生名,Week,日付,Level,ConceptSource,自信度,エビデンス,メモ\n")
        for e in judged:
            j = e['judgment']
            source = j.get('concept_source', '')
            f.write(f"{e['id']},{e['context']['student_name']},{e['context']['week_number']},"
                    f"{e['context']['journal_date']},{j['level']},{source},{j['confidence'] or ''},"
                    f"\"{j['evidence']}\",\"{j['notes']}\"\n")
    print(f"\n[OK] CSV出力: {csv_file}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    data, filename = load_latest_judged()
    analyze(data)
