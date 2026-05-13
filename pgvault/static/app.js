const form = document.querySelector("#connection-form");
const profileList = document.querySelector("#profile-list");
const newProfileBtn = document.querySelector("#new-profile-btn");
const saveBtn = document.querySelector("#save-btn");
const validateBtn = document.querySelector("#validate-btn");
const scanBtn = document.querySelector("#scan-btn");
const message = document.querySelector("#message");
const appStatus = document.querySelector("#app-status");
const connectionScreen = document.querySelector("#connection-screen");
const resultsScreen = document.querySelector("#results-screen");
const findingList = document.querySelector("#finding-list");
const detailPanel = document.querySelector("#detail-panel");
const summary = document.querySelector("#summary");
const historyList = document.querySelector("#history-list");
const resultTitle = document.querySelector("#result-title");
const newScanBtn = document.querySelector("#new-scan-btn");

const DEMO_PROFILES = [
  {
    alias: "fintechdb-demo",
    host: "fintechdb",
    port: 5432,
    database: "fintechdb",
    user: "fintech_user",
    password: "fintech_pass",
    sslmode: "disable",
    sample_limit: 100,
    query_timeout: 10,
  },
  {
    alias: "tiendadb-demo",
    host: "tiendadb",
    port: 5432,
    database: "tiendadb",
    user: "tienda_user",
    password: "tienda_pass",
    sslmode: "disable",
    sample_limit: 100,
    query_timeout: 10,
  },
  {
    alias: "appdb-demo",
    host: "appdb",
    port: 5432,
    database: "appdb",
    user: "app_user",
    password: "app_pass",
    sslmode: "disable",
    sample_limit: 100,
    query_timeout: 10,
  },
];

const PROFILE_STORAGE_KEY = "pgvault.localProfiles.v1";
const HISTORY_STORAGE_KEY = "pgvault.localScanHistory.v1";

let profiles = [];
let currentPayload = null;
let currentResult = null;
let lastValidatedKey = null;
let activeProfileKey = "";

const EMPTY_PROFILE = {
  alias: "",
  host: "",
  port: 5432,
  database: "",
  user: "",
  password: "",
  sslmode: "disable",
  sample_limit: 100,
  query_timeout: 10,
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function payloadFromForm() {
  const data = new FormData(form);
  return {
    alias: data.get("alias").trim(),
    host: data.get("host").trim(),
    port: Number(data.get("port")),
    database: data.get("database").trim(),
    user: data.get("user").trim(),
    password: data.get("password") || null,
    sslmode: data.get("sslmode"),
    sample_limit: Number(data.get("sample_limit")),
    query_timeout: Number(data.get("query_timeout")),
  };
}

function validationKey(payload) {
  const { password, ...safePayload } = payload;
  return JSON.stringify(safePayload);
}

function setMessage(text, kind = "") {
  message.textContent = text;
  message.className = `message ${kind}`;
}

function isSavedProfile(alias) {
  return profiles.some((profile) => profile.alias === alias);
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "La solicitud no pudo completarse.");
  }
  return data;
}

function readLocalJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function writeLocalJson(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

async function loadProfiles() {
  profiles = readLocalJson(PROFILE_STORAGE_KEY, []);
  renderProfileSidebar();
}

function profileKey(profile) {
  return profile.demo ? `demo:${profile.alias}` : profile.alias;
}

function renderProfileSidebar() {
  const demoProfiles = DEMO_PROFILES.map((profile) => ({ ...profile, demo: true }));
  const savedProfiles = profiles.map((profile) => ({ ...profile, demo: false }));
  const allProfiles = [...demoProfiles, ...savedProfiles];
  profileList.innerHTML = "";

  if (!allProfiles.length) {
    profileList.innerHTML = '<p class="muted profile-empty">Sin perfiles guardados.</p>';
    return;
  }

  for (const profile of allProfiles) {
    const item = document.createElement("div");
    item.className = `profile-item ${profileKey(profile) === activeProfileKey ? "active" : ""}`;
    item.innerHTML = `
      <button type="button" class="profile-main">
        <span class="profile-alias">${escapeHtml(profile.alias)}</span>
        <span class="profile-meta">${escapeHtml(profile.user)}@${escapeHtml(profile.host)} / ${escapeHtml(profile.database)}</span>
        <span class="profile-kind">${profile.demo ? "demo" : "local"}</span>
      </button>
      <div class="profile-actions">
        <button type="button" class="profile-menu-btn" title="Opciones">...</button>
        <div class="profile-menu hidden">
          <button type="button" data-action="edit">Modificar</button>
          ${profile.demo ? "" : '<button type="button" data-action="delete" class="danger-text">Eliminar</button>'}
        </div>
      </div>
    `;

    item.querySelector(".profile-main").addEventListener("click", () => selectProfile(profile));
    item.querySelector('[data-action="edit"]').addEventListener("click", () => selectProfile(profile));
    const deleteAction = item.querySelector('[data-action="delete"]');
    if (deleteAction) {
      deleteAction.addEventListener("click", () => deleteProfile(profile.alias));
    }
    const menuButton = item.querySelector(".profile-menu-btn");
    const menu = item.querySelector(".profile-menu");
    menuButton.addEventListener("click", (event) => {
      event.stopPropagation();
      document.querySelectorAll(".profile-menu").forEach((node) => {
        if (node !== menu) node.classList.add("hidden");
      });
      menu.classList.toggle("hidden");
    });
    profileList.append(item);
  }
}

function fillProfile(profile) {
  for (const [name, value] of Object.entries({
    alias: profile.alias,
    host: profile.host,
    port: profile.port,
    database: profile.database,
    user: profile.user,
    sslmode: profile.sslmode,
    sample_limit: profile.sample_limit,
    query_timeout: profile.query_timeout,
  })) {
    const field = form.elements[name];
    if (field) field.value = value;
  }
  form.elements.password.value = profile.password || "";
  scanBtn.disabled = true;
  lastValidatedKey = null;
  appStatus.textContent = "perfil cargado";
  setMessage("", "");
}

function selectProfile(profile) {
  activeProfileKey = profileKey(profile);
  fillProfile(profile);
  renderProfileSidebar();
}

function newProfile() {
  activeProfileKey = "";
  fillProfile(EMPTY_PROFILE);
  appStatus.textContent = "nuevo perfil";
  renderProfileSidebar();
}

function deleteProfile(alias) {
  if (!alias || !isSavedProfile(alias)) {
    setMessage("Solo se pueden eliminar perfiles guardados manualmente.", "error");
    return;
  }
  if (!window.confirm(`Eliminar el perfil guardado "${alias}"?`)) return;
  writeLocalJson(
    PROFILE_STORAGE_KEY,
    profiles.filter((profile) => profile.alias !== alias),
  );
  loadProfiles();
  newProfile();
  setMessage("Perfil eliminado.", "ok");
  appStatus.textContent = "perfil eliminado";
}

function locationLabel(finding) {
  const parts = [finding.table_schema, finding.table_name, finding.column_name].filter(Boolean);
  return parts.length ? parts.join(".") : "base de datos";
}

function allItems(result) {
  const findings = (result.findings || []).map((finding) => ({ type: "finding", ...finding }));
  const errors = (result.errors || []).map((error, index) => ({
    type: "error",
    id: `error-${index}`,
    title: error.module,
    category: "error",
    severity: "HIGH",
    evidence: error.detail || error.message,
    description: error.message,
    recommendation: "Revisar el modulo indicado y volver a ejecutar la revision.",
  }));
  const warnings = (result.warnings || []).map((warning, index) => ({
    type: "warning",
    id: `warning-${index}`,
    title: warning.source,
    category: "warning",
    severity: "LOW",
    evidence: warning.detail || warning.message,
    description: warning.message,
    recommendation: "Verificar permisos de catalogo y disponibilidad de vistas de PostgreSQL.",
  }));
  return [...findings, ...errors, ...warnings];
}

function renderSummary(result) {
  summary.innerHTML = `
    <div class="metric"><span>Hallazgos</span><strong>${result.total_findings ?? result.findings.length}</strong></div>
    <div class="metric"><span>Warnings</span><strong>${result.total_warnings ?? result.warnings.length}</strong></div>
    <div class="metric"><span>Errores</span><strong>${result.total_errors ?? result.errors.length}</strong></div>
  `;
}

function renderFindings(result) {
  const items = allItems(result);
  findingList.innerHTML = "";
  if (!items.length) {
    findingList.innerHTML = '<p class="muted">No se encontraron hallazgos, warnings ni errores.</p>';
    renderDetail(null);
    return;
  }
  items.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "finding-item";
    button.innerHTML = `
      <div class="finding-meta">
        <span class="tag ${escapeHtml(item.severity)}">${escapeHtml(item.severity)}</span>
        <span class="tag">${escapeHtml(item.category)}</span>
        <span class="tag">${escapeHtml(locationLabel(item))}</span>
      </div>
      <strong>${escapeHtml(item.title)}</strong>
      <p class="muted">${escapeHtml(item.evidence || "Sin evidencia detallada.")}</p>
    `;
    button.addEventListener("click", () => {
      document.querySelectorAll(".finding-item").forEach((node) => node.classList.remove("active"));
      button.classList.add("active");
      renderDetail(item);
    });
    findingList.append(button);
    if (index === 0) button.click();
  });
}

