
const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");

const savedTheme = localStorage.getItem("trackbus-theme");
const initialTheme = savedTheme || "dark";

function applyTheme(theme) {
  root.setAttribute("data-theme", theme);

  if (themeToggle) {
    themeToggle.textContent =
      theme === "dark" ? "☀ Light" : "☾ Dark";
  }
}

applyTheme(initialTheme);

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const currentTheme = root.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";

    applyTheme(newTheme);
    localStorage.setItem("trackbus-theme", newTheme);
  });
}
