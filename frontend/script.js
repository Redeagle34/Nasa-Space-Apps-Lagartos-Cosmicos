// Frontend-only JavaScript (backend calls removed)

// Provide a simple DOM-ready initializer. Keep an exported loadData stub
// in case other modules expect it.
function loadData() {
    // No backend: this area can be used to load local assets or initialize UI state.
    console.log('Frontend running in standalone mode.');
}

document.addEventListener('DOMContentLoaded', () => {
    loadData();
});

// Export for dev console convenience
window.app = { loadData };