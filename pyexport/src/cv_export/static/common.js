// yaml_cv フォーム共通ヘルパー。
// - localStorage への自動下書き保存/復元
// - fetch でファイル生成 -> ダウンロード
// - 動的な繰り返し行の追加/削除補助
"use strict";

/** localStorage に data を JSON として保存する。 */
function saveDraft(storageKey, data) {
  try {
    localStorage.setItem(storageKey, JSON.stringify(data));
  } catch (err) {
    console.warn("下書きの保存に失敗しました", err);
  }
}

/** localStorage から下書きを読み込む。無ければ null を返す。 */
function loadDraft(storageKey) {
  try {
    const raw = localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : null;
  } catch (err) {
    console.warn("下書きの読み込みに失敗しました", err);
    return null;
  }
}

/** ステータス表示欄に一時的にメッセージを出す。 */
function flashStatus(el, message, timeoutMs = 3000) {
  el.textContent = message;
  if (timeoutMs > 0) {
    setTimeout(() => {
      if (el.textContent === message) el.textContent = "";
    }, timeoutMs);
  }
}

/** レスポンスの Content-Disposition からファイル名を取り出し、ダウンロードさせる。 */
async function downloadResponse(response, fallbackName) {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || detail;
    } catch (_err) {
      // JSON でなければ無視
    }
    throw new Error(`生成に失敗しました (${response.status}): ${detail}`);
  }
  const disposition = response.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="?([^"]+)"?/);
  const filename = match ? match[1] : fallbackName;
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** テキストを .yaml / .md ファイルとしてブラウザにダウンロードさせる。 */
function downloadText(text, filename, mime = "text/plain") {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

/** input[type=file] からテキストを読み出す Promise。 */
function readFileAsText(fileInput) {
  return new Promise((resolve, reject) => {
    const file = fileInput.files && fileInput.files[0];
    if (!file) {
      reject(new Error("ファイルが選択されていません"));
      return;
    }
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file, "utf-8");
  });
}
