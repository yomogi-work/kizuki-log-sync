let dashboardData = null;

// グローバル設定（薬局共通）
let globalSettings = {
    slogan: "笑顔でつなぐ、地域の絆",
    keywords: "地域連携, 在宅医療, 丁寧な服薬指導"
};

/**
 * 名前文字列から安定したIDを生成する。
 * 同じ名前なら常に同じIDが返る（デバイス間同期対策）。
 */
function generateStableId(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        const char = name.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash; // Convert to 32-bit integer
    }
    // 正の値にして、既存のDB IDと衝突しないよう100000以上にする
    return Math.abs(hash) + 100000;
}

async function init() {
    try {
        const response = await fetch('./dashboard_data.json?t=' + Date.now());
        dashboardData = await response.json();

        // 各学生に初期設定を付与（既存データ移行用）
        dashboardData.students.forEach(student => {
            if (!student.settings) {
                student.settings = {
                    startDate: "2025-05-19",
                    endDate: "2025-08-01",
                    goal: "患者さん一人ひとりに寄り添った服薬指導ができるようになる",
                    interests: "在宅医療、多職種連携"
                };
            }
        });

        populateStudentSelector();

        // 初期表示
        const firstStudent = dashboardData.students[0];
        if (firstStudent) {
            updateDashboard(firstStudent);
            syncSettingsForm(firstStudent);
        }

        document.getElementById('student-select').addEventListener('change', (e) => {
            const student = dashboardData.students.find(s => s.id == e.target.value);
            if (student) {
                updateDashboard(student);
                syncSettingsForm(student);
                clearDailyInterface();
            }
        });

        // 今日の日付をDaily Inputのデフォルトにする
        document.getElementById('daily-date').valueAsDate = new Date();

        // イベントリスナーのセットアップ
        setupEventListeners();

        // AIプロバイダの復元
        const savedProvider = localStorage.getItem('kizuki_ai_provider');
        const providerSelect = document.getElementById('ai-provider-select');
        if (savedProvider && providerSelect) {
            providerSelect.value = savedProvider;
        }

        // 指導者モードの復元
        const instructorMode = localStorage.getItem('kizuki_instructor_mode') === 'true';
        const toggle = document.getElementById('instructor-mode-toggle');
        if (toggle) {
            toggle.checked = instructorMode;
            if (instructorMode) document.body.classList.add('instructor-mode');
        }

    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

function setupEventListeners() {
    // タブ切り替え
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('tab-storyboard').style.display = tabId === 'storyboard' ? 'block' : 'none';
            document.getElementById('tab-daily').style.display = tabId === 'daily' ? 'block' : 'none';
            document.getElementById('tab-settings').style.display = tabId === 'settings' ? 'block' : 'none';

            // Dailyタブを開いた時に前回の継続フラグを表示
            if (tabId === 'daily') {
                loadPreviousTriggers();
            }
        });
    });

    // 新規学生を追加ボタン
    const addNewBtn = document.getElementById('add-new-student-btn');
    if (addNewBtn) {
        addNewBtn.addEventListener('click', () => {
            document.getElementById('settings-title').textContent = "新規学生の登録";
            document.getElementById('student-name').value = "";
            document.getElementById('start-date').value = "";
            document.getElementById('end-date').value = "";
            document.getElementById('student-goal').value = "";
            document.getElementById('student-interests').value = "";

            const sBtn = document.getElementById('save-settings-btn');
            if (sBtn) sBtn.textContent = "新規学生として登録";

            document.getElementById('student-name').focus();
        });
    }

    // 保存ボタン
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', () => {
            const name = document.getElementById('student-name').value.trim();
            if (!name) {
                alert("学生氏名を入力してください");
                return;
            }

            globalSettings.slogan = document.getElementById('pharmacy-slogan').value;
            globalSettings.keywords = document.getElementById('focus-keywords').value;

            const tempSettings = {
                startDate: document.getElementById('start-date').value,
                endDate: document.getElementById('end-date').value,
                goal: document.getElementById('student-goal').value,
                interests: document.getElementById('student-interests').value
            };

            if (!tempSettings.startDate || !tempSettings.endDate) {
                alert("実習期間を設定してください");
                return;
            }

            let student = dashboardData.students.find(s => s.name === name);
            const isNew = !student;

            if (isNew) {
                student = {
                    id: generateStableId(name),
                    name: name,
                    settings: tempSettings,
                    journals: [],
                    growth_triggers: [],
                    insights: []
                };
                dashboardData.students.push(student);
                populateStudentSelector();
            } else {
                student.settings = tempSettings;
            }

            document.getElementById('student-select').value = student.id;

            const subtitleEl = document.querySelector('.subtitle');
            if (subtitleEl) {
                subtitleEl.textContent = `〜${globalSettings.slogan}〜`;
            }

            alert(isNew ? `新しい学生「${name}」を登録しました。` : `「${name}」の設定を変更しました。`);

            saveDataToServer();
            clearDailyInterface();
            document.querySelector('.tab-btn[data-tab="storyboard"]').click();
            updateDashboard(student);
        });
    }

    // ==================================================
    // AI解析・保存ボタン
    // ==================================================
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', async () => {
            const practicalText = document.getElementById('journal-practical').value;
            const unachievedText = document.getElementById('journal-unachieved').value;
            const dateStr = document.getElementById('daily-date').value;
            const instructorNotes = document.getElementById('instructor-notes').value;

            if (!practicalText && !unachievedText) {
                alert("日誌を入力してください");
                return;
            }

            // 1. データの保存
            const studentId = document.getElementById('student-select').value;
            const student = dashboardData.students.find(s => s.id == studentId);

            if (student) {
                let journal = student.journals.find(j => j.date === dateStr);
                if (!journal) {
                    journal = {
                        id: Date.now(),
                        date: dateStr,
                        week_number: calculateWeekNumber(dateStr, student.settings.startDate)
                    };
                    student.journals.push(journal);
                }

                journal.practical_content = practicalText;
                journal.unachieved_point = unachievedText;
                journal.content = practicalText; // 互換性のため
                journal.instructor_notes = instructorNotes;

                await saveDataToServer();

                // カレンダーの再描画
                renderCalendar(student);

                // 2. AI解析
                const weekNum = journal.week_number;
                const previousTriggers = getLatestSelectedSeed(student, dateStr);

                await performAIAnalysis(weekNum, practicalText, unachievedText, previousTriggers, instructorNotes);
            }
        });
    }

    // 日付変更時のデータロード
    const dateInput = document.getElementById('daily-date');
    if (dateInput) {
        dateInput.addEventListener('change', (e) => {
            loadJournalForDate(e.target.value);
        });
    }

    // フィードバック保存
    const saveFeedbackBtn = document.getElementById('save-feedback-btn');
    if (saveFeedbackBtn) {
        saveFeedbackBtn.addEventListener('click', async () => {
            const text = document.getElementById('feedback-input').value;
            if (!text) {
                alert("コメントを入力してください");
                return;
            }

            const studentId = document.getElementById('student-select').value;
            const student = dashboardData.students.find(s => s.id == studentId);
            const dateStr = document.getElementById('daily-date').value;

            if (student) {
                const journal = student.journals.find(j => j.date === dateStr);
                if (journal) {
                    journal.feedback = text;
                    await saveDataToServer();
                    alert("フィードバックを保存しました！");
                } else {
                    alert("先に日誌を保存してください。");
                }
            }
        });
    }

    // 指導シード保存
    const saveSeedBtn = document.getElementById('save-seed-btn');
    if (saveSeedBtn) {
        saveSeedBtn.addEventListener('click', async () => {
            const selected = document.querySelector('input[name="mentoring-seed"]:checked');
            if (!selected) {
                alert("シードを1つ選択してください");
                return;
            }

            const studentId = document.getElementById('student-select').value;
            const student = dashboardData.students.find(s => s.id == studentId);
            const dateStr = document.getElementById('daily-date').value;

            if (student) {
                const journal = student.journals.find(j => j.date === dateStr);
                if (journal) {
                    journal.selected_seed = selected.value;
                    await saveDataToServer();
                    alert("指導シードを保存しました！\n次回の日誌入力時に「継続フラグ」として表示されます。");
                }
            }
        });
    }

    // Step0 判定結果の保存 (New!)
    const saveStep0Btn = document.getElementById('save-step0-btn');
    if (saveStep0Btn) {
        saveStep0Btn.addEventListener('click', async () => {
            const studentId = document.getElementById('student-select').value;
            const student = dashboardData.students.find(s => s.id == studentId);
            const dateStr = document.getElementById('daily-date').value;

            if (!student) return;
            const journal = student.journals.find(j => j.date === dateStr);
            if (!journal) {
                alert("先に日誌をAI解析・保存してください。");
                return;
            }

            // UIから編集内容を収集
            const draftsContainer = document.getElementById('step0-drafts-list');
            const items = draftsContainer.querySelectorAll('.step0-draft-item');
            const finalJudgments = [];

            items.forEach(item => {
                const evidence = item.dataset.evidence;
                const level = parseInt(item.querySelector('.step0-level-select').value, 10);
                const source = item.querySelector('.step0-source-select').value;

                finalJudgments.push({
                    evidence: evidence,
                    level: level,
                    concept_source: source
                });
            });

            // journal オブジェクトに保存
            journal.step0_judgments = finalJudgments;

            // サーバーへ送信
            await saveDataToServer();
            alert("研究用データ（Step0）の判定を確定・保存しました！");

            // 保存完了のUI視覚的フィードバック
            saveStep0Btn.textContent = "✓ 保存完了";
            saveStep0Btn.style.backgroundColor = "#4caf50";
            setTimeout(() => {
                saveStep0Btn.textContent = "この判定を確定して保存";
                saveStep0Btn.style.backgroundColor = "#9c27b0";
            }, 2000);
        });
    }

    // AIプロバイダ選択の保存
    const providerSelect = document.getElementById('ai-provider-select');
    if (providerSelect) {
        providerSelect.addEventListener('change', (e) => {
            localStorage.setItem('kizuki_ai_provider', e.target.value);
        });
    }

    // AI接続テストボタン
    const testAiBtn = document.getElementById('test-ai-btn');
    if (testAiBtn) {
        testAiBtn.addEventListener('click', async () => {
            const provider = document.getElementById('ai-provider-select').value;
            const statusDot = document.querySelector('.status-dot');
            const statusText = document.getElementById('ai-status-text');

            testAiBtn.disabled = true;
            testAiBtn.textContent = 'テスト中...';
            statusDot.className = 'status-dot status-unknown';
            statusText.textContent = '接続を確認中...';

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        week: 1,
                        log_achieved: '接続テスト',
                        log_unachieved: '接続テスト',
                        provider: provider
                    })
                });
                const result = await response.json();
                if (result.error) {
                    statusDot.className = 'status-dot status-error';
                    statusText.textContent = `❌ エラー: ${result.message}`;
                } else {
                    statusDot.className = 'status-dot status-ok';
                    statusText.textContent = `✅ 接続OK — ${provider} が正常に応答しました`;
                }
            } catch (e) {
                statusDot.className = 'status-dot status-error';
                statusText.textContent = `❌ 接続失敗: ${e.message}`;
            } finally {
                testAiBtn.disabled = false;
                testAiBtn.textContent = '🔌 接続テスト';
            }
        });
    }

    // 指導者モード切替
    const instructorToggle = document.getElementById('instructor-mode-toggle');
    if (instructorToggle) {
        instructorToggle.addEventListener('change', (e) => {
            const active = e.target.checked;
            document.body.classList.toggle('instructor-mode', active);
            localStorage.setItem('kizuki_instructor_mode', active);
        });
    }

    // 週次分析生成ボタン
    const generateWeeklyBtn = document.getElementById('generate-weekly-btn');
    if (generateWeeklyBtn) {
        generateWeeklyBtn.addEventListener('click', async () => {
            const studentId = document.getElementById('student-select').value;
            const student = dashboardData.students.find(s => s.id == studentId);
            if (!student) return;

            if (student.journals.length === 0) {
                alert("日誌データがありません。");
                return;
            }

            const latestJournal = student.journals.reduce((prev, current) =>
                (prev.date > current.date) ? prev : current
            );
            const targetWeek = latestJournal.week_number;

            if (confirm(`Week ${targetWeek} の週次分析を生成しますか？\n(1週間分のデータを俯瞰的に解析します)`)) {
                await performWeeklyAnalysis(student, targetWeek);
            }
        });
    }
}

