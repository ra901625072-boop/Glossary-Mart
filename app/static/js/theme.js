/**
 * Jay Goga Unified Theme Management
 * Handles dark/light mode synchronization across the entire application.
 */

(function() {
    const root = document.documentElement;
    const themeStorageKey = 'ss-theme';
    const systemLightMedia = window.matchMedia('(prefers-color-scheme: light)');

    /**
     * Applies the theme to the document and saves it to local storage.
     * @param {boolean} isLight - True for light mode, false for dark mode.
     */
    function applyTheme(isLight) {
        if (isLight) {
            root.setAttribute('data-theme', 'light');
        } else {
            root.removeAttribute('data-theme');
        }
        
        // Update all theme icons in the document
        const themeIcons = document.querySelectorAll('#themeIcon');
        themeIcons.forEach(icon => {
            if (isLight) {
                icon.classList.remove('bi-moon-stars');
                icon.classList.add('bi-sun-fill', 'text-warning');
            } else {
                icon.classList.remove('bi-sun-fill', 'text-warning');
                icon.classList.add('bi-moon-stars');
            }
        });
    }

    /**
     * Toggles the current theme.
     */
    function toggleTheme() {
        const currentIsLight = root.getAttribute('data-theme') === 'light';
        const newIsLight = !currentIsLight;
        localStorage.setItem(themeStorageKey, newIsLight ? 'light' : 'dark');
        applyTheme(newIsLight);
    }

    // Initialize Theme on Load
    const savedTheme = localStorage.getItem(themeStorageKey);
    const initialIsLight = savedTheme === 'light' || (!savedTheme && systemLightMedia.matches);
    applyTheme(initialIsLight);

    // Listen for System Theme Changes
    systemLightMedia.addEventListener('change', (e) => {
        if (!localStorage.getItem(themeStorageKey)) {
            applyTheme(e.matches);
        }
    });

    // Expose Toggle Function to Global Scope
    window.ssToggleTheme = toggleTheme;

    // Attach Event Listeners to Theme Toggle Buttons
    document.addEventListener('DOMContentLoaded', () => {
        const themeToggles = document.querySelectorAll('#themeToggle');
        themeToggles.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                toggleTheme();
            });
        });
    });
})();
