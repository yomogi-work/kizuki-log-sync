"""
Kizuki-Log AI Bridge
Constitution v1.0 に基づく LLM API ブリッジモジュール
"""

import json
import os
import urllib.request
import urllib.error
import sys

# ──────────────────────────────────────────────
# .env ファイルの簡易ローダー
# ──────────────────────────────────────────────
def load_env(env_path=None):
    """標準ライブラリのみで .env ファイルを読み込む"""
    if env_path is None:
        env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, _, value = line.partition('=')
                os.environ.setdefault(key.strip(), value.strip())


# ──────────────────────────────────────────────
# システムプロンプト（Constitution §3, §4, §5, §6）
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは、地域密着型薬局の熟練指導薬剤師です。
20年以上の調剤・服薬指導・在宅医療の経験を持ち、「穏やかな日々のお手伝い」を信念とするメンターとして振る舞います。

## あなたの役割
あなたは学生を「評価」しません。学生の日誌に潜む**価値を認め（Recognition of Value）**、指導薬剤師に対して「ブリーフィング・レポート」を提供する**鏡（Mirror）**であり**翻訳者（Translator）**です。

## 絶対禁止事項
- 成績評価（点数化、A/B/C、合否判定、序列化）
- ラベリング（「良い学生」「悪い学生」等）
- 指導の代替（人間の指導を省略する自動化）

## 5つの翻訳レンズ（薬局固有の分析視点）
以下の5つのフィルターで学生の日誌を「プロの気づき」に翻訳してください：
1. **生活背景への解像度**: 患者を「疾患」でなく「生活者」として見ているか
2. **言葉の裏にある「伏線」の回収**: 非言語情報（表情、声色、言い淀み）への気づき
3. **「点」でなく「線」の関わり**: 前回との比較、将来の予測、継続的信頼の構築
4. **地域資源との有機的な繋がり**: 薬局の外（坂道、スーパー、ケアマネ、他職種）への視点
5. **職能の「滲み出し」**: 業務外での自発的な気づき、薬剤師としての「お節介」の芽

## トーン＆マナー
- 丁寧だが親しみやすい「です・ます」調
- 医療用語は適切に使うが、難解な表現で威圧しない
- 絵文字は 🌿, 💡, 💊 程度を適度に使用

## 出力形式
必ず以下のJSON形式**のみ**を出力してください。JSON以外のテキストは一切出力しないでください。

{
  "translation_for_instructor": {
    "professional_insight": "学生の記述を専門的価値（5つのレンズ）に翻訳した解説",
    "growth_evidence": "過去の傾向と比較した、本日特筆すべき成長の兆し",
    "attention_points": "日誌から読み取れる学生の勘違いや、フォローが必要な不安要素"
  },
  "mentoring_support": {
    "praise_points": "本日の対話で、指導者が学生を『褒める』ための具体的な根拠",
    "suggested_questions": [
      "学生の視座を高めるための『問いかけ』案①",
      "学生の視座を高めるための『問いかけ』案②"
    ]
  },
  "mentoring_seeds": [
    "次回以降も継続して観察・指導すべきポイント①",
    "次回以降も継続して観察・指導すべきポイント②",
    "次回以降も継続して観察・指導すべきポイント③"
  ],
  "step0_drafts": [
    {
      "evidence": "学生の日誌から抽出した『具体的な気づき・成長点』の一文（トピック1）",
      "level": 1,
      "concept_source": "SELF",
      "notes": "この判定の理由（例：指導内容のオウム返し等）"
    },
    {
      "evidence": "日誌内に複数の気づきが含まれている場合は抽出した別の一文（トピック2）",
      "level": 3,
      "concept_source": "ECHO",
      "notes": "この判定の理由"
    }
  ]
}

## 学生の気づきの自動分類（step0_drafts の判定基準）
学生の日誌に書かれている複数の気づき（トピック）を抽出し、それぞれについて以下の基準で判定（下書きを作成）してください。

