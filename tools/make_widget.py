# speaking.html(단독 스피킹 앱) → 단어 앱(index.html) 안에 넣는 스피킹 위젯(window.EJSpeak) 생성
# 사용법: python3 tools/make_widget.py speaking.html index.html
#   speaking.html 을 고친 뒤 이 명령을 실행하면 index.html 안의 위젯 부분만 새로 바뀝니다.
import re, sys, json
src = open(sys.argv[1], encoding='utf-8').read()
out_path = sys.argv[2]

def between(s, a, b):
    i = s.index(a) + len(a); j = s.index(b, i); return s[i:j]

css = between(src, '<style>', '</style>')
body = src[src.index('<div class="app" id="app">'):src.index('<script>')]
js = between(src, "<script>\n'use strict';", '</script>')

def rep(s, a, b, count=1):
    n = s.count(a)
    assert n == count, (n, a[:80])
    return s.replace(a, b)

# ---------- CSS: 그림자 DOM 안에서만 적용 ----------
css = rep(css, ':root{', ':host{all:initial;')
css = rep(css, 'html,body{margin:0;height:100%}\n', '')
css = rep(css, 'body{\n  background:var(--cream);', '.wrap{\n  height:100%;background:var(--cream);')
css = rep(css, '.app{display:flex;flex-direction:column;height:100vh;height:100dvh;', '.app{display:flex;flex-direction:column;height:100%;')
css += '\n.wrap{position:relative}\n.overlay{position:absolute}\n'

# ---------- HTML ----------
body = rep(body, '<button id="settingsBtn" class="icon-btn" title="설정" aria-label="설정">⚙️</button>',
  '<button id="settingsBtn" class="icon-btn" title="설정" aria-label="설정">⚙️</button>\n      <button id="closeBtn" class="icon-btn" title="나가기" aria-label="나가기">✕</button>')
# 학생 정보·주제·단어는 숙제에서 정해지므로 설정 화면에서 숨김
for title in ['<h3>💬 오늘의 주제</h3>', '<h3>🎯 오늘의 목표 단어 (10개)</h3>']:
    k = body.index(title); c = body.rindex('<div class="card">', 0, k)
    body = body[:c] + '<div class="card hidden">' + body[c+len('<div class="card">'):]
body = rep(body, '💾 저장하고 대화하기', '💾 저장하기')
# 학생 정보 카드: 영어 이름만 (학년은 숙제에서 정함)
body = rep(body, '<h3>🙋 학생 정보</h3>', '<h3>🙋 내 영어 이름</h3>')
body = rep(body, '<label for="sName">학생 이름 (영어 이름도 좋아요)</label>', '<label for="sName">영어 이름 (선택) — 선생님이 이 이름으로 불러 줘요. 비우면 가입한 이름을 써요.</label>')
body = rep(body, '<div class="field">\n          <label>학년 (AI 난이도)</label>', '<div class="field hidden">\n          <label>학년 (AI 난이도)</label>')
html = '<div class="wrap">' + body + '</div>'

# ---------- JS ----------
js = rep(js, "const $ = (id) => document.getElementById(id);", "let ROOT = null, HOST = null;\nconst $ = (id) => ROOT.getElementById(id);")
js = js.replace('document.querySelectorAll(', 'ROOT.querySelectorAll(').replace('document.querySelector(', 'ROOT.querySelector(')
js = rep(js, "const EJ_DEBUG = window.EJ_DEBUG = {", "const EJ_DEBUG = window.EJ_SPEAK_DEBUG = {")

# 숙제(ASSIGN)에서 주제·단어·이름·학년을 가져옴
js = rep(js, "function gradeText(g = settings.grade)", "let ASSIGN = null;   // { hwId, topic, words:[{word,meaning}], level, name, onSubmit, preview }\nfunction curGrade() { return ASSIGN && ASSIGN.level === 'middle' ? 'middle' : 'elementary'; }\nfunction gradeText(g = curGrade())")
js = rep(js, "function gradeKo(g = settings.grade)", "function gradeKo(g = curGrade())")
js = rep(js, "function targetWords() { return parseWords(settings.wordsText).slice(0, CONFIG.MAX_TARGET_WORDS); }",
  "function targetWords() { return ((ASSIGN && ASSIGN.words) || []).filter(w => w && w.word).slice(0, CONFIG.MAX_TARGET_WORDS); }")
