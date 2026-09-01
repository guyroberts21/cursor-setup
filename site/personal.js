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

function renderList(items, empty) {
  if (!items.length) return `<p class="muted">${empty}</p>`;
  return `<ul class="reflection-list">${items.map((i) => `<li>${i}</li>`).join("")}</ul>`;
}

function renderReflection(data) {
  const reflection = data.reflection;
  const latest = reflection.latest;

  document.getElementById("shutdown-ritual").innerHTML =
    reflection.shutdown_ritual_html || "<p>No ritual defined yet.</p>";

  if (!latest) {
    document.getElementById("reflection-latest").innerHTML =
      "<p>No reflection yet. Add an entry to <code>data/reflections.yaml</code>.</p>";
    document.getElementById("reflection-date").textContent = "";
    return;
  }

  document.getElementById("reflection-date").textContent = fmtDate(latest.date);

  const blocks = latest.tomorrow_blocks.length
    ? `<div class="reflection-block">
        <h4>Tomorrow's schedule</h4>
        <ul class="reflection-list">
          ${latest.tomorrow_blocks
            .map(
              (b) =>
                `<li><strong>${b.time_label}</strong>${b.project_name ? ` · ${b.project_name}` : ""}${b.note ? ` — ${b.note}` : ""}</li>`
            )
            .join("")}
        </ul>
      </div>`
    : "";

  document.getElementById("reflection-latest").innerHTML = `
    <div class="reflection-block">
      <h4>Done today</h4>
      ${renderList(latest.done_summary, "Nothing logged yet.")}
    </div>
    <div class="reflection-block">
      <h4>Tomorrow's focus</h4>
      ${renderList(latest.tomorrow_focus, "Nothing set yet.")}
    </div>
    ${blocks}
    ${
      latest.notes.length
        ? `<div class="reflection-block"><h4>Notes</h4>${renderList(latest.notes, "")}</div>`
        : ""
    }
  `;
}

function renderPersonal(data) {
  const personal = data.personal;
  document.getElementById("notes").innerHTML =
    personal.notes_html || "<p>No notes yet. Edit <code>data/notes.md</code>.</p>";

  const open = personal.open_todos;
  const total = personal.todos.length;
  document.getElementById("todo-count").textContent = `${open} open / ${total} total`;

  document.getElementById("todos").innerHTML = personal.todos.length
    ? personal.todos
        .map(
          (t) => `
        <li class="${t.done ? "done" : ""}${t.priority ? " priority" : ""}">
          <span class="todo-check">${t.done ? "✓" : t.priority ? "!" : "○"}</span>
          <span class="todo-text">${t.priority ? `<strong>${t.text}</strong>` : t.text}</span>
        </li>`
        )
        .join("")
    : "<li>No todos yet. Edit <code>data/todos.md</code>.</li>";

  const meta = document.getElementById("personal-meta");
  if (personal.updated_at) {
    meta.textContent = `Updated ${new Date(personal.updated_at).toLocaleString("en-GB")}`;
  }

  document.getElementById("sync-meta").textContent =
    `Generated ${new Date(data.generated_at).toLocaleString("en-GB")} · Edit markdown locally, push to update the site`;
}

async function main() {
  try {
    const data = await loadData();
    renderReflection(data);
    renderPersonal(data);
  } catch (err) {
    document.body.innerHTML = `<p style="padding:2rem;color:#e07070">Error: ${err.message}</p>`;
  }
}

main();