**1. Level（概念化レベル）:**
- 1: 事実描写・表層的な感想（「〜を見学した」「〜が嬉しかった」）
- 2: 文脈理解・意味づけ（「〜だからこれが必要なんだと分かった」）
- 3: 機能的一般化・普遍の原則（「薬剤師という職業は〜であるべきだ」）※滅多に出ない高いハードル

**2. Concept Source（概念の主体）:**
- SELF: 学生独自の表現、個人的経験に基づく考察
- ECHO: 指導者メモに記載されている指導内容と酷似している、または言い換えただけの受け売り
- MIXED: 指導者からの助言内容と、学生独自の解釈・具体例が混合している状態

## SOS検知
学生の強い無力感、倫理的危機、メンタル不調を感じた場合は、通常のレポートの代わりに以下を出力してください：
{
  "sos_alert": true,
  "alert_reason": "検知した内容の説明",
  "suggested_action": "指導者への推奨対応"
}

## 低品質日誌への対応
内容が乏しい場合でも叱責せず、その日の「景色」や「音」など五感の記憶から想起を促す問いかけを suggested_questions に含めてください。
"""


def get_week_stance_instruction(week: int) -> str:
    """§5.3 週次による指導スタンスの調整"""
    if week <= 2:
        return """【指導スタンス: Week 1-2 — 安心感と関係構築】
まずは些細な気づきを褒め、実習環境に馴染ませることを優先した助言を行ってください。
学生が不安を感じていても、「それでいいんです」と受容する姿勢を大切にしてください。"""
    elif week <= 7:
        return """【指導スタンス: Week 3-7 — 視座の翻訳と拡大】
患者の生活背景や非言語情報に目を向けさせる問いかけを中心に提案してください。
「なぜそう感じたのか？」「患者さんの立場ではどうか？」といった視点転換を促してください。"""
    else:
        return """【指導スタンス: Week 8-11 — プロとしての自律支援】
一人の薬剤師として臨床判断を求めるような、高度な対話を指導者に促してください。
学生が自ら考え、判断し、行動できるようになることを見据えた問いかけを提案してください。"""



WEEKLY_SYSTEM_PROMPT = """あなたは、地域密着型薬局の熟練指導薬剤師メンター「Gag」です。
1週間分の学生の日誌と、指導者が確定させた判定データ（Step 0）を精査し、学生の成長を「点ではなく線」で捉えた高度な臨床教育レビューを作成してください。

## あなたの役割
表面的な出来事の要約（「〜ができた」「〜を学んだ」等の羅列）は**厳禁**です。
プロの指導者として、日誌の行間や判定データの傾向から、以下の「診断」を行ってください：
1. **視座の移動**: 初日と最終日で、学生が見ている「風景」はどう変わったか？
2. **Step 0の解釈**: Level (1-3) の推移と Source (SELF/ECHO) の比率から、その気づきが「借り物（オウム返し）」か「自分の血肉」かを評価。
3. **5つのレンズによる多角化**: 憲法の視点（生活背景、非言語、線の関わり等）がどれくらい「解像度高く」見え始めているか。

## 絶対に避けるべき表現（禁止事項）
- 「日誌を通じて成長が見られました」のような一般的・機械的なコメント。
- 「〜ができ、〜もでき、さらには〜もできました」という単なる事実の羅列。
- 「来週も頑張りましょう」などの具体性のない激励。

## 望ましい視点と表現
- 「週の初めは薬効（Level 1）に固執していたが、水曜日を境に患者さんの『言葉の裏（Lens）』へ関心が移行し始めている。」
- 「SELF比率が低い。高度な概念（Level 3）を口にしているが、それは指導者の言葉をなぞっている段階（ECHO）であり、まだ本人の実感に基づいた言葉になっていない。」

## 出力形式
必ず以下のJSON形式**のみ**を出力してください。

