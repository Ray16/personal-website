// Navigation toggle
document.getElementById('nav-toggle').addEventListener('click', function () {
    var navLinks = document.getElementById('nav-links');
    var expanded = this.getAttribute('aria-expanded') === 'true';
    this.setAttribute('aria-expanded', String(!expanded));
    navLinks.classList.toggle('active');
});

// Dark mode toggle
(function () {
    var toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    var saved = localStorage.getItem('theme');
    var theme = saved || 'light';

    function applyTheme(t) {
        document.documentElement.setAttribute('data-theme', t);
        toggle.textContent = t === 'dark' ? '\u2600\uFE0F' : '\uD83C\uDF19';
        toggle.setAttribute('aria-label', t === 'dark' ? 'Switch to light mode' : 'Switch to dark mode');
        localStorage.setItem('theme', t);
    }

    applyTheme(theme);

    toggle.addEventListener('click', function () {
        var current = document.documentElement.getAttribute('data-theme');
        applyTheme(current === 'dark' ? 'light' : 'dark');
    });
})();

// News year filter
(function () {
    var filterContainer = document.querySelector('.news-filter');
    if (!filterContainer) return;

    var buttons = filterContainer.querySelectorAll('.news-filter-btn');
    var yearGroups = document.querySelectorAll('.news-year-group');

    buttons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            var year = this.getAttribute('data-year');

            buttons.forEach(function (b) { b.classList.remove('active'); });
            this.classList.add('active');

            yearGroups.forEach(function (group) {
                if (year === 'all' || group.getAttribute('data-year') === year) {
                    group.classList.remove('hidden');
                } else {
                    group.classList.add('hidden');
                }
            });
        });
    });
})();
