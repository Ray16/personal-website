// Set the theme before paint. Storage may be unavailable in private browsers.
(function () {
    var theme;
    try { theme = localStorage.getItem('theme'); } catch (_) {}
    if (theme !== 'light' && theme !== 'dark') {
        theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    document.documentElement.setAttribute('data-theme', theme);
})();
