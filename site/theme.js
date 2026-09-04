(() => {
  const STORAGE_KEY = "dashboard-theme";
  const ORDER = ["system", "light", "dark"];
  const LABELS = {
    system: "System",
    light: "Light",
    dark: "Dark",
  };
  const ICONS = {
    system: "◐",
    light: "☀",
    dark: "☾",
  };

  function getPreference() {
    const stored = localStorage.getItem(STORAGE_KEY);
    return ORDER.includes(stored) ? stored : "system";
  }

  function resolveTheme(preference) {
    if (preference === "light" || preference === "dark") return preference;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(preference = getPreference()) {
    const resolved = resolveTheme(preference);
    document.documentElement.setAttribute("data-theme", resolved);
    document.documentElement.setAttribute("data-theme-pref", preference);
    localStorage.setItem(STORAGE_KEY, preference);

    const button = document.getElementById("theme-toggle");
    if (!button) return;
    button.setAttribute("aria-label", `Theme: ${LABELS[preference]}. Click to change.`);
    button.title = `Theme: ${LABELS[preference]} (follows system when set to System)`;
    button.innerHTML =
      `<span class="theme-toggle-icon" aria-hidden="true">${ICONS[preference]}</span>` +
      `<span>${LABELS[preference]}</span>`;
  }

  function cycleTheme() {
    const current = getPreference();
    const next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];
    applyTheme(next);
  }

  window.__dashboardTheme = { applyTheme, getPreference, cycleTheme };

  applyTheme();

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      if (getPreference() === "system") applyTheme("system");
    });

  document.addEventListener("DOMContentLoaded", () => {
    applyTheme();
    const button = document.getElementById("theme-toggle");
    if (button) button.addEventListener("click", cycleTheme);
  });
})();
