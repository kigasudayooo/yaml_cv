// 職務経歴書フォーム(shokumu.html)の挙動。
"use strict";

const DRAFT_KEY = "yaml_cv:shokumu:draft";

const form = document.getElementById("shokumu-form");
const tpl = (id) => document.getElementById(id).content;

function scheduleSave() {
  saveDraft(DRAFT_KEY, collectFormData());
}

// --- テキスト一覧（学歴・箇条書き・スキル項目・ブロック項目 共通） ---

function addTextListRow(container, value = "") {
  const node = tpl("tpl-text-list-row").cloneNode(true);
  const row = node.querySelector("[data-text-row]");
  row.querySelector("[data-line]").value = value;
  row.querySelector("[data-remove]").addEventListener("click", () => {
    row.remove();
    scheduleSave();
  });
  container.appendChild(row);
}

function collectTextList(container) {
  return Array.from(container.querySelectorAll("[data-text-row]")).map(
    (row) => row.querySelector("[data-line]").value
  );
}

// --- 補足情報 (key/value) 一覧 ---

function addMetaRow(container, key = "", value = "") {
  const node = tpl("tpl-meta-row").cloneNode(true);
  const row = node.querySelector("[data-meta-row]");
  row.querySelector("[data-meta-key]").value = key;
  row.querySelector("[data-meta-value]").value = value;
  row.querySelector("[data-remove]").addEventListener("click", () => {
    row.remove();
    scheduleSave();
  });
  container.appendChild(row);
}

function collectMetaList(container) {
  return Array.from(container.querySelectorAll("[data-meta-row]")).map((row) => ({
    key: row.querySelector("[data-meta-key]").value,
    value: row.querySelector("[data-meta-value]").value,
  }));
}

// --- スキル分類 ---

function addSkillGroup(container, group = {}) {
  const node = tpl("tpl-skill-group").cloneNode(true);
  const el = node.querySelector("[data-skill-group]");
  el.querySelector("[data-heading]").value = group.heading || "";
  const itemsEl = el.querySelector("[data-items]");
  (group.items || []).forEach((item) => addTextListRow(itemsEl, item));
  el.querySelector("[data-add-item]").addEventListener("click", () => {
    addTextListRow(itemsEl);
    scheduleSave();
  });
  el.querySelector("[data-remove]").addEventListener("click", () => {
    el.remove();
    scheduleSave();
  });
  container.appendChild(el);
}

function collectSkillGroups(container) {
  return Array.from(container.querySelectorAll("[data-skill-group]")).map((el) => ({
    heading: el.querySelector("[data-heading]").value,
    items: collectTextList(el.querySelector("[data-items]")),
  }));
}

// --- プロジェクト内の小見出しブロック ---

function addBlock(container, block = {}) {
  const node = tpl("tpl-block").cloneNode(true);
  const el = node.querySelector("[data-block]");
  el.querySelector("[data-heading]").value = block.heading || "";
  const itemsEl = el.querySelector("[data-items]");
  (block.items || []).forEach((item) => addTextListRow(itemsEl, item));
  el.querySelector("[data-add-item]").addEventListener("click", () => {
    addTextListRow(itemsEl);
    scheduleSave();
  });
  el.querySelector("[data-remove]").addEventListener("click", () => {
    el.remove();
    scheduleSave();
  });
  container.appendChild(el);
}

function collectBlocks(container) {
  return Array.from(container.querySelectorAll(":scope > [data-block]")).map((el) => ({
    heading: el.querySelector("[data-heading]").value,
    items: collectTextList(el.querySelector("[data-items]")),
  }));
}

// --- プロジェクト ---

function addProject(container, project = {}) {
  const node = tpl("tpl-project").cloneNode(true);
  const el = node.querySelector("[data-project]");
  el.querySelector("[data-name]").value = project.name || "";
  const metaEl = el.querySelector("[data-meta]");
  (project.meta || []).forEach((m) => addMetaRow(metaEl, m.key, m.value));
  el.querySelector("[data-add-meta]").addEventListener("click", () => {
    addMetaRow(metaEl);
    scheduleSave();
  });
  const blocksEl = el.querySelector("[data-blocks]");
  (project.blocks || []).forEach((b) => addBlock(blocksEl, b));
  el.querySelector("[data-add-block]").addEventListener("click", () => {
    addBlock(blocksEl);
    scheduleSave();
  });
  el.querySelector("[data-remove]").addEventListener("click", () => {
    el.remove();
    scheduleSave();
  });
  container.appendChild(el);
}

function collectProjects(container) {
  return Array.from(container.querySelectorAll(":scope > [data-project]")).map((el) => ({
    name: el.querySelector("[data-name]").value,
    meta: collectMetaList(el.querySelector("[data-meta]")),
    blocks: collectBlocks(el.querySelector("[data-blocks]")),
  }));
}

// --- 会社 ---

