async function loadData() {
  const res = await fetch("data.json");
  if (!res.ok) throw new Error(`Failed to load data.json (${res.status})`);
  return res.json();
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
        <li class="${t.done ? "done" : ""}">
          <span class="todo-check">${t.done ? "✓" : "○"}</span>
          <span class="todo-text">${t.text}</span>
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
    renderPersonal(data);
  } catch (err) {
    document.body.innerHTML = `<p style="padding:2rem;color:#e07070">Error: ${err.message}</p>`;
  }
}

main();
