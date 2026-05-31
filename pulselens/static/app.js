const levelClass = (level) => ["low", "guarded", "elevated", "high", "critical"].includes(level) ? level : "low";

async function getJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Request failed: ${url}`);
  return response.json();
}

function renderEntity(entity) {
  const aliases = entity.aliases || entity.name;
  return `
    <article class="entity">
      <header>
        <h3>${escapeHtml(entity.name)}</h3>
        <span class="badge ${entity.max_risk >= 60 ? "high" : entity.max_risk >= 40 ? "elevated" : "low"}">${Math.round(entity.max_risk)}</span>
      </header>
      <p>${escapeHtml(entity.description || aliases)}</p>
      <div class="meta">
        <span>${entity.mentions} mentions</span>
        <span>avg risk ${Number(entity.avg_risk).toFixed(1)}</span>
      </div>
    </article>
  `;
}

function renderMention(mention) {
  return `
    <article class="mention">
      <header>
        <h3>${escapeHtml(mention.entity_name)} · ${escapeHtml(mention.source)}</h3>
        <span class="badge ${levelClass(mention.risk_level)}">${escapeHtml(mention.risk_level)} ${mention.risk_score}</span>
      </header>
      <p class="mention-text">${escapeHtml(mention.text)}</p>
      <div class="meta">
        <span>sentiment ${Number(mention.sentiment).toFixed(2)}</span>
        <span>reach ${mention.reach}</span>
        <span class="strategy">${escapeHtml(mention.strategy)}</span>
      </div>
      <p>${escapeHtml(mention.rationale)}</p>
    </article>
  `;
}

async function refresh() {
  const [summary, entities] = await Promise.all([
    getJson("/api/summary"),
    getJson("/api/entities"),
  ]);

  document.querySelector("#totalMentions").textContent = summary.total_mentions;
  document.querySelector("#highAlerts").textContent = summary.high_alerts;
  document.querySelector("#averageRisk").textContent = summary.average_risk;
  document.querySelector("#entities").innerHTML = entities.entities.map(renderEntity).join("");

  const filter = document.querySelector("#entityFilter");
  const current = filter.value;
  filter.innerHTML = `<option value="">All entities</option>` + entities.entities
    .map((entity) => `<option value="${entity.id}">${escapeHtml(entity.name)}</option>`)
    .join("");
  filter.value = current;
  await refreshMentions();
}

async function refreshMentions() {
  const filter = document.querySelector("#entityFilter");
  const suffix = filter.value ? `?entity_id=${filter.value}&limit=100` : "?limit=100";
  const data = await getJson(`/api/mentions${suffix}`);
  document.querySelector("#mentions").innerHTML = data.mentions.map(renderMention).join("");
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[char]);
}

document.querySelector("#entityFilter").addEventListener("change", refreshMentions);
refresh();
