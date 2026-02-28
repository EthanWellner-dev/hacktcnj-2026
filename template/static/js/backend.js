// backend.js contains reusable functions for communicating with the Flask backend.
// Designed to be imported before any module-specific script so that the
// helpers are available globally.

// fetch current user information and update the XP display
async function fetchMe() {
    const token = localStorage.getItem('ss_token');
    if (!token) {
        window.location.href = '/';
        return null;
    }
    try {
        const resp = await fetch('/api/users/me', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!resp.ok) throw new Error('not authorized');
        const data = await resp.json();
        document.getElementById('user-xp').textContent = data.xp || 0;
        return data;
    } catch (err) {
        console.error(err);
        localStorage.removeItem('ss_token');
        window.location.href = '/';
    }
}

// convenience helper to increment xp and refresh header
async function awardXP(amount) {
    const token = localStorage.getItem('ss_token');
    if (!token) return;
    try {
        const resp = await fetch('/api/module6/complete', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ xp: amount })
        });
        if (!resp.ok) throw new Error('xp update failed');
        const data = await resp.json();
        document.getElementById('user-xp').textContent = data.xp || 0;
        return data;
    } catch (e) {
        console.error(e);
    }
}

// generic training submission helper used by every exercise script
async function submitTrainingResults(moduleName, metrics) {
    const token = localStorage.getItem('ss_token');
    if (!token) return;
    try {
        const resp = await fetch('/api/training/submit', {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                module: moduleName,
                results: metrics
            })
        });
        if (!resp.ok) throw new Error('training submit failed');
        const data = await resp.json();
        // backend may include updated xp
        if (data.xp !== undefined) {
            document.getElementById('user-xp').textContent = data.xp;
        }
        return data;
    } catch (e) {
        console.error(e);
    }
}

// export helpers to a global namespace so exercises can simply call them
window.backend = {
    fetchMe,
    awardXP,
    submitTrainingResults
};