function addCompany(container, company = {}) {
  const node = tpl("tpl-company").cloneNode(true);
  const el = node.querySelector("[data-company]");
  el.querySelector("[data-name]").value = company.name || "";
  el.querySelector("[data-period]").value = company.period || "";
  const metaEl = el.querySelector("[data-meta]");
  (company.meta || []).forEach((m) => addMetaRow(metaEl, m.key, m.value));
  el.querySelector("[data-add-meta]").addEventListener("click", () => {
    addMetaRow(metaEl);
    scheduleSave();
  });
  const itemsEl = el.querySelector("[data-items]");
  (company.items || []).forEach((item) => addTextListRow(itemsEl, item));
  el.querySelector("[data-add-item]").addEventListener("click", () => {
    addTextListRow(itemsEl);
    scheduleSave();
  });
  const projectsEl = el.querySelector("[data-projects]");
  (company.projects || []).forEach((p) => addProject(projectsEl, p));
  el.querySelector("[data-add-project]").addEventListener("click", () => {
    addProject(projectsEl);
    scheduleSave();
  });
  el.querySelector("[data-remove]").addEventListener("click", () => {
    el.remove();
    scheduleSave();
  });
  container.appendChild(el);
}

function collectCompanies(container) {
  return Array.from(container.querySelectorAll(":scope > [data-company]")).map((el) => ({
    name: el.querySelector("[data-name]").value,
    period: el.querySelector("[data-period]").value,
    meta: collectMetaList(el.querySelector("[data-meta]")),
    items: collectTextList(el.querySelector("[data-items]")),
    projects: collectProjects(el.querySelector("[data-projects]")),
  }));
}

// --- フォーム全体 ---

const educationList = document.getElementById("education-list");
const skillGroups = document.getElementById("skill-groups");
const companies = document.getElementById("companies");

document.getElementById("btn-add-education").addEventListener("click", () => {
  addTextListRow(educationList);
  scheduleSave();
});
document.getElementById("btn-add-skill-group").addEventListener("click", () => {
  addSkillGroup(skillGroups);
  scheduleSave();
});
document.getElementById("btn-add-company").addEventListener("click", () => {
  addCompany(companies);
  scheduleSave();
});

function collectFormData() {
  return {
    name: form.elements["name"].value,
    summary: form.elements["summary"].value,
    education: collectTextList(educationList),
    skill_groups: collectSkillGroups(skillGroups),
    companies: collectCompanies(companies),
  };
}

function clearContainers() {
  educationList.innerHTML = "";
  skillGroups.innerHTML = "";
  companies.innerHTML = "";
}

function applyFormData(data) {
  if (!data) return;
  form.elements["name"].value = data.name || "";
  form.elements["summary"].value = data.summary || "";
  clearContainers();
  (data.education || []).forEach((item) => addTextListRow(educationList, item));
  (data.skill_groups || []).forEach((g) => addSkillGroup(skillGroups, g));
  (data.companies || []).forEach((c) => addCompany(companies, c));
}

// 初期化: 下書きを復元。無ければ最低限の空行を用意。
const draft = loadDraft(DRAFT_KEY);
if (draft) {
  applyFormData(draft);
} else {
  addTextListRow(educationList);
  addSkillGroup(skillGroups);
  addCompany(companies);
}

form.addEventListener("input", scheduleSave);
form.addEventListener("click", scheduleSave);

// cv.md の読み込み
document.getElementById("btn-import").addEventListener("click", async () => {
  const fileInput = document.getElementById("import-file");
  const statusEl = document.getElementById("import-status");
  try {
    const text = await readFileAsText(fileInput);
    const response = await fetch("/import/shokumu", {
      method: "POST",
      headers: { "Content-Type": "text/plain; charset=utf-8" },
      body: text,
    });
    if (!response.ok) throw new Error(`読み込みに失敗しました (${response.status})`);
    const data = await response.json();
    applyFormData(data);
    scheduleSave();
    flashStatus(statusEl, "読み込みました");
  } catch (err) {
    flashStatus(statusEl, err.message, 5000);
  }
});

// cv.md の書き出し
document.getElementById("btn-export-md").addEventListener("click", async () => {
  const statusEl = document.getElementById("import-status");
  try {
    const response = await fetch("/export/shokumu", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectFormData()),
    });
    if (!response.ok) throw new Error(`書き出しに失敗しました (${response.status})`);
    const text = await response.text();
    downloadText(text, "cv.md", "text/markdown");
  } catch (err) {
    flashStatus(statusEl, err.message, 5000);
  }
});

// 入力クリア
document.getElementById("btn-clear").addEventListener("click", () => {
  if (!confirm("入力内容をすべてクリアしますか？")) return;
  form.reset();
  clearContainers();
  addTextListRow(educationList);
  addSkillGroup(skillGroups);
  addCompany(companies);
  localStorage.removeItem(DRAFT_KEY);
});

// 生成
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const statusEl = document.getElementById("generate-status");
  const payload = collectFormData();
  const body = new FormData();
  body.append("payload", JSON.stringify(payload));
  body.append("name", payload.name || "");

  flashStatus(statusEl, "生成中...", 0);
  try {
    const response = await fetch("/generate/shokumu-form", { method: "POST", body });
    await downloadResponse(response, "shokumu.docx");
    flashStatus(statusEl, "生成しました");
  } catch (err) {
    flashStatus(statusEl, err.message, 6000);
  }
});