js = rep(js, "function isConfigured() { return (!!getApiKey() || EJ_DEBUG.mock) && !!(settings.currentTopic || '').trim(); }",
  "function isConfigured() { return (!!getApiKey() || EJ_DEBUG.mock) && !!(ASSIGN && ASSIGN.topic); }")
js = rep(js, "    topic: (settings.currentTopic || '').trim(),\n    studentName: (settings.name || '').trim(),\n    grade: settings.grade,",
  "    topic: ASSIGN.topic,\n    studentName: (ASSIGN.name || '').trim(),\n    grade: curGrade(),\n    hwId: ASSIGN.hwId || '',")
js = rep(js, "  const opening = settings.grade === 'middle'", "  const opening = curGrade() === 'middle'")
js = rep(js, "    const base = settings.grade === 'middle' ? 0.98 : 0.9;", "    const base = curGrade() === 'middle' ? 0.98 : 0.9;")
js = rep(js, "function saveCurrent() { if (state.session) saveJSON(LS.current, state.session); }",
  "function curKey() { return LS.current + ':' + ((ASSIGN && ASSIGN.hwId) || 'free'); }\nfunction saveCurrent() { if (state.session) saveJSON(curKey(), state.session); }")
js = rep(js, "  if (!isConfigured()) { openSettings(); return; }", "  if (!isConfigured()) { openSettings(); toast('먼저 API 키를 넣어 주세요 🔑'); return; }")

# 리포트: 선생님께 제출
js = rep(js, "  try { localStorage.removeItem(LS.current); } catch {}", "  try { localStorage.removeItem(curKey()); } catch {}")
js = rep(js, """    <button class="btn big" id="rNew" type="button">🦒 새 대화 시작</button>`;""",
"""    ${ASSIGN && ASSIGN.onSubmit ? '<button class="btn big" id="rSubmit" type="button">📤 선생님께 제출하기</button>' : ''}
    <p class="meta" id="rMsg" style="margin:0;text-align:center"></p>
    <button class="btn big ghost" id="rNew" type="button">${ASSIGN && ASSIGN.onSubmit ? '제출하지 않고 나가기' : '닫기'}</button>`;""")
js = rep(js, "  $('rNew').onclick = () => { $('reportScreen').classList.add('hidden'); startNewSession(true); };",
"""  $('rNew').onclick = () => {
    if (ASSIGN && ASSIGN.onSubmit && !r.submitted && !confirm('제출하지 않고 나갈까요? (기록은 이 기기에 남아요)')) return;
    closeWidget();
  };
  const sb = $('rSubmit');
  if (sb) sb.onclick = async () => {
    sb.disabled = true; sb.textContent = '제출하는 중…'; $('rMsg').textContent = '';
    try {
      await ASSIGN.onSubmit(r);
      r.submitted = true;
      sb.textContent = '✅ 제출했어요!';
      $('rNew').textContent = '숙제 화면으로 돌아가기';
      toast('선생님께 제출했어요! 수고했어요 🎉', 'party', 3000);
    } catch (e) {
      sb.disabled = false; sb.textContent = '📤 다시 제출하기';
      $('rMsg').textContent = '제출하지 못했어요. 인터넷 연결을 확인하고 다시 눌러 주세요.';
    }
  };""")

# 세션 시작/복원: 숙제별로 저장
js = rep(js, """  const cur = loadJSON(LS.current, null);
  if (cur && cur.topic === (settings.currentTopic || '').trim() && Array.isArray(cur.messages)) {""",
"""  const cur = loadJSON(curKey(), null);
  if (cur && cur.topic === ASSIGN.topic && Array.isArray(cur.messages)) {""")