function renderDetail(item) {
  if (!item) {
    detailPanel.innerHTML = '<p class="eyebrow">detalle técnico</p><h2>Sin hallazgos</h2><p class="muted">La revisión no reportó elementos que atender.</p>';
    return;
  }
  const refs = (item.regulation_refs || [])
    .map((ref) => `<li><strong>${escapeHtml(ref.framework)}</strong>${ref.article ? `, ${escapeHtml(ref.article)}` : ""}${ref.description ? `: ${escapeHtml(ref.description)}` : ""}</li>`)
    .join("");
  const docLinks = `
    <li><a href="https://www.postgresql.org/docs/current/ddl-priv.html" target="_blank" rel="noreferrer">PostgreSQL privileges</a></li>
    <li><a href="https://www.postgresql.org/docs/current/auth-pg-hba-conf.html" target="_blank" rel="noreferrer">PostgreSQL client authentication</a></li>
  `;
  detailPanel.innerHTML = `
    <article>
      <div>
        <p class="eyebrow">${escapeHtml(item.module || item.type)}</p>
        <h2>${escapeHtml(item.title)}</h2>
        <div class="finding-meta">
          <span class="tag ${escapeHtml(item.severity)}">${escapeHtml(item.severity)}</span>
          <span class="tag">${escapeHtml(item.category)}</span>
          <span class="tag">${escapeHtml(locationLabel(item))}</span>
        </div>
      </div>
      <section class="detail-section"><h3>Explicación técnica</h3><p>${escapeHtml(item.description || "Sin descripción.")}</p></section>
      <section class="detail-section"><h3>Evidencia</h3><pre>${escapeHtml(item.evidence || "Sin evidencia.")}</pre></section>
      <section class="detail-section"><h3>Recomendación</h3><p>${escapeHtml(item.recommendation || "Revisar el hallazgo y ajustar la configuración.")}</p></section>
      ${item.remediation_sql ? `<section class="detail-section"><h3>SQL sugerido</h3><pre>${escapeHtml(item.remediation_sql)}</pre></section>` : ""}
      <section class="detail-section"><h3>Referencias regulatorias</h3><ul>${refs || "<li>No especificadas por el módulo.</li>"}</ul></section>
      <section class="detail-section"><h3>Documentación pública</h3><ul>${docLinks}</ul></section>
    </article>
  `;
}

async function renderHistory(alias) {
  const scans = readLocalJson(HISTORY_STORAGE_KEY, []).filter((scan) => scan.alias === alias);
  historyList.innerHTML = "";
  if (!scans.length) {
    historyList.innerHTML = '<p class="muted">Este perfil aun no tiene revisiones guardadas.</p>';
    return;
  }
  for (const scan of scans.slice(0, 5)) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-item";
    button.innerHTML = `<strong>${escapeHtml(new Date(scan.created_at).toLocaleString())}</strong><p class="muted">${escapeHtml(scan.total_findings)} hallazgos, ${escapeHtml(scan.total_errors)} errores</p>`;
    button.addEventListener("click", () => {
      showResult(scan.result, scan.alias, false);
    });
    historyList.append(button);
  }
}