// ==================================================
// AI 解析
// ==================================================
async function performAIAnalysis(week, logAchieved, logUnachieved, previousTriggers, instructorNotes) {
    const loadingEl = document.getElementById('analyze-loading');
    const analyzeBtn = document.getElementById('analyze-btn');

    // ローディング表示
    loadingEl.style.display = 'flex';
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = '解析中...';

    try {
        const selectedProvider = document.getElementById('ai-provider-select')?.value || '';
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                week: week,
                log_achieved: logAchieved,
                log_unachieved: logUnachieved,
                previous_triggers: previousTriggers,
                instructor_notes: instructorNotes,
                provider: selectedProvider
            })
        });

        const result = await response.json();

        if (result.error) {
            renderErrorResult(result);
        } else if (result.sos_alert) {
            renderSOSAlert(result);
        } else {
            renderBriefingReport(result);
        }

        // 解析結果を保存
        const studentId = document.getElementById('student-select').value;
        const student = dashboardData.students.find(s => s.id == studentId);
        const dateStr = document.getElementById('daily-date').value;
        if (student) {
            const journal = student.journals.find(j => j.date === dateStr);
            if (journal) {
                journal.ai_analysis = result;
                await saveDataToServer();
            }
        }

    } catch (error) {
        renderErrorResult({
            error: true,
            message: `通信エラー: ${error.message}`,
            suggestion: "サーバーが起動しているか確認してください。"
        });
    } finally {
        loadingEl.style.display = 'none';
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = '🤖 AI解析・保存';
    }
}