# 설정: 주제·단어 관련 처리 제거
s0 = js.index('function openSettings() {'); s1 = js.index('/** 키 테스트')
js = js[:s0] + r'''function openSettings() {
  recognizer.stop(false);
  $('sApiKey').value = getApiKey();
  $('sApiKey').type = 'password'; $('sKeyShow').textContent = '보기';
  $('sKeyResult').textContent = ''; $('sKeyResult').className = 'test-result';
  $('sName').value = settings.engName || '';
  $('sAutoTTS').checked = settings.autoTTS;
  $('sFbOpen').checked = settings.feedbackAlwaysOpen;
  ROOT.querySelectorAll('input[name=sFbStyle]').forEach(r => { r.checked = r.value === (settings.feedbackStyle || 'teacher'); });
  $('sMicAutoSend').checked = settings.micAutoSend;
  $('sRpm').value = settings.rpm;
  $('sRpd').value = settings.rpd;
  $('sModelPrimary').value = settings.modelPrimary; $('sModelPrimary').placeholder = CONFIG.MODEL_PRIMARY;
  $('sModelFallback').value = settings.modelFallback; $('sModelFallback').placeholder = CONFIG.MODEL_FALLBACK;
  updateHistoryInfo();
  $('settingsScreen').classList.remove('hidden');
}
function closeSettings() { $('settingsScreen').classList.add('hidden'); }
function updateHistoryInfo() {
  const all = loadJSON(LS.sessions, []);
  $('sHistoryInfo').textContent = all.length
    ? `이 기기에 ${all.length}개의 대화 기록이 있어요. (마지막: ${all[all.length - 1].date} · ${all[all.length - 1].topic})`
    : '아직 저장된 대화 기록이 없어요.';
  const u = getUsage();
  $('sUsageInfo').textContent = `오늘 ${u.count}회 사용${u.stopped ? ' · 사용 중지 상태' : ''}.`;
}
function saveSettingsFromForm() {
  const key = $('sApiKey').value.trim();
  if (!key && !EJ_DEBUG.mock) { toast('API 키를 입력해 주세요 🔑'); $('sApiKey').focus(); return; }
  setApiKey(key);
  const engName = $('sName').value.trim();
  const nameChanged = engName !== (settings.engName || '');
  Object.assign(settings, {
    engName,
    autoTTS: $('sAutoTTS').checked,
    feedbackAlwaysOpen: $('sFbOpen').checked,
    feedbackStyle: (ROOT.querySelector('input[name=sFbStyle]:checked') || {}).value || 'teacher',
    micAutoSend: $('sMicAutoSend').checked,
    rpm: Math.min(60, Math.max(1, parseInt($('sRpm').value, 10) || CONFIG.DEFAULT_RPM)),
    rpd: Math.min(5000, Math.max(1, parseInt($('sRpd').value, 10) || CONFIG.DEFAULT_RPD)),
    modelPrimary: $('sModelPrimary').value.trim(),
    modelFallback: $('sModelFallback').value.trim(),
  });
  saveSettings();
  closeSettings();
  hideNotice();
  if (nameChanged && ASSIGN) {
    ASSIGN.name = engName || ASSIGN.baseName || '';
    if (state.session && !userTurns().length) { startNewSession(false); toast('저장했어요 ✅'); return; }
    if (state.session) state.session.studentName = ASSIGN.name;
  }
  renderHeader();
  renderAllMessages();
  refreshLock();
  toast('저장했어요 ✅');
}

''' + js[s1:]

# 이벤트
js = rep(js, """  $('settingsClose').onclick = () => {
    if (!isConfigured()) { toast('API 키와 주제를 먼저 저장해 주세요'); return; }
    closeSettings();
  };""", """  $('settingsClose').onclick = closeSettings;
  $('closeBtn').onclick = () => {
    if (state.busy) return;
    closeWidget();
  };""")
js = rep(js, "  $('sTopics').addEventListener('input', () => fillTopicSelect($('sTopic').value));\n  $('sWords').addEventListener('input', updateWordPreview);\n", "")