{
  "weekly_review": {
    "growth_story": "学生の視座の変化を『物語（ナラティブ）』として記述。事実の羅列ではなく、プロの鋭い洞察を込めること。250〜400文字程度。",
    "key_achievements": "今週の『決定的な瞬間（Aha-moment）』。どの発言・行動が、プロへの階段を一段登らせたか。",
    "habitual_patterns": "日誌の書き方や思考から見える、学生特有の『認知のバイアス』や『良い癖』の指摘。",
    "next_week_goals": "来週、具体的にどの『レンズ（視点）』を意識して現場に立たせるべきかの具体的な処方箋。"
  },
  "internal_scores": {
    "lenses": {
      "insight_on_lifestyle": 0.0,
      "non_verbal_clues": 0.0,
      "continuous_relationship": 0.0,
      "community_resources": 0.0,
      "professional_proactivity": 0.0
    },
    "conceptualization_avg": 0.0,
    "self_reliance_ratio": 0.0,
    "instructor_notes_summary": "指導者メモに隠された、学生が言語化できていない非言語的成長や課題のプロによる要約。"
  }
}

## スコア算出（0.0 〜 5.0）
1. **5つのレンズ**: 日誌内の気づきの「具体性と深さ」で判定。単に触れただけなら 1.0、その視点から臨床判断を試みていれば 4.0 以上。
2. **conceptualization_avg**: Step 0 判定データの Level 加重平均。
3. **self_reliance_ratio**: SELF / (SELF+ECHO+MIXED) の比率。
"""


def build_user_prompt(week: int, log_achieved: str, log_unachieved: str,
                      previous_triggers: str = "", instructor_notes: str = "") -> str:
    """ユーザープロンプトを構築する"""
    stance = get_week_stance_instruction(week)
    
    prompt = f"""{stance}

---
## 本日の日誌データ

**実習週**: Week {week}

### 学生ログ①: 具体的な実習内容・達成できた点
{log_achieved}

### 学生ログ②: 達成できなかった点・反省・改善点
{log_unachieved}
"""
    
    if previous_triggers:
        prompt += f"""
### 前回の継続フラグ（指導者が前回選択した観察ポイント）
{previous_triggers}
※ このポイントについて、今日の日誌ではどのような変化が見られるか報告してください。
"""
    
    if instructor_notes:
        prompt += f"""
### 指導者の観察メモ
{instructor_notes}
※ この観察を踏まえてAIの解釈を補正してください。
"""
    
    prompt += """