function saveLocalScan(alias, result) {
  const scans = readLocalJson(HISTORY_STORAGE_KEY, []);
  scans.unshift({
    id: crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}`,
    alias,
    database: result.database,
    scan_id: result.scan_id,
    created_at: new Date().toISOString(),
    total_findings: result.total_findings ?? result.findings?.length ?? 0,
    total_warnings: result.total_warnings ?? result.warnings?.length ?? 0,
    total_errors: result.total_errors ?? result.errors?.length ?? 0,
    result,
  });
  writeLocalJson(HISTORY_STORAGE_KEY, scans.slice(0, 50));
}

function showResult(result, alias, persistHistory = true) {
  currentResult = result;
  if (persistHistory && alias) {
    saveLocalScan(alias, result);
  }
  connectionScreen.classList.add("hidden");
  resultsScreen.classList.remove("hidden");
  resultTitle.textContent = `Hallazgos: ${alias || result.database}`;
  renderSummary(result);
  renderFindings(result);
  renderHistory(alias || currentPayload?.alias || "");
  appStatus.textContent = "revision completada";
}

newProfileBtn.addEventListener("click", newProfile);

document.addEventListener("click", (event) => {
  if (!event.target.closest(".profile-actions")) {
    document.querySelectorAll(".profile-menu").forEach((node) => node.classList.add("hidden"));
  }
});

form.addEventListener("input", () => {
  const nextPayload = payloadFromForm();
  if (validationKey(nextPayload) !== lastValidatedKey) {
    scanBtn.disabled = true;
    appStatus.textContent = "sin validar";
  }
});

saveBtn.addEventListener("click", async () => {
  if (!form.reportValidity()) return;
  const payload = payloadFromForm();
  setMessage("Guardando perfil local sin contraseña...", "");
  saveBtn.disabled = true;
  try {
    const localProfile = {
      alias: payload.alias,
      host: payload.host,
      port: payload.port,
      database: payload.database,
      user: payload.user,
      sslmode: payload.sslmode,
      sample_limit: payload.sample_limit,
      query_timeout: payload.query_timeout,
      password_saved: false,
      updated_at: new Date().toISOString(),
    };
    const nextProfiles = profiles.filter((profile) => profile.alias !== payload.alias);
    nextProfiles.unshift(localProfile);
    writeLocalJson(PROFILE_STORAGE_KEY, nextProfiles);
    await loadProfiles();
    activeProfileKey = payload.alias;
    renderProfileSidebar();
    setMessage("Perfil guardado en este navegador. La contraseña no se persistió.", "ok");
    appStatus.textContent = "perfil guardado";
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    saveBtn.disabled = false;
  }
});

validateBtn.addEventListener("click", async () => {
  if (!form.reportValidity()) return;
  currentPayload = payloadFromForm();
  scanBtn.disabled = true;
  lastValidatedKey = null;
  setMessage("Validando conexion...", "");
  validateBtn.disabled = true;
  try {
    const result = await requestJson("/api/validate", {
      method: "POST",
      body: JSON.stringify(currentPayload),
    });
    if (!result.ok) {
      setMessage(result.message, "error");
      appStatus.textContent = "conexion fallida";
      scanBtn.disabled = true;
      return;
    }
    setMessage(result.message, "ok");
    lastValidatedKey = validationKey(currentPayload);
    scanBtn.disabled = false;
    appStatus.textContent = "conexion validada";
  } catch (error) {
    setMessage(error.message, "error");
    appStatus.textContent = "conexion fallida";
  } finally {
    validateBtn.disabled = false;
  }
});

scanBtn.addEventListener("click", async () => {
  if (!form.reportValidity()) return;
  currentPayload = payloadFromForm();
  setMessage("Ejecutando revision...", "");
  scanBtn.disabled = true;
  appStatus.textContent = "revision en curso";
  try {
    const response = await requestJson("/api/scans", {
      method: "POST",
      body: JSON.stringify(currentPayload),
    });
    await loadProfiles();
    showResult(response.result, currentPayload.alias);
  } catch (error) {
    setMessage(error.message, "error");
    appStatus.textContent = "revision fallida";
  } finally {
    scanBtn.disabled = false;
  }
});

newScanBtn.addEventListener("click", () => {
  resultsScreen.classList.add("hidden");
  connectionScreen.classList.remove("hidden");
  appStatus.textContent = currentResult ? "revision completada" : "sin validar";
});

loadProfiles().catch((error) => setMessage(error.message, "error"));
