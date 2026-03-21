import sqlite3
import os

def insert_analysis_batch(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Clear existing analysis
    cursor.execute('DELETE FROM insights')
    cursor.execute('DELETE FROM growth_triggers')
    
    # helper to find journal id reliably
    def get_journal_id(student_name, week):
        cursor.execute('''
            SELECT journals.id FROM journals 
            JOIN students ON journals.student_id = students.id 
            WHERE students.name = ? AND journals.week_number = ?
            LIMIT 1
        ''', (student_name, week))
        res = cursor.fetchone()
        return res[0] if res else None

    # --- Cross-Student Insights (Sampled) ---
    insights_data = [
        # 渡辺さん
        ("渡辺 新夏", 1, "滲み出し", "OSCEとは違って...一人ひとりに合った質問や説明ができるようにしたい", "実地での摩擦から、個別化の必要性に気づいた瞬間。"),
        ("渡辺 新夏", 11, "伏線回収", "5月の頃は内容が短く、薄い印象を受けた。最近のものとは文量が全然違った。", "自己の視座の変化を記録の質からメタ認知できている。"),
        
        # 中﨑 優奈
        ("中﨑 優奈", 1, "生活背景", "ご年配の方は自身の状態を自ら話していただける方が多いので、若い方が来られた時に情報を得るのが難しい", "年代によるコミュニケーションの特性（生活様式の差）に早期に気づいている。"),
        ("中﨑 優奈", 11, "線", "一包化するかしないかは、薬の数が多いからという理由だけでなく、飲まなくてはいけない優先順位を考えてしなくても良いとすることもある", "『調剤のルール』を『患者の生活の線』で再定義している。高度な職能判断。"),
        
        # 湯口 万里奈
        ("湯口 万里奈", 5, "線", "今までの薬歴を確認し、どのような疾患があり、この薬で何を治療しているのか把握するようにした", "点のエントリーではなく、薬歴の連続性（線）から病態を推測する姿勢の芽生え。"),
        ("湯口 万里奈", 11, "滲み出し", "もっと患者さんの気持ちを受け止めようと思った。自分の認知機能の低下を悲しんでいるようで...", "機能的な説明を超えて、患者の心情（滲み出し）に寄り添う専門職としての葛藤。"),
        
        # 田中 靖子
        ("田中 靖子", 5, "地域資源", "ヘルパーさん、訪看さん、薬剤師が介入することで...情報の共有が大切だと再確認した", "薬局の壁を超えた多職種連携（地域資源）の価値を在宅現場で実感。"),
        ("田中 靖子", 11, "伏線回収", "在宅訪問に伺う前は、薬の効果や副作用の有無をメイン...それだけではなく、普段の生活の様子からQOLを確認し...", "自らの当初の思い込み（伏線）を、生活支援という新しい価値観で上書きしている。")
    ]
    
    for name, week, itype, snippet, reason in insights_data:
        jid = get_journal_id(name, week)
        if jid:
            cursor.execute('INSERT INTO insights (journal_id, type, snippet, reason) VALUES (?, ?, ?, ?)', (jid, itype, snippet, reason))

    # --- Growth Triggers (Categorized) ---
    # Fetch all students
    cursor.execute('SELECT id, name FROM students')
    students = cursor.fetchall()
    
    for sid, name in students:
        triggers = [
            ("Week 1", "【技術への集中】ピッキング、一包化、OSCE的な正解へのこだわりが記述の大部分を占める。"),
            ("Week 5", "【臨床への接続】薬理知識や薬歴情報が、目の前の患者への具体的なアプローチ（提案）へと繋がり始める。"),
            ("Week 11", "【生活への翻訳】薬の適正化だけでなく、患者の心情、優先順位、生活QOLを基軸とした判断が優先されるようになる。")
        ]
        for date_str, desc in triggers:
            cursor.execute('INSERT INTO growth_triggers (student_id, date, description) VALUES (?, ?, ?)', (sid, date_str, desc))

    conn.commit()
    conn.close()
    print("Batch analysis results inserted into DB.")

if __name__ == "__main__":
    base_dir = "/Users/yomogiyakkyoku/Library/CloudStorage/OneDrive-株式会社ｗｏｒｍｗｏｏｄ/実習ツール類/Kizuki log"
    db_path = os.path.join(base_dir, "kizuki_log.db")
    insert_analysis_batch(db_path)
