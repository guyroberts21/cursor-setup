async function loadData() {
  const res = await fetch("data.json");
  if (!res.ok) throw new Error(`Failed to load data.json (${res.status})`);
  return res.json();
}

function fmtDate(iso) {
  return new Date(iso + "T12:00:00").toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
  });
}

function renderWeek(data) {
  const el = document.getElementById("week-meta");
  const { week } = data;
  el.innerHTML = `
    <div><strong>${week.id}</strong></div>
    <div>${fmtDate(week.start)} – ${fmtDate(week.end)}</div>
    <div>${week.work_days_remaining} work day${week.work_days_remaining === 1 ? "" : "s"} left</div>
  `;
}

function renderTotals(data) {
  const { hours } = data;
  const extra = hours.extra_logged
    ? `<div><div class="stat-value">${hours.extra_logged}h</div><div class="stat-label">Extra</div></div>`
    : "";
  document.getElementById("totals").innerHTML = `
    <div><div class="stat-value">${hours.total_logged}h</div><div class="stat-label">Logged</div></div>
    <div><div class="stat-value">${hours.total_remaining}h</div><div class="stat-label">Remaining</div></div>
    <div><div class="stat-value">${hours.total_target}h</div><div class="stat-label">Target</div></div>
    ${extra}
  `;
}

function renderProjects(data) {
  const container = document.getElementById("projects");
  container.innerHTML = data.hours.projects
    .map((p) => {
      const pct = p.target_hours ? Math.min(100, (p.logged_hours / p.target_hours) * 100) : 0;
      const over = p.logged_hours >= p.target_hours;
      return `
        <div class="project-row">
          <div class="project-head">
            <span>${p.name}</span>
            <span>${p.logged_hours}h / ${p.target_hours}h</span>
          </div>
          <div class="bar-track">
            <div class="bar-fill ${over ? "over" : ""}" style="width:${pct}%"></div>
          </div>
        </div>`;
    })
    .join("");
}

function priorityTag(labels) {
  if (labels.includes("P1")) return '<span class="tag p1">P1</span>';
  if (labels.includes("P2")) return '<span class="tag p2">P2</span>';
  return "";
}

function renderTicket(item) {
  const stale = item.days_since_update >= 3;
  return `
    <li>
      <a class="ticket-link" href="${item.url}" target="_blank" rel="noopener">
        MD-${item.number} — ${item.title}
      </a>
      <div class="ticket-meta">
        ${priorityTag(item.labels)}
        ${item.client ? `<span class="tag">${item.client}</span>` : ""}
        ${item.status ? `<span class="tag">${item.status}</span>` : ""}
        <span class="tag ${stale ? "stale" : ""}">${item.days_since_update ?? 0}d since update</span>
      </div>
    </li>`;
}

function renderPriorities(data) {
  document.getElementById("priority-count").textContent =
    `${data.priorities.length} priority`;
  document.getElementById("priorities").innerHTML =
    data.priorities.length
      ? data.priorities.map(renderTicket).join("")
      : "<li>No Action needed + P1/P2 tickets right now.</li>";

  const allBtn = document.getElementById("toggle-all");
  const allList = document.getElementById("all-assigned");
  if (data.all_assigned_count > data.priorities.length) {
    allBtn.hidden = false;
    allList.innerHTML = data.all_assigned
      .map((i) => renderTicket({ ...i, days_since_update: i.days_since_update ?? 0 }))
      .join("");
    allBtn.addEventListener("click", () => {
      const hidden = allList.hidden;
      allList.hidden = !hidden;
      allBtn.textContent = hidden ? "Hide all assigned" : "Show all assigned";
    });
  }
}

function renderLog(data) {
  const el = document.getElementById("recent-log");
  if (!data.recent_log.length) {
    el.innerHTML = "<li>No hours logged yet this week.</li>";
    return;
  }
  el.innerHTML = data.recent_log
    .map((e) => {
      const extra = e.extra ? ' <span class="tag">extra</span>' : "";
      return `
      <li>
        <span>${e.project_name}: ${e.hours}h${e.note ? ` — ${e.note}` : ""}${extra}</span>
        <span class="log-date">${fmtDate(e.date)}</span>
      </li>`;
    })
    .join("");
}

function renderFooter(data) {
  const parts = [`Generated ${new Date(data.generated_at).toLocaleString("en-GB")}`];
  if (data.github_synced_at) {
    parts.push(`GitHub synced ${new Date(data.github_synced_at).toLocaleString("en-GB")}`);
  }
  document.getElementById("sync-meta").textContent = parts.join(" · ");
}

async function main() {
  try {
    const data = await loadData();
    renderWeek(data);
    renderTotals(data);
    renderProjects(data);
    renderPriorities(data);
    renderLog(data);
    renderFooter(data);
  } catch (err) {
    document.body.innerHTML = `<p style="padding:2rem;color:#e07070">Error: ${err.message}</p>`;
  }
}

main();
