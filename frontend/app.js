const API = window.API_BASE_URL;
let conversationId = null;
// 선택 기간. 비어 있으면 전체. 요약·목록·AI 답변이 모두 이 기간을 따른다.
let period = { start: "", end: "" };

function periodQuery() {
  const q = new URLSearchParams();
  if (period.start) q.set("start", period.start);
  if (period.end) q.set("end", period.end);
  const s = q.toString();
  return s ? "?" + s : "";
}

const $ = (id) => document.getElementById(id);
const chatLog = $("chat-log");

async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

/* ---------- 데이터 요약 ---------- */
async function loadSummary() {
  try {
    const s = await api("/api/data/summary" + periodQuery());
    if (!s.count) {
      $("summary-content").textContent = "선택한 기간에 데이터가 없습니다.";
      return;
    }
    const m = s.metrics;
    $("summary-content").innerHTML =
      `기간 <b>${s.period}</b> · <b>${s.count}</b>개<br>` +
      `평균 <b>${m.average.toLocaleString()}</b> MWh · ` +
      `최대 ${m.max.toLocaleString()} <span class="dim">(${m.max_date})</span> · ` +
      `최소 ${m.min.toLocaleString()} <span class="dim">(${m.min_date})</span><br>` +
      `추세: <b>${s.trend}</b><br>` +
      `연도별 평균: ${s.yearly.map((y) => `${y.key} <b>${y.average.toLocaleString()}</b>`).join(" · ")}` +
      `<details><summary>월별 집계 (${s.monthly.length}개월)</summary><table>` +
      `<tr><th>월</th><th>평균</th><th>최대</th><th>최소</th></tr>` +
      s.monthly.map((g) =>
        `<tr><td>${g.key}</td><td>${g.average.toLocaleString()}</td>` +
        `<td>${g.max.toLocaleString()} <span class="dim">${g.max_date.slice(5)}</span></td>` +
        `<td>${g.min.toLocaleString()} <span class="dim">${g.min_date.slice(5)}</span></td></tr>`
      ).join("") +
      `</table></details>`;
  } catch (e) {
    $("summary-content").textContent = "요약 로드 실패: " + e.message;
  }
}

/* ---------- 채팅 ---------- */
function addMsg(role, text, cls = "") {
  const div = document.createElement("div");
  div.className = `msg ${role} ${cls}`;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
  return div;
}

$("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("chat-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  $("send-btn").disabled = true;
  addMsg("user", text);
  const loading = addMsg("assistant", "답변 생성 중…", "loading");
  try {
    const r = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message: text,
        conversation_id: conversationId,
        period: { start: period.start || null, end: period.end || null },
      }),
    });
    loading.remove();
    addMsg("assistant", r.reply);
    conversationId = r.conversation_id;
    loadConversations();
  } catch (err) {
    loading.remove();
    addMsg("assistant", "오류: " + err.message, "loading");
  } finally {
    $("send-btn").disabled = false;
  }
});

/* ---------- 대화 기록 ---------- */
async function loadConversations() {
  try {
    const r = await api("/api/conversations");
    const ul = $("conv-list");
    ul.innerHTML = "";
    r.items.forEach((c) => {
      const li = document.createElement("li");
      if (c.id === conversationId) li.classList.add("active");
      const span = document.createElement("span");
      span.textContent = c.title;
      li.appendChild(span);
      const del = document.createElement("button");
      del.className = "danger";
      del.textContent = "삭제";
      del.onclick = async (e) => {
        e.stopPropagation();
        await api(`/api/conversations/${c.id}`, { method: "DELETE" });
        if (c.id === conversationId) newChat();
        loadConversations();
      };
      li.appendChild(del);
      li.onclick = () => loadConversation(c.id);
      ul.appendChild(li);
    });
  } catch (e) { /* 목록 실패는 조용히 넘어감 */ }
}

async function loadConversation(id) {
  const c = await api(`/api/conversations/${id}`);
  conversationId = id;
  chatLog.innerHTML = "";
  c.messages.forEach((m) => addMsg(m.role, m.content));
  loadConversations();
}

function newChat() {
  conversationId = null;
  chatLog.innerHTML = "";
  addMsg("assistant", "안녕하세요! 저장된 전력수요 데이터를 기반으로 답해 드려요.");
  loadConversations();
}
$("new-chat-btn").addEventListener("click", newChat);

/* ---------- 데이터 관리 (CRUD) ---------- */
async function loadData() {
  try {
    const r = await api("/api/data" + periodQuery());
    const ul = $("data-list");
    ul.innerHTML = "";
    r.items.slice(0, 50).forEach((d) => {
      const li = document.createElement("li");
      const info = document.createElement("span");
      info.innerHTML = `<b>${d.date}</b> ${Number(d.value).toLocaleString()}` +
        (d.memo ? ` <span class="memo">${d.memo}</span>` : "");
      li.appendChild(info);
      const del = document.createElement("button");
      del.className = "danger";
      del.textContent = "삭제";
      del.onclick = async () => {
        await api(`/api/data/${d.id}`, { method: "DELETE" });
        setStatus(`${d.date} 삭제됨`);
        loadData(); loadSummary();
      };
      li.appendChild(del);
      ul.appendChild(li);
    });
  } catch (e) {
    setStatus("데이터 로드 실패: " + e.message);
  }
}

function setStatus(msg) {
  $("data-status").textContent = msg;
  setTimeout(() => { $("data-status").textContent = ""; }, 3000);
}

$("data-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api("/api/data", {
      method: "POST",
      body: JSON.stringify({
        date: $("data-date").value,
        value: Number($("data-value").value),
        memo: $("data-memo").value,
      }),
    });
    setStatus("추가 완료");
    e.target.reset();
    loadData(); loadSummary();
  } catch (err) {
    setStatus("추가 실패: " + err.message);
  }
});

/* ---------- 기간 선택 ---------- */
$("period-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const start = $("period-start").value;
  const end = $("period-end").value;
  if (start && end && start > end) {
    $("summary-content").textContent = "시작일이 종료일보다 늦습니다.";
    return;
  }
  period = { start, end };
  loadSummary(); loadData();
});
$("period-reset").addEventListener("click", () => {
  $("period-start").value = "";
  $("period-end").value = "";
  period = { start: "", end: "" };
  loadSummary(); loadData();
});

/* ---------- 초기화 ---------- */
newChat();
loadSummary();
loadData();
