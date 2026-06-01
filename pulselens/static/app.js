const levelClass = (level) => {
  const high = ["L3", "L4", "L5"];
  const elevated = ["L2"];
  if (high.includes(level)) return "high";
  if (elevated.includes(level)) return "elevated";
  return "low";
};

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
        <span class="badge ${entity.max_risk >= 61 ? "high" : entity.max_risk >= 41 ? "elevated" : "low"}">${Math.round(entity.max_risk)}</span>
      </header>
      <p>${escapeHtml(entity.description || aliases)}</p>
      <div class="meta">
        <span>${entity.mentions} mentions</span>
        <span>avg risk ${Number(entity.avg_risk).toFixed(1)}</span>
        <span>max ${Math.round(entity.max_risk)}</span>
      </div>
    </article>
  `;
}

function renderMention(mention) {
  const score = Number(mention.risk_score || 0);
  return `
    <article class="mention">
      <header>
        <h3>${escapeHtml(mention.entity_name)} / ${escapeHtml(mention.source)}</h3>
        <span class="badge ${levelClass(mention.risk_level)}">${escapeHtml(mention.risk_level)} ${score}</span>
      </header>
      <p class="mention-text">${escapeHtml(mention.text)}</p>
      <div class="meta">
        <span>sentiment ${Number(mention.sentiment).toFixed(2)}</span>
        <span>${escapeHtml(mention.risk_type)}</span>
        <span>reach ${mention.reach}</span>
        <span class="strategy">${escapeHtml(mention.strategy)}</span>
      </div>
      <p>${escapeHtml(mention.ai_summary || "")}</p>
      <p>${escapeHtml(mention.rationale)}</p>
    </article>
  `;
}

function renderRiskMix(levels) {
  if (!levels || levels.length === 0) {
    return `<span class="risk-pill">No mentions yet</span>`;
  }
  const order = ["L5", "L4", "L3", "L2", "L1", "L0"];
  const sorted = [...levels].sort((a, b) => order.indexOf(a.risk_level) - order.indexOf(b.risk_level));
  return sorted
    .map((item) => `<span class="risk-pill">${escapeHtml(item.risk_level)} ${item.count}</span>`)
    .join("");
}

async function refresh() {
  const [summary, entities] = await Promise.all([
    getJson("/api/summary"),
    getJson("/api/entities"),
  ]);

  document.querySelector("#totalMentions").textContent = summary.total_mentions;
  document.querySelector("#highAlerts").textContent = summary.high_alerts;
  document.querySelector("#averageRisk").textContent = summary.average_risk;
  document.querySelector("#riskMix").innerHTML = renderRiskMix(summary.levels);
  document.querySelector("#entities").innerHTML = entities.entities.length
    ? entities.entities.map(renderEntity).join("")
    : `<p class="empty">No watched entities yet. Seed data or import a CSV to start monitoring.</p>`;

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
  document.querySelector("#mentions").innerHTML = data.mentions.length
    ? data.mentions.map(renderMention).join("")
    : `<p class="empty">No priority mentions match this view.</p>`;
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
