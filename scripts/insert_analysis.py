import sqlite3
import os

def insert_analysis(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Clear existing analysis
    cursor.execute('DELETE FROM insights')
    cursor.execute('DELETE FROM growth_triggers')
    
    # 2. Get Journal IDs (ordered by date)
    cursor.execute('SELECT id, date, week_number FROM journals ORDER BY date ASC')
    journals = { f"{row[1]}_{row[2]}": row[0] for row in cursor.fetchall() }
    
    # helper to find journal id reliably
    def get_id(search_date, week):
        for k, v in journals.items():
            if search_date in k and str(week) in k:
                return v
        return None

    # --- Insights ---
    insights_data = [
        # W1
        (get_id("05月19日", 1), "生活背景", "認知症とは思えなかったが、日常よりも診察室での方が症状がわかりにくい...", "患者の『診察室での姿』と『生活の場での姿』の乖離に気づき、日常生活を知る重要性を認識した瞬間。"),
        (get_id("05月19日", 1), "滲み出し", "ピッキングがスムーズにできなかったり...一人ひとりに合った質問や説明ができるようにしたい", "OSCE（試験）と実地（生活）の差に直面した際の葛藤が表れている。"),
        # W5
        (get_id("06月16日", 5), "線", "タムスロシンのtmaxとt1/2から評価する技を知った。半減期から効果がいつ頃得ることができるのかを推測...", "薬理学的な知識を、点（成分）から線（時間軸での効果予測）へ変換して臨床に応用し始めている。"),
        # W11
        (get_id("07月29日", 11), "生活背景", "1ヵ月後に飲む薬はカレンダーに貼ってあるらしく...", "患者が自宅でどのように薬と向き合っているか（生活の細部）への関心が高まっている。"),
        (get_id("07月30日", 11), "伏線回収", "5月の頃は内容が短く、薄い印象を受けた。最近のものとは文量が全然違った。", "自らの過去の記録（伏線）を振り返り、自身の視座の変化を客観的に評価できている。"),
        (get_id("07月30日", 11), "線", "優先順位を考えてしなくても良いとすることもあることを学んだ", "『ルール通りの調剤』から、患者の人生における薬の『重みづけ』という線で捉え直している。")
    ]
    
    for item in insights_data:
        if item[0]:
            cursor.execute('INSERT INTO insights (journal_id, type, snippet, reason) VALUES (?, ?, ?, ?)', item)

    # --- Growth Triggers ---
    # Need student_id
    cursor.execute('SELECT id FROM students LIMIT 1')
    student_id = cursor.fetchone()[0]
    
    triggers = [
        ("2025年05月", "【初期状態】OSCE形式の『正解探し』。患者の生活よりも、自己の技術不足や知識不足に焦点が当たっている。"),
        ("2025年06月", "【変化：専門性の臨床応用】薬理知識（半減期等）を、患者の『困りごと（夜間尿）』の解決策として結びつけ始めた。"),
        ("2025年07月", "【飛躍：対話のヒント】『減らしたい患者に、なぜ？と問い、言語化させる』という、智弘様の指導に近い高度なヒアリング視座を獲得。日誌の質的変化を自ら確信。")
    ]
    
    for date_str, desc in triggers:
        cursor.execute('INSERT INTO growth_triggers (student_id, date, description) VALUES (?, ?, ?)', (student_id, date_str, desc))

    conn.commit()
    conn.close()
    print("Analysis results inserted into DB.")

if __name__ == "__main__":
    base_dir = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log"
    db_path = os.path.join(base_dir, "kizuki_log.db")
    insert_analysis(db_path)
