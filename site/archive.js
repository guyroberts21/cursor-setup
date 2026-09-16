async function loadData() {
  const res = await fetch("data.json");
  if (!res.ok) throw new Error(`Failed to load data.json (${res.status})`);
  return res.json();
}

function fmtDate(iso) {
  return new Date(iso + "T12:00:00").toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function renderTodos(todos, listId, countId) {
  const open = todos.filter((t) => !t.done).length;
  document.getElementById(countId).textContent = `${open} open / ${todos.length} total`;
  document.getElementById(listId).innerHTML = todos.length
    ? todos
        .map(
          (t) => `
        <li class="${t.done ? "done" : ""}${t.priority ? " priority" : ""}">
          <span class="todo-check">${t.done ? "✓" : t.priority ? "!" : "○"}</span>
          <span class="todo-text">${t.priority ? `<strong>${t.text}</strong>` : t.text}</span>
        </li>`
        )
        .join("")
    : "<li>No archived todos.</li>";
}

function renderWeeks(weeks) {
  const el = document.getElementById("weeks");
  const previous = weeks.filter((w) => !w.is_current);
  const current = weeks.find((w) => w.is_current);

  if (!weeks.length) {
    el.innerHTML = "<p class=\"muted\">No week files in <code>data/weeks/</code> yet.</p>";
    return;
  }

  const currentNote = current
    ? `<p class="muted archive-current-note"><strong>${current.id}</strong> is this week — ${current.total_logged}h / ${current.total_target}h on the <a href="index.html">dashboard</a>.</p>`
    : "";

  if (!previous.length) {
    el.innerHTML = `${currentNote}<p class="muted">No previous week files yet.</p>`;
    return;
  }

  el.innerHTML =
    currentNote +
    previous
      .map((w) => {
        const extra = w.extra_logged ? ` · ${w.extra_logged}h extra` : "";
        const projects = (w.projects || [])
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
        return `
          <article class="archive-week">
            <div class="card-head">
              <h3>${w.id}</h3>
              <span class="badge">${w.total_logged}h / ${w.total_target}h</span>
            </div>
            <p class="muted">${fmtDate(w.start)} – ${fmtDate(w.end)}${extra}</p>
            ${projects}
          </article>`;
      })
      .join("");
}

function renderArchive(data) {
  const archive = data.archive || {};
  renderWeeks(archive.weeks || []);

  document.getElementById("archive-notes").innerHTML =
    archive.notes_html || "<p>No archived notes yet. Edit <code>data/archive/notes-archive.md</code>.</p>";

  renderTodos(archive.todos || [], "archive-todos", "archive-todo-count");

  const meta = document.getElementById("archive-meta");
  const previousCount = (archive.weeks || []).filter((w) => !w.is_current).length;
  meta.innerHTML = `
    <div>${previousCount} previous week${previousCount === 1 ? "" : "s"}</div>
    <div class="muted">This week: ${data.week?.id || "—"}</div>
  `;

  document.getElementById("sync-meta").textContent =
    `Generated ${new Date(data.generated_at).toLocaleString("en-GB")} · Edit archive markdown locally, push to update the site`;
}

async function main() {
  try {
    const data = await loadData();
    renderArchive(data);
  } catch (err) {
    document.body.innerHTML = `<p style="padding:2rem;color:#e07070">Error: ${err.message}</p>`;
  }
}

main();
