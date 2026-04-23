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

// Strip redundant " - " separator after <time> pills in news
(function () {
    document.querySelectorAll('.news-section p > time').forEach(function (t) {
        var next = t.nextSibling;
        if (next && next.nodeType === 3) {
            next.textContent = next.textContent.replace(/^\s*[-–]\s*/, ' ');
        }
    });
})();

// Scroll-to-top button
(function () {
    var btn = document.createElement('button');
    btn.className = 'scroll-top';
    btn.setAttribute('aria-label', 'Scroll to top');
    btn.type = 'button';
    btn.innerHTML = '↑';
    document.body.appendChild(btn);

    var threshold = 400;
    var ticking = false;

    function update() {
        if (window.scrollY > threshold) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
        ticking = false;
    }

    window.addEventListener('scroll', function () {
        if (!ticking) {
            window.requestAnimationFrame(update);
            ticking = true;
        }
    }, { passive: true });

    btn.addEventListener('click', function () {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
