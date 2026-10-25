// Текущий год в подвале сайта: год не записан в HTML, его подставляет скрипт.
const yearElement = document.getElementById("current-year");
if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}
