// 履歴書フォーム(rirekisho.html)の挙動。
"use strict";

const DRAFT_KEY = "yaml_cv:rirekisho:draft";
const LIST_FIELDS = ["education", "experience", "licences", "awards"];
const SCALAR_FIELDS = [
  "date", "name_kana", "name", "birth_day", "gender", "cell_phone", "email",
  "address_kana", "address", "address_zip", "tel", "fax",
  "address_kana2", "address2", "address_zip2", "tel2", "fax2",
  "degree", "degree_year", "degree_affiliation", "thesis_title",
  "commuting_time", "dependents", "spouse", "supporting_spouse",
];
const TEXT_FIELDS = ["teaching", "affiliated_society", "notices", "hobby", "motivation", "request"];

const form = document.getElementById("rirekisho-form");
const rowTemplate = document.getElementById("history-row-template");

function addHistoryRow(listName, item = {}) {
  const container = document.getElementById(`${listName}-rows`);
  const node = rowTemplate.content.cloneNode(true);
  const rowEl = node.querySelector("[data-history-row]");
  rowEl.querySelector('[data-field="year"]').value = item.year || "";
  rowEl.querySelector('[data-field="month"]').value = item.month || "";
  rowEl.querySelector('[data-field="value"]').value = item.value || "";
  rowEl.querySelector("[data-remove-row]").addEventListener("click", () => {
    rowEl.remove();
  });
  container.appendChild(rowEl);
}

document.querySelectorAll("[data-add-row]").forEach((btn) => {
  btn.addEventListener("click", () => addHistoryRow(btn.dataset.addRow));
});

function collectFormData() {
  const data = {};
  for (const name of [...SCALAR_FIELDS, ...TEXT_FIELDS]) {
    data[name] = form.elements[name] ? form.elements[name].value : "";
  }
  for (const listName of LIST_FIELDS) {
    const rows = document.querySelectorAll(`#${listName}-rows [data-history-row]`);
    data[listName] = Array.from(rows).map((row) => ({
      year: row.querySelector('[data-field="year"]').value,
      month: row.querySelector('[data-field="month"]').value,
      value: row.querySelector('[data-field="value"]').value,
    }));
  }
  return data;
}

function applyFormData(data) {
  if (!data) return;
  for (const name of [...SCALAR_FIELDS, ...TEXT_FIELDS]) {
    if (form.elements[name] && data[name] !== undefined) {
      form.elements[name].value = data[name];
    }
  }
  for (const listName of LIST_FIELDS) {
    document.getElementById(`${listName}-rows`).innerHTML = "";
    (data[listName] || []).forEach((item) => addHistoryRow(listName, item));
  }
}

function ensureAtLeastOneRowEach() {
  for (const listName of LIST_FIELDS) {
    const container = document.getElementById(`${listName}-rows`);
    if (container.children.length === 0) addHistoryRow(listName);
  }
}

// 初期化: 下書きを復元、無ければ各リストに空行を1つ用意
const draft = loadDraft(DRAFT_KEY);
if (draft) {
  applyFormData(draft);
} else {
  ensureAtLeastOneRowEach();
}

// 入力の度に下書き保存
form.addEventListener("input", () => saveDraft(DRAFT_KEY, collectFormData()));
form.addEventListener("click", () => saveDraft(DRAFT_KEY, collectFormData()));

// data.yaml の読み込み
document.getElementById("btn-import").addEventListener("click", async () => {
  const fileInput = document.getElementById("import-file");
  const statusEl = document.getElementById("import-status");
  try {
    const text = await readFileAsText(fileInput);
    const response = await fetch("/import/rirekisho", {
      method: "POST",
      headers: { "Content-Type": "text/plain; charset=utf-8" },
      body: text,
    });
    if (!response.ok) throw new Error(`読み込みに失敗しました (${response.status})`);
    const data = await response.json();
    applyFormData(data);
    ensureAtLeastOneRowEach();
    saveDraft(DRAFT_KEY, collectFormData());
    flashStatus(statusEl, "読み込みました");
  } catch (err) {
    flashStatus(statusEl, err.message, 5000);
  }
});

// data.yaml の書き出し（クライアント側で簡易YAML化はせず、サーバに変換してもらう）
document.getElementById("btn-export-yaml").addEventListener("click", async () => {
  const statusEl = document.getElementById("import-status");
  try {
    const response = await fetch("/export/rirekisho", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectFormData()),
    });
    if (!response.ok) throw new Error(`書き出しに失敗しました (${response.status})`);
    const text = await response.text();
    downloadText(text, "data.yaml", "application/x-yaml");
  } catch (err) {
    flashStatus(statusEl, err.message, 5000);
  }
});

// 入力クリア
document.getElementById("btn-clear").addEventListener("click", () => {
  if (!confirm("入力内容をすべてクリアしますか？")) return;
  form.reset();
  document.querySelectorAll("[id$='-rows']").forEach((el) => (el.innerHTML = ""));
  ensureAtLeastOneRowEach();
  localStorage.removeItem(DRAFT_KEY);
});

// 生成
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const statusEl = document.getElementById("generate-status");
  const photoInput = document.getElementById("photo-file");
  const format = form.elements["format"].value;
  const payload = collectFormData();

  const body = new FormData();
  body.append("payload", JSON.stringify(payload));
  body.append("format", format);
  if (photoInput.files && photoInput.files[0]) {
    body.append("photo", photoInput.files[0]);
  }

  flashStatus(statusEl, "生成中...", 0);
  try {
    const response = await fetch("/generate/rirekisho-form", { method: "POST", body });
    await downloadResponse(response, `rirekisho.${format === "pdf" ? "pdf" : format === "excel" ? "xlsx" : "docx"}`);
    flashStatus(statusEl, "生成しました");
  } catch (err) {
    flashStatus(statusEl, err.message, 6000);
  }
});
