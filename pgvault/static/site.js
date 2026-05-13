const healthChip = document.querySelector("#health-chip");
const healthOutput = document.querySelector("#health-output");
const rotatingTerm = document.querySelector("#rotating-term");
const metricValues = document.querySelectorAll("[data-count]");
const ruleItems = document.querySelectorAll(".rule-item");
const salesForm = document.querySelector("#sales-form");
const salesMessage = document.querySelector("#sales-message");
const leadTitle = document.querySelector("#lead-title");
const leadScope = document.querySelector("#lead-scope");
const leadPriority = document.querySelector("#lead-priority");
const leadState = document.querySelector("#lead-state");
const revealNodes = document.querySelectorAll(".reveal-on-scroll");

const terms = ["evidencia tecnica", "cumplimiento claro", "hallazgos accionables", "operacion segura"];
let termIndex = 0;

function rotateTerm() {
  if (!rotatingTerm) return;
  rotatingTerm.classList.add("term-out");
  window.setTimeout(() => {
    termIndex = (termIndex + 1) % terms.length;
    rotatingTerm.textContent = terms[termIndex];
    rotatingTerm.classList.remove("term-out");
  }, 220);
}

function animateMetrics() {
  metricValues.forEach((node) => {
    const target = Number(node.dataset.count || 0);
    if (!node.dataset.count) return;
    let current = 0;
    const increment = target === 0 ? 0 : Math.max(1, Math.ceil(target / 34));
    const timer = window.setInterval(() => {
      current = Math.min(target, current + increment);
      node.textContent = target === 24 ? "24/7" : `${current}${target <= 1 ? "" : "+"}`;
      if (current >= target) window.clearInterval(timer);
    }, 28);
  });
}

async function checkHealth() {
  if (!healthChip || !healthOutput) return;
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    healthChip.classList.add("is-online");
    healthChip.querySelector("span:last-child").textContent = "servicio activo";
    healthOutput.textContent = JSON.stringify(data, null, 2);
  } catch {
    healthChip.classList.add("is-offline");
    healthChip.querySelector("span:last-child").textContent = "servicio no disponible";
    healthOutput.textContent = '{ "status": "offline" }';
  }
}

function updateLeadPreview() {
  if (!salesForm || !leadTitle || !leadScope || !leadPriority) return;
  const data = new FormData(salesForm);
  const name = data.get("name")?.toString().trim();
  const company = data.get("company")?.toString().trim();
  leadTitle.textContent = company || name || "Nuevo contacto";
  leadScope.textContent = `${data.get("database_count") || "1-3"} bases`;
  leadPriority.textContent = data.get("priority") || "Evaluacion inicial";
}

ruleItems.forEach((item) => {
  item.addEventListener("click", () => {
    ruleItems.forEach((node) => node.classList.remove("active"));
    item.classList.add("active");
  });
});

if (salesForm && salesMessage) {
  salesForm.addEventListener("input", updateLeadPreview);
  salesForm.addEventListener("change", updateLeadPreview);
  salesForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!salesForm.reportValidity()) return;
    const data = Object.fromEntries(new FormData(salesForm));
    localStorage.setItem("pgvault.salesLead.v1", JSON.stringify({ ...data, created_at: new Date().toISOString() }));
    const name = data.name?.trim() || "tu equipo";
    salesMessage.textContent = `Solicitud registrada para ${name}. El equipo de ventas dara seguimiento con la informacion capturada.`;
    salesMessage.className = "message ok";
    if (leadState) leadState.textContent = "registrado localmente";
  });
}

window.setInterval(rotateTerm, 2600);
animateMetrics();
checkHealth();

if ("IntersectionObserver" in window) {
  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.14 },
  );
  revealNodes.forEach((node) => revealObserver.observe(node));
} else {
  revealNodes.forEach((node) => node.classList.add("is-visible"));
}