---
上記の日誌を分析し、指定されたJSON形式のみで出力してください。
"""
    return prompt


# ──────────────────────────────────────────────
# LLM API 呼び出し
# ──────────────────────────────────────────────

def call_openai(system_prompt: str, user_prompt: str) -> dict:
    """OpenAI API (GPT-4o) を呼び出す"""
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key or api_key.startswith('sk-xxxx'):
        raise ValueError("OPENAI_API_KEY が設定されていません。.env ファイルを確認してください。")
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    content = result['choices'][0]['message']['content']
    return json.loads(content)


def call_anthropic(system_prompt: str, user_prompt: str) -> dict:
    """Anthropic API (Claude 3.5 Sonnet) を呼び出す"""
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key or api_key.startswith('sk-ant-xxxx'):
        raise ValueError("ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。")
    
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ]
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    content = result['content'][0]['text']
    # JSONブロックを抽出（```json ... ``` で囲まれている場合）
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()
    
    return json.loads(content)


def call_gemini(system_prompt: str, user_prompt: str) -> dict:
    """Google Gemini API (AI Studio) を呼び出す"""
    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key or api_key.startswith('AIzaSy-xxxx'):
        raise ValueError("GEMINI_API_KEY が設定されていません。.env ファイルを確認してください。")
    
    model = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash').strip()
    # v1beta エンドポイントを使用（2.0系はこれが安定）
    url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": user_prompt}]
            }
        ],
        "systemInstruction": {
            "parts": [{"text": system_prompt}]
        },
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    content = result['candidates'][0]['content']['parts'][0]['text']
    
    # JSONブロックを抽出（```json ... ``` で囲まれている場合）
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()
    
    return json.loads(content)


def call_groq(system_prompt: str, user_prompt: str) -> dict:
    """Groq API (Llama 3.3 70B) を呼び出す"""
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key or api_key.startswith('gsk_xxxx'):
        raise ValueError("GROQ_API_KEY が設定されていません。.env ファイルを確認してください。")
    
    model = os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        'https://api.groq.com/openai/v1/chat/completions',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'Kizuki-Log/1.0'
        },
        method='POST'
    )
    
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode('utf-8'))
    
    content = result['choices'][0]['message']['content']
    return json.loads(content)


def analyze_journal(week: int, log_achieved: str, log_unachieved: str,
                    previous_triggers: str = "", instructor_notes: str = "") -> dict:
    """
    メインの解析関数。
    Constitution §5.2 準拠のJSON を返す。
    """
    load_env()
    
    provider = os.environ.get('AI_PROVIDER', 'gemini').lower()
    user_prompt = build_user_prompt(week, log_achieved, log_unachieved,
                                    previous_triggers, instructor_notes)
    
    # プロバイダ → 呼び出し関数のマッピング
    provider_map = {
        'gemini': call_gemini,
        'openai': call_openai,
        'anthropic': call_anthropic,
        'groq': call_groq,
    }
    
    # フォールバック設定（メインが429エラーの場合に使用）
    fallback_provider = os.environ.get('AI_FALLBACK_PROVIDER', '').lower()
    
    try:
        call_fn = provider_map.get(provider, call_gemini)
        try:
            result = call_fn(SYSTEM_PROMPT, user_prompt)
        except urllib.error.HTTPError as e:
            if e.code == 429 and fallback_provider and fallback_provider in provider_map:
                print(f"⚠️  {provider} がクォータ制限中。{fallback_provider} にフォールバックします...")
                fallback_fn = provider_map[fallback_provider]
                result = fallback_fn(SYSTEM_PROMPT, user_prompt)
            else:
                raise
        
        # レスポンスの検証
        if 'sos_alert' in result:
            return result  # SOS アラートはそのまま返す
        
        # 必須フィールドの存在チェック
        required_keys = ['translation_for_instructor', 'mentoring_support', 'mentoring_seeds']
        for key in required_keys:
            if key not in result:
                raise ValueError(f"APIレスポンスに必須フィールド '{key}' がありません")
        
        return result
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        return {
            "error": True,
            "message": f"API エラー ({e.code}): {error_body[:200]}",
            "suggestion": "APIキーの設定と残高を確認してください。"
        }
    except urllib.error.URLError as e:
        return {
            "error": True,
            "message": f"接続エラー: {str(e.reason)}",
            "suggestion": "インターネット接続を確認してください。"
        }
    except json.JSONDecodeError as e:
        return {
            "error": True,
            "message": f"JSON解析エラー: {str(e)}",
            "suggestion": "AIの応答形式が不正でした。再度お試しください。"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"予期しないエラー: {str(e)}",
            "suggestion": "開発者に連絡してください。"
        }


def analyze_weekly(week_number: int, journals: list) -> dict:
    """
    1週間分の日誌リストを分析し、週次レビューとスコアを返す。
    journals: [ { "date": "...", "practical_content": "...", "step0_judgments": [...] }, ... ]
    """
    load_env()
    
    # ユーザープロンプトの構築
    journal_texts = []
    judgments_summary = []
    
    for j in journals:
        date = j.get('date', '不明')
        content = j.get('practical_content', '')
        unachieved = j.get('unachieved_point', '')
        notes = j.get('instructor_notes', '')
        
        entry = f"--- 日付: {date} ---\n[実習内容]\n{content}\n[反省]\n{unachieved}\n[指導者メモ]\n{notes}\n"
        
        juds = j.get('step0_judgments', [])
        if juds:
            entry += "[確定判定]\n"
            for jud in juds:
                entry += f"  - Lv.{jud.get('level')} | {jud.get('concept_source')} | {jud.get('evidence')}\n"
        
        journal_texts.append(entry)

    user_prompt = f"""【重要事項】