// ==================================================
// レンダリング関数
// ==================================================

function renderBriefingReport(result) {
    const resultDiv = document.getElementById('daily-analysis-result');
    const suggestDiv = document.getElementById('daily-suggestions');
    const seedCard = document.getElementById('seed-selection-card');

    // ブリーフィング・レポート
    const t = result.translation_for_instructor || {};
    resultDiv.innerHTML = `
        <div class="briefing-section">
            <div class="briefing-label">🔍 専門的洞察（5つのレンズ）</div>
            <div class="briefing-content">${escapeHtml(t.professional_insight || '')}</div>
        </div>
        <div class="briefing-section">
            <div class="briefing-label">📈 成長の兆し</div>
            <div class="briefing-content">${escapeHtml(t.growth_evidence || '')}</div>
        </div>
        <div class="briefing-section">
            <div class="briefing-label">⚠️ 注意すべき点</div>
            <div class="briefing-content">${escapeHtml(t.attention_points || '')}</div>
        </div>
    `;

    // 対話サポート
    const m = result.mentoring_support || {};
    let suggestHTML = `
        <div class="briefing-section">
            <div class="briefing-label">👏 褒めポイント</div>
            <div class="briefing-content">${escapeHtml(m.praise_points || '')}</div>
        </div>
        <div class="briefing-label" style="margin-top: 12px;">💡 問いかけ案</div>
    `;
    if (m.suggested_questions && m.suggested_questions.length > 0) {
        m.suggested_questions.forEach((q, i) => {
            suggestHTML += `<div class="suggestion-item">💬 ${escapeHtml(q)}</div>`;
        });
    }
    suggestDiv.innerHTML = suggestHTML;

    // 指導シード
    const seeds = result.mentoring_seeds || [];
    if (seeds.length > 0) {
        seedCard.style.display = 'block';
        const seedList = document.getElementById('mentoring-seeds-list');
        seedList.innerHTML = '';
        seeds.forEach((seed, i) => {
            const id = `seed-${i}`;
            seedList.innerHTML += `
                <label class="seed-option" for="${id}">
                    <input type="radio" name="mentoring-seed" id="${id}" value="${escapeHtml(seed)}">
                    <span class="seed-text">🌱 ${escapeHtml(seed)}</span>
                </label>
            `;
        });
    } else {
        seedCard.style.display = 'none';
    }

    // 研究データ判定 (Step0 Drafts) の描画
    const step0Card = document.getElementById('step0-judgment-card');
    const draftsList = document.getElementById('step0-drafts-list');
    const drafts = result.step0_drafts || [];

    if (drafts.length > 0) {
        step0Card.style.display = 'block';
        draftsList.innerHTML = '';

        drafts.forEach((draft, idx) => {
            // 安全のためエスケープ
            const safeEvidence = escapeHtml(draft.evidence || '');
            const safeNotes = escapeHtml(draft.notes || '');

            // Level選択の生成
            const l1_sel = draft.level === 1 ? 'selected' : '';
            const l2_sel = draft.level === 2 ? 'selected' : '';
            const l3_sel = draft.level === 3 ? 'selected' : '';

            // Source選択の生成
            const sSelf_sel = draft.concept_source === 'SELF' ? 'selected' : '';
            const sEcho_sel = draft.concept_source === 'ECHO' ? 'selected' : '';
            const sMix_sel = draft.concept_source === 'MIXED' ? 'selected' : '';

            const html = `
                <div class="step0-draft-item" data-evidence="${safeEvidence}">
                    <div class="draft-evidence">"${safeEvidence}"</div>
                    ${safeNotes ? `<div class="draft-notes">AI分析: ${safeNotes}</div>` : ''}
                    <div class="draft-judgment-row">
                        <select class="step0-level-select">
                            <option value="1" ${l1_sel}>Lv.1 (事実描写)</option>
                            <option value="2" ${l2_sel}>Lv.2 (文脈・意味づけ)</option>
                            <option value="3" ${l3_sel}>Lv.3 (機能的一般化)</option>
                        </select>
                        <select class="step0-source-select">
                            <option value="SELF" ${sSelf_sel}>主体: SELF (学生独自)</option>
                            <option value="ECHO" ${sEcho_sel}>主体: ECHO (オウム返し)</option>
                            <option value="MIXED" ${sMix_sel}>主体: MIXED (混合)</option>
                        </select>
                    </div>
                </div>
            `;
            draftsList.insertAdjacentHTML('beforeend', html);
        });
    } else {
        step0Card.style.display = 'none';
        draftsList.innerHTML = '';
    }
}

