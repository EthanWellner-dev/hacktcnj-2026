// dashboard.js handles fetching user info, leaderboard, xp meter, and gym buttons

async function fetchMe() {
    const token = localStorage.getItem('ss_token');
    if (!token) return window.location.href = '/';
    try {
        const resp = await fetch('/api/users/me', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (!resp.ok) throw new Error('not authorized');
        const data = await resp.json();
        showXP(data.xp || 0);
        return data;
    } catch (err) {
        console.error(err);
        localStorage.removeItem('ss_token');
        return window.location.href = '/';
    }
}

async function loadLeaderboard() {
    try {
        const resp = await fetch('/api/users/leaderboard');
        const list = await resp.json();
        const ul = document.getElementById('leaderboard-list');
        ul.innerHTML = '';
        list.forEach((entry) => {
            const li = document.createElement('li');
            li.textContent = `${entry.name} — ${entry.xp} XP`;
            li.className = 'border-b pb-1';
            ul.appendChild(li);
        });
    } catch (err) {
        console.error('Leaderboard load failed', err);
    }
}

function showXP(xp) {
    const fill = document.getElementById('xp-fill');
    const value = document.getElementById('xp-value');
    const percent = Math.min(100, Math.max(0, xp));
    if (fill) fill.style.width = percent + '%';
    if (value) value.textContent = `${xp} XP`;
}

function setupButtons() {
    document.getElementById('btn-digital').addEventListener('click', () => {
        document.getElementById('gym-area').innerHTML = `<h4 class="text-slate-100 font-medium">Gym 1: Digital Comm Suite</h4><p class="text-slate-400">Open chat-module.html (not yet implemented)</p>`;
    });
    document.getElementById('btn-vocal').addEventListener('click', () => {
        document.getElementById('gym-area').innerHTML = `<h4 class="text-slate-100 font-medium">Gym 2: Vocal Sandbox</h4><p class="text-slate-400">Hold-to-Speak UI placeholder</p>`;
    });
    document.getElementById('btn-facial').addEventListener('click', () => {
        document.getElementById('gym-area').innerHTML = `<h4 class="text-slate-100 font-medium">Gym 3: Facial Gym</h4><p class="text-slate-400">Expression training placeholder</p>`;
    });
    document.getElementById('logout').addEventListener('click', () => {
        localStorage.removeItem('ss_token');
        window.location.href = '/';
    });
}

// init
(async function init() {
    await fetchMe();
    await loadLeaderboard();
    setupButtons();
})();
