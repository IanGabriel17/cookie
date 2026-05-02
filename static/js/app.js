const themeToggle = document.getElementById("themeToggle");

function syncThemeToggle() {
    if (!themeToggle) {
        return;
    }
    const isDark = document.documentElement.dataset.theme === "dark";
    themeToggle.innerHTML = isDark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
    themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
    themeToggle.setAttribute("title", isDark ? "Switch to light mode" : "Switch to dark mode");
}

if (themeToggle) {
    syncThemeToggle();
    themeToggle.addEventListener("click", () => {
        const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
        document.documentElement.dataset.theme = nextTheme;
        localStorage.setItem("bakery-theme", nextTheme);
        syncThemeToggle();
    });
}

document.querySelectorAll("[data-submit-on-change]").forEach((element) => {
    element.addEventListener("change", () => element.closest("form")?.submit());
});