# 시작: 자동 실행 대신 EJSpeak.open()
s0 = js.index("function init() {")
js = js[:s0] + r'''let mounted = false;
function mount() {
  HOST = document.createElement('div');
  HOST.id = 'ej-speak-host';
  HOST.style.cssText = 'position:fixed;inset:0;z-index:2147483000;display:none';
  ROOT = HOST.attachShadow({ mode: 'open' });
  ROOT.innerHTML = '<style>' + WIDGET_CSS + '</style>' + WIDGET_HTML;
  document.body.appendChild(HOST);
  // 위젯 안의 키보드·클릭이 뒤쪽 단어 앱으로 새어 나가지 않게 막음
  ['keydown', 'keyup', 'keypress', 'input', 'change', 'paste', 'click', 'pointerdown', 'pointerup', 'drop', 'dragover']
    .forEach(t => HOST.addEventListener(t, e => e.stopPropagation()));
  bindEvents();
  if (!SR) $('micBtn').classList.add('hidden');
  mounted = true;
}
let prevOverflow = '';
function closeWidget() {
  recognizer.stop(false);
  tts.stop();
  clearTimeout(state.lockTimer);
  $('reportScreen').classList.add('hidden');
  $('settingsScreen').classList.add('hidden');
  HOST.style.display = 'none';
  document.body.style.overflow = prevOverflow;
  const cb = ASSIGN && ASSIGN.onClose;
  state.session = null;
  ASSIGN = null;
  if (cb) try { cb(); } catch {}
}
/**
 * 스피킹 열기
 * opts = { hwId, topic, words:[{word, meaning}], level:'elementary'|'middle', name,
 *          onSubmit: async (report) => {...}  // 없으면 제출 버튼 없음 (원장 미리보기)
 *          onClose: () => {} }
 */
function open(opts) {
  if (!mounted) mount();
  ASSIGN = Object.assign({ words: [], level: 'elementary', name: '' }, opts || {});
  ASSIGN.topic = String(ASSIGN.topic || '').trim() || 'Free talk';
  settings = Object.assign({}, DEFAULT_SETTINGS, loadJSON(LS.settings, {}));
  ASSIGN.baseName = ASSIGN.name;
  if (settings.engName) ASSIGN.name = settings.engName;   // 영어 이름이 있으면 그 이름으로 불러 줌
  prevOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  HOST.style.display = 'block';
  hideNotice();
  $('reportScreen').classList.add('hidden');
  if (!SR) showNotice('이 브라우저는 음성 인식을 지원하지 않아요. 글자로 입력해 주세요. (Chrome / Edge 권장)', 'warn');
  restoreOrStart();
  if (!isConfigured()) { openSettings(); toast('처음 한 번만 Gemini API 키를 넣어 주세요 🔑', '', 3500); }
}
window.EJSpeak = { open, close: () => mounted && HOST.style.display !== 'none' && closeWidget(), parseWords };
'''

js = js.replace("let settings = Object.assign", "let settings = Object.assign", 1)
widget = "/* ===== EJ Speaking 위젯 (tools/make_widget.py 로 speaking.html 에서 자동 생성) ===== */\n(function () {\n'use strict';\nconst WIDGET_CSS = " + json.dumps(css, ensure_ascii=False) + ";\nconst WIDGET_HTML = " + json.dumps(html, ensure_ascii=False) + ";\n" + js + "\n})();\n"
assert '</script' not in widget.lower()
if out_path.endswith('.html'):
    # index.html 안의 <script id="ej-speak-widget"> ... </script> 부분만 교체
    page = open(out_path, encoding='utf-8').read()
    a = '<script id="ej-speak-widget">'
    i = page.index(a) + len(a); j = page.index('</script>', i)
    page = page[:i] + '\n' + widget + page[j:]
    open(out_path, 'w', encoding='utf-8').write(page)
else:
    open(out_path, 'w', encoding='utf-8').write(widget)
print('widget bytes', len(widget.encode()))