function renderSOSAlert(result) {
    const resultDiv = document.getElementById('daily-analysis-result');
    resultDiv.innerHTML = `
        <div class="sos-alert-box">
            <div class="sos-header">🚨 SOSアラート</div>
            <div class="sos-reason">${escapeHtml(result.alert_reason || '')}</div>
            <div class="sos-action"><strong>推奨対応:</strong> ${escapeHtml(result.suggested_action || '')}</div>
        </div>
    `;

    const suggestDiv = document.getElementById('daily-suggestions');
    suggestDiv.innerHTML = '<div class="sos-note">⚠️ SOSが検知されたため、通常のフィードバックは生成されませんでした。<br>学生との直接対話を優先してください。</div>';
}

function renderErrorResult(result) {
    const resultDiv = document.getElementById('daily-analysis-result');
    resultDiv.innerHTML = `
        <div class="error-box">
            <div class="error-header">❌ エラー</div>
            <div class="error-message">${escapeHtml(result.message || '不明なエラーが発生しました')}</div>
            ${result.suggestion ? `<div class="error-suggestion">💡 ${escapeHtml(result.suggestion)}</div>` : ''}
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


// ==================================================
// 指導シードの継続（Instructor's Selection Loop）
// ==================================================

function getLatestSelectedSeed(student, currentDate) {
    /**
     * §5.4 継続的指導サイクル
     * 直近の日誌で選択された seed を取得する
     */
    if (!student || !student.journals) return '';

    // 日付順にソートして、currentDate より前の日誌で selected_seed があるものを探す
    const pastJournals = student.journals
        .filter(j => j.selected_seed && j.date < currentDate)
        .sort((a, b) => (b.date || '').localeCompare(a.date || ''));

    return pastJournals.length > 0 ? pastJournals[0].selected_seed : '';
}

function loadPreviousTriggers() {
    const studentId = document.getElementById('student-select').value;
    const student = dashboardData.students.find(s => s.id == studentId);
    const dateStr = document.getElementById('daily-date').value;

    const displayEl = document.getElementById('previous-triggers-display');
    const textEl = document.getElementById('previous-triggers-text');

    if (student) {
        const seed = getLatestSelectedSeed(student, dateStr);
        if (seed) {
            displayEl.style.display = 'block';
            textEl.textContent = seed;
        } else {
            displayEl.style.display = 'none';
        }
    }
}


// ==================================================
// データ保存
// ==================================================
async function saveDataToServer() {
    try {
        const response = await fetch('/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dashboardData),
        });
        if (response.ok) {
            console.log('Data saved to server successfully');
        } else {
            console.error('Failed to save data to server');
            alert('データの保存に失敗しました。サーバーが動作しているか確認してください。');
        }
    } catch (error) {
        console.error('Error saving data:', error);
    }
}


// ==================================================
// 以下、既存機能（変更なし）
// ==================================================

function populateStudentSelector() {
    const selector = document.getElementById('student-select');
    selector.innerHTML = '';
    dashboardData.students.forEach(student => {
        const option = document.createElement('option');
        option.value = student.id;
        option.textContent = student.name;
        selector.appendChild(option);
    });
}

function syncSettingsForm(student) {
    if (!student) return;

    document.getElementById('pharmacy-slogan').value = globalSettings.slogan;
    document.getElementById('focus-keywords').value = globalSettings.keywords;

    const name = student.name;
    document.getElementById('settings-title').textContent = `学生情報の編集：${name}`;
    document.getElementById('save-settings-btn').textContent = "変更内容を保存して適用";
    document.getElementById('student-name').value = name;

    const settings = student.settings || {};
    document.getElementById('start-date').value = settings.startDate || "";
    document.getElementById('end-date').value = settings.endDate || "";
    document.getElementById('student-goal').value = settings.goal || "";
    document.getElementById('student-interests').value = settings.interests || "";

    const subtitleEl = document.querySelector('.subtitle');
    if (subtitleEl) {
        subtitleEl.textContent = `〜${globalSettings.slogan}〜`;
    }
}

function updateDashboard(student) {
    if (!student) return;

    const container = document.getElementById('story-board-container');
    container.innerHTML = '';

    const settings = student.settings || {};
    if (!settings.startDate) {
        container.innerHTML = '<div class="empty-state">設定画面で実習期間を設定すると、ここから成長の物語が始まります。</div>';
        return;
    }

    const targetWeeks = [1, 5, 11];
    targetWeeks.forEach((weekNum, index) => {
        const column = createStageColumn(weekNum, student);
        container.appendChild(column);

        if (index < targetWeeks.length - 1) {
            const connector = document.createElement('div');
            connector.className = 'stage-connector';
            connector.innerHTML = '<div class="arrow">→</div>';
            container.appendChild(connector);
        }
    });

    updateAiAdvice(student);
    renderCalendar(student);
}

function renderCalendar(student) {
    const calendarEl = document.getElementById('attendance-calendar');
    calendarEl.innerHTML = '';

    const settings = student.settings || {};
    if (!settings.startDate || !settings.endDate) return;

    const start = new Date(settings.startDate);
    const end = new Date(settings.endDate);

    const journalDates = new Set(student.journals.map(j => j.date));

    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        const dayEl = document.createElement('div');
        dayEl.className = 'calendar-day';
        dayEl.title = dateStr;
        dayEl.textContent = d.getDate();

        if (journalDates.has(dateStr)) {
            dayEl.classList.add('filled');
        }

        dayEl.addEventListener('click', () => {
            document.querySelectorAll('.calendar-day').forEach(el => el.classList.remove('active'));
            dayEl.classList.add('active');

            const dateInput = document.getElementById('daily-date');
            dateInput.value = dateStr;
            loadJournalForDate(dateStr);
        });

        calendarEl.appendChild(dayEl);
    }
}

function createStageColumn(weekNum, student) {
    const col = document.createElement('div');
    col.className = 'stage-column';

    const themes = {
        1: { icon: '⚙️', name: '技術の摩擦' },
        5: { icon: '💊', name: '知識の接続' },
        11: { icon: '🤝', name: '生活の翻訳' }
    };
    const theme = themes[weekNum] || { icon: '📝', name: '成長の過程' };

    col.innerHTML = `
        <div class="stage-header">
            <div class="stage-icon">${theme.icon}</div>
            <div class="stage-info">
                <h2>Week ${weekNum}</h2>
                <p class="stage-theme">${theme.name}</p>
            </div>
        </div>
        <div class="content-area"></div>
    `;

    const contentArea = col.querySelector('.content-area');

    const trigger = student.growth_triggers.find(g => g.description.includes(`Week ${weekNum}`));
    if (trigger) {
        const triggerEl = document.createElement('div');
        triggerEl.className = 'growth-trigger-card';
        triggerEl.innerHTML = `
            <div class="trigger-icon">🌱</div>
            <div class="trigger-desc">${trigger.description}</div>
        `;
        contentArea.appendChild(triggerEl);
    }

    const weekInsights = student.insights.filter(insight => {
        const journal = student.journals.find(j => j.id === insight.journal_id);
        return journal && journal.week_number === weekNum;
    });

    weekInsights.forEach(insight => {
        const el = document.createElement('div');
        el.className = 'insight-card';
        el.innerHTML = `
            <div class="insight-header">
                <span class="badgem badge-${insight.type}">${insight.type}</span>
            </div>
            <div class="insight-text">"${insight.snippet}"</div>
            <div class="insight-reason">💡 ${insight.reason}</div>
        `;
        contentArea.appendChild(el);
    });

    if (contentArea.innerHTML === '') {
        contentArea.innerHTML = '<div class="empty-state">日誌を入力すると、ここに「気づき」が積み上がります。</div>';
    }

    // 週次レビューの追加（もしあれば）
    if (student.weekly_reviews && student.weekly_reviews[weekNum]) {
        const review = student.weekly_reviews[weekNum];
        const reviewEl = createWeeklyReviewElement(review);
        col.appendChild(reviewEl);
    }

    return col;
}

function createWeeklyReviewElement(review) {
    const card = document.createElement('div');
    card.className = 'weekly-review-card';

    const r = review.weekly_review || {};
    const s = review.internal_scores || {};
    const lenses = s.lenses || {};

    let lensHTML = '';
    const lensLabels = {
        insight_on_lifestyle: "生活背景",
        non_verbal_clues: "言葉の裏",
        continuous_relationship: "線の関わり",
        community_resources: "地域資源",
        professional_proactivity: "職能の滲み出し"
    };

    for (const [key, label] of Object.entries(lensLabels)) {
        const val = lenses[key] || 0;
        const percent = (val / 5.0) * 100;
        lensHTML += `
            <div class="score-item">
                <span class="score-label">${label}</span>
                <div class="score-bar-container">
                    <div class="score-bar-fill" style="width: ${percent}%;"></div>
                </div>
                <span class="score-value">${val.toFixed(1)}</span>
            </div>
        `;
    }

    card.innerHTML = `
        <div class="weekly-review-header">
            <span class="icon">📊</span>
            <h3 style="margin:0; font-size:1.1rem; color:#1e40af;">Weekly Review</h3>
        </div>
        
        <div class="weekly-review-section">
            <div class="weekly-review-label">📈 成長の物語</div>
            <div class="weekly-review-content">${escapeHtml(r.growth_story || '')}</div>
        </div>
        
        <div class="weekly-review-section">
            <div class="weekly-review-label">👏 今週の白眉</div>
            <div class="weekly-review-content">${escapeHtml(r.key_achievements || '')}</div>
        </div>

        <div class="weekly-review-section">
            <div class="weekly-review-label">💡 思考の癖</div>
            <div class="weekly-review-content">${escapeHtml(r.habitual_patterns || '')}</div>
        </div>

        <div class="weekly-review-section">
            <div class="weekly-review-label">🏁 来週の目標</div>
            <div class="weekly-review-content">${escapeHtml(r.next_week_goals || '')}</div>
        </div>

        <!-- 指導者用内部スコア（指導者モード時のみ表示） -->
        <div class="internal-score-box">
            <div class="weekly-review-label" style="color: #6366f1; border-bottom: 1px solid #ddd; margin-bottom: 10px;">👨‍🏫 指導者用内部評価</div>
            <div class="score-grid">
                ${lensHTML}
                <div class="score-item">
                    <span class="score-label">概念化Lv平均</span>
                    <span class="score-value" style="font-size: 1.2rem; color: #9333ea;">${(s.conceptualization_avg || 0).toFixed(2)}</span>
                </div>
                <div class="score-item">
                    <span class="score-label">主体性(SELF比率)</span>
                    <span class="score-value" style="font-size: 1.2rem; color: #0891b2;">${Math.round((s.self_reliance_ratio || 0) * 100)}%</span>
                </div>
            </div>
            <div class="weekly-review-label" style="margin-top: 15px; font-size: 0.8rem; color: #64748b;">現場での学生の非言語的変化</div>
            <div class="weekly-review-content" style="font-size: 0.85rem; background: #fff; padding: 8px; border-radius: 6px;">
                ${escapeHtml(s.instructor_notes_summary || 'なし')}
            </div>
        </div>
    `;
    return card;
}

async function performWeeklyAnalysis(student, weekNum) {
    const loadingEl = document.getElementById('weekly-loading');
    const btn = document.getElementById('generate-weekly-btn');

    loadingEl.style.display = 'inline-block';
    btn.disabled = true;

    try {
        // 当該週の日誌を集める
        const weekJournals = student.journals.filter(j => j.week_number === weekNum);

        const response = await fetch('/review_weekly', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                week_number: weekNum,
                journals: weekJournals,
                provider: document.getElementById('ai-provider-select')?.value || ''
            })
        });

        const result = await response.json();

        if (result.error) {
            alert("エラー: " + result.message);
        } else {
            // 保存
            if (!student.weekly_reviews) student.weekly_reviews = {};
            student.weekly_reviews[weekNum] = result;

            await saveDataToServer();
            updateDashboard(student);
            alert(`Week ${weekNum} の週次分析が完了しました！\nStory Board で確認できます。`);
        }
    } catch (e) {
        alert("通信エラーが発生しました: " + e.message);
    } finally {
        loadingEl.style.display = 'none';
        btn.disabled = false;
    }
}

function updateAiAdvice(student) {
    const adviceContent = document.getElementById('ai-advice-content');
    let advice = "";

    if (student.name.includes("中﨑")) {
        advice = "<strong>指導のポイント:</strong> 実習初期の「正解探し」から、11週目には「患者の生活背景」を考慮した判断へと大きく視座が移動しています。この変化を具体的にフィードバックし、自信を持たせてください。";
    } else if (student.name.includes("渡辺")) {
        advice = "<strong>指導のポイント:</strong> 豊富な知識を臨床現場でどう応用するか、試行錯誤の跡が見られます。失敗を恐れずに提案できた点を評価しましょう。";
    } else {
        advice = "<strong>指導のポイント:</strong> 全体を通して着実な成長が見られます。特にコミュニケーションの質的変化に注目して声をかけてみてください。";
    }

    adviceContent.innerHTML = `<div class="advice-box">${advice}</div>`;
}

function clearDailyInterface() {
    document.getElementById('journal-practical').value = '';
    document.getElementById('journal-unachieved').value = '';
    document.getElementById('instructor-notes').value = '';
    document.getElementById('feedback-input').value = '';

    const resultDiv = document.getElementById('daily-analysis-result');
    if (resultDiv) {
        resultDiv.innerHTML = '<div class="empty-state-sm">日誌を入力して解析ボタンを押してね</div>';
    }

    const suggestDiv = document.getElementById('daily-suggestions');
    if (suggestDiv) {
        suggestDiv.innerHTML = '';
    }

    const seedCard = document.getElementById('seed-selection-card');
    if (seedCard) {
        seedCard.style.display = 'none';
    }

    document.getElementById('daily-date').valueAsDate = new Date();
    loadPreviousTriggers();
}

function loadJournalForDate(dateStr) {
    const selector = document.getElementById('student-select');
    if (!selector) return;
    const studentId = selector.value;
    const student = dashboardData.students.find(s => s.id == studentId);

    const practicalInput = document.getElementById('journal-practical');
    const unachievedInput = document.getElementById('journal-unachieved');
    const instructorInput = document.getElementById('instructor-notes');
    const feedbackInput = document.getElementById('feedback-input');

    if (student) {
        const journal = student.journals.find(j => j.date === dateStr);
        if (journal) {
            practicalInput.value = journal.practical_content || journal.content || "";
            unachievedInput.value = journal.unachieved_point || "";
            instructorInput.value = journal.instructor_notes || "";
            feedbackInput.value = journal.feedback || "";

            // 保存済みのAI解析結果があれば表示
            if (journal.ai_analysis && !journal.ai_analysis.error) {
                if (journal.ai_analysis.sos_alert) {
                    renderSOSAlert(journal.ai_analysis);
                } else {
                    renderBriefingReport(journal.ai_analysis);
                }
            }
        } else {
            practicalInput.value = "";
            unachievedInput.value = "";
            instructorInput.value = "";
            feedbackInput.value = "";
        }

        // 前回の継続フラグを更新
        loadPreviousTriggers();
    }
}

function calculateWeekNumber(dateStr, startDateStr) {
    if (!startDateStr) return 1;
    const date = new Date(dateStr);
    const start = new Date(startDateStr);
    const diffTime = date - start;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return Math.floor(Math.max(0, diffDays) / 7) + 1;
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// 初期化
init();
