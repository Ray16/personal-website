(function () {
    'use strict';
    document.documentElement.classList.add('js');
    var menu = document.getElementById('nav-toggle');
    var links = document.getElementById('nav-links');
    function closeMenu(returnFocus) {
        if (!menu || !links) return;
        menu.setAttribute('aria-expanded', 'false');
        menu.setAttribute('aria-label', 'Open navigation');
        links.classList.remove('active');
        if (returnFocus) menu.focus();
    }
    if (menu && links) {
        menu.addEventListener('click', function () {
            var open = menu.getAttribute('aria-expanded') !== 'true';
            menu.setAttribute('aria-expanded', String(open));
            menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
            links.classList.toggle('active', open);
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') closeMenu(true);
        });
        document.addEventListener('click', function (e) {
            if (!e.target.closest('.site-nav')) closeMenu(false);
        });
        links.addEventListener('click', function (e) { if (e.target.closest('a')) closeMenu(false); });
        links.addEventListener('focusout', function (e) {
            if (!e.relatedTarget || !e.relatedTarget.closest('.site-nav')) closeMenu(false);
        });
        window.matchMedia('(max-width: 760px)').addEventListener('change', function () { closeMenu(false); });
    }
    var toggle = document.getElementById('theme-toggle');
    var systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
    function updateToggle() {
        if (!toggle) return;
        var dark = document.documentElement.getAttribute('data-theme') === 'dark';
        toggle.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
        toggle.setAttribute('aria-pressed', String(dark));
        toggle.innerHTML = '<span aria-hidden="true">' + (dark ? '☼' : '◐') + '</span>';
    }
    updateToggle();
    if (toggle) toggle.addEventListener('click', function () {
        var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try { localStorage.setItem('theme', next); } catch (_) {}
        updateToggle();
    });
    systemTheme.addEventListener('change', function (e) {
        var saved;
        try { saved = localStorage.getItem('theme'); } catch (_) {}
        if (!saved) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            updateToggle();
        }
    });
    var filters = document.querySelector('.news-filter');
    if (filters) {
        var groups = Array.from(document.querySelectorAll('.news-year-group'));
        var entries = groups.flatMap(function (group) { return Array.from(group.querySelectorAll('p')); });
        // Choose the newest six entries across all years, independently of source ordering.
        var recent = entries.slice().sort(function (a,b) {
            return (b.querySelector('time').dateTime || '').localeCompare(a.querySelector('time').dateTime || '');
        }).slice(0, 6);
        var status = document.createElement('p');
        status.className = 'news-status';
        status.setAttribute('role', 'status');
        status.setAttribute('aria-live', 'polite');
        filters.closest('.news-section').appendChild(status);
        function filterNews(year) {
            filters.querySelectorAll('button').forEach(function (button) {
                var active = button.dataset.year === year;
                button.classList.toggle('active', active);
                button.setAttribute('aria-pressed', String(active));
            });
            var count = 0;
            groups.forEach(function (group) {
                var visible = 0;
                group.querySelectorAll('p').forEach(function (entry) {
                    var show = year === 'recent' ? recent.includes(entry) : year === 'all' || group.dataset.year === year;
                    entry.hidden = !show;
                    if (show) visible++;
                });
                group.classList.toggle('hidden', visible === 0);
                count += visible;
            });
            status.textContent = year === 'recent' ? 'Showing the ' + count + ' latest updates. Choose a year to explore the archive.' : 'Showing ' + count + ' updates' + (year === 'all' ? ' across all years.' : ' from ' + year + '.');
        }
        filters.addEventListener('click', function (e) {
            var button = e.target.closest('button[data-year]');
            if (button) filterNews(button.dataset.year);
        });
        document.querySelectorAll('.news-section p > time').forEach(function (time) {
            var next = time.nextSibling;
            if (next && next.nodeType === 3) next.textContent = next.textContent.replace(/^\s*[-–]\s*/, ' ');
        });
        document.querySelectorAll('.news-year-group p').forEach(function (entry) {
            var time = entry.querySelector('time');
            if (!time) return;
            var description = document.createElement('span');
            description.className = 'news-description';
            while (time.nextSibling) description.appendChild(time.nextSibling);
            entry.appendChild(description);
        });
        filterNews('recent');
    }
    var top = document.createElement('button');
    top.className = 'scroll-top';
    top.type = 'button';
    top.setAttribute('aria-label', 'Back to top');
    top.innerHTML = '<span aria-hidden="true">↑</span>';
    top.tabIndex = -1;
    document.body.appendChild(top);
    var queued = false;
    function updateScroll() {
        var visible = window.scrollY > 500;
        top.classList.toggle('visible', visible);
        top.tabIndex = visible ? 0 : -1;
        queued = false;
    }
    window.addEventListener('scroll', function () {
        if (!queued) { queued = true; window.requestAnimationFrame(updateScroll); }
    }, { passive: true });
    updateScroll();
    top.addEventListener('click', function () {
        var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        window.scrollTo({ top: 0, behavior: reduce ? 'instant' : 'smooth' });
        var main = document.getElementById('main-content');
        main.setAttribute('tabindex', '-1');
        main.focus({ preventScroll: true });
    });
})();
