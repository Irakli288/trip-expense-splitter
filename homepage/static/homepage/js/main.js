// Текущий год в подвале сайта. В HTML его нет, скрипт подставляет его сам.
const yearElement = document.getElementById("current-year");
if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}