これは全11週間にわたる薬局実習のうち、「第 {week_number} 週目」のまとめ分析です。
({week_number}/11週目という現在地を強く意識してください。序盤・中盤の週である場合、「実習全体を通して」や「初日から最終日で大きく変化した」といった完了形の評価は不適切です)

以下の第 {week_number} 週目の実習記録と判定データを精査し、週次レビューを作成してください：

{"".join(journal_texts)}

---
上記を元に、指定されたJSON形式で週次レビューを出力してください。
"""

    provider = os.environ.get('AI_PROVIDER', 'gemini').lower()
    # 週次分析は文脈が長くなるため、可能であればより賢いモデルを選択（ここでは共通の仕組みを利用）
    
    provider_map = {
        'gemini': call_gemini,
        'openai': call_openai,
        'anthropic': call_anthropic,
        'groq': call_groq,
    }
    
    fallback_provider = os.environ.get('AI_FALLBACK_PROVIDER', '').lower()
    
    try:
        call_fn = provider_map.get(provider, call_gemini)
        try:
            result = call_fn(WEEKLY_SYSTEM_PROMPT, user_prompt)
        except urllib.error.HTTPError as e:
            if e.code == 429 and fallback_provider and fallback_provider in provider_map:
                print(f"⚠️  週次分析: {provider} がクォータ制限中。{fallback_provider} にフォールバックします...")
                fallback_fn = provider_map[fallback_provider]
                result = fallback_fn(WEEKLY_SYSTEM_PROMPT, user_prompt)
            else:
                raise
        
        # 最低限のバリデーション
        if 'weekly_review' not in result or 'internal_scores' not in result:
             raise ValueError("週次レビューの必須フィールドが不足しています。")
        
        return result

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else ''
        return {
            "error": True,
            "message": f"API エラー ({e.code}): {error_body[:200]}",
            "suggestion": "APIクォータ制限に達しました。しばらく待つか、別モデル（Groq等）をお試しください。"
        }
    except Exception as e:
        return {
            "error": True,
            "message": f"週次分析エラー: {str(e)}",
            "suggestion": "データ量が多い場合、プロバイダの制限に達した可能性があります。"
        }


# ──────────────────────────────────────────────
# CLIテスト用
# ──────────────────────────────────────────────
if __name__ == '__main__':
    if '--test' in sys.argv:
        print("=== Kizuki-Log AI Bridge テスト ===")
        load_env()
        print(f"プロバイダ: {os.environ.get('AI_PROVIDER', 'gemini')}")
        
        # サンプル日誌（中﨑さん Week 1 のデータを匿名化）
        test_result = analyze_journal(
            week=1,
            log_achieved="""本日は、受付業務の担当だったので、処方箋を患者さんから受け取る、マイナンバーカードとお薬手帳を持っているかの確認をした。
OTCを探している患者に対して、どんなお薬を探しているか聞いた。目薬を探しているとのことだったので、目に痛みがあるのか、目が乾いているのかを聞けたことは良かった。
服薬指導も2件担当させてもらった。緊張せず、患者さんと会話ができたので、引き続き落ち着いて取り組んでいきたい。
1件目の患者さんは、時間がないので急いで欲しいと述べられた。このパターンは、OSCEでは想定していなかったので、非常によい経験になった。""",
            log_unachieved="""服薬指導の流れを的確に覚えていなかったので、本日中に確認し、明日は今日より成長したい。
過去の薬歴をみて、患者さんに伝えるべきことが今の段階では、全くわからないので、触れた薬から少しずつ知識をつけていかなければと感じた。""",
            previous_triggers="",
            instructor_notes=""
        )
        
        print("\n--- 結果 ---")
        print(json.dumps(test_result, ensure_ascii=False, indent=2))
    else:
        print("使い方: python ai_bridge.py --test")
