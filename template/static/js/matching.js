// matching.js - Handles user matching and chat group assignment

let currentUser = null;
let matchedUsers = [];

async function initializeMatching() {
    try {

        // Get current user info
        const token = localStorage.getItem('ss_token');
        if (!token) {
            window.location.href = '/';
            return;
        }

        const userResp = await fetch('/api/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (!userResp.ok) {
            window.location.href = '/';
            return;
        }

        currentUser = await userResp.json();
        
        // Update XP display in nav
        const xpDisplay = document.getElementById('user-xp');
        if (xpDisplay) {
            xpDisplay.textContent = currentUser.xp || 0;
        }
        
        // Load matches
        await loadMatches();
    } catch (err) {
        console.error('Error initializing matching:', err);
    }
}

async function loadMatches() {
    try {
        // Fetch matches from API
        const resp = await fetch('/api/users/matching/get-matches', {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('ss_token')}` }
        });

        if (resp.ok) {
            const data = await resp.json();
            matchedUsers = data.matches || [];
        } else {
            // Fallback: generate mock matches if endpoint fails
            generateMockMatches();
        }

        renderMatches();
    } catch (err) {
        console.error('Error loading matches:', err);
        // Fallback to mock data for demonstration
        generateMockMatches();
        renderMatches();
    }
}

function generateMockMatches() {
    // Generate 2-5 mock users for demonstration
    const mockHobbies = [
        ['gaming', 'music', 'tech'],
        ['reading', 'cooking', 'art'],
        ['sports', 'fitness', 'travel'],
        ['gaming', 'tech'],
        ['music', 'art', 'cooking']
    ];

    const mockPersonas = ['job_seeker', 'awkward_texter', 'conflict_avoider'];
    const mockGenders = ['male', 'female', 'non-binary'];
    const mockBios = [
        'Love connecting with people and learning new things',
        'Always up for interesting conversations',
        'Passionate about tech and gaming',
        'Creative soul looking for like-minded friends',
        'Fitness enthusiast and travel junkie'
    ];

    const mockUsernames = ['Alex23', 'Jordan_Arts', 'Casey_Tech', 'Morgan_Fit', 'Riley_Books'];

    const numMatches = Math.floor(Math.random() * 4) + 2; // 2-5 matches

    matchedUsers = [];
    for (let i = 0; i < numMatches; i++) {
        matchedUsers.push({
            _id: `mock-${i}`,
            username: mockUsernames[i],
            age: Math.floor(Math.random() * 40) + 18,
            gender: mockGenders[Math.floor(Math.random() * mockGenders.length)],
            persona: mockPersonas[Math.floor(Math.random() * mockPersonas.length)],
            hobbies: mockHobbies[i % mockHobbies.length],
            bio: mockBios[i],
            compatibility: 75 + Math.floor(Math.random() * 25) // 75-100
        });
    }
}

function renderMatches() {
    const container = document.getElementById('matches-container');
    const loadingState = document.getElementById('loading-state');
    const noMatchesState = document.getElementById('no-matches-state');

    if (matchedUsers.length === 0) {
        container.style.display = 'none';
        loadingState.style.display = 'none';
        noMatchesState.style.display = 'block';
        return;
    }

    container.style.display = 'grid';
    loadingState.style.display = 'none';
    noMatchesState.style.display = 'none';
    container.innerHTML = '';

    matchedUsers.forEach((user, index) => {
        const card = createMatchCard(user);
        container.appendChild(card);
        // Stagger animation
        setTimeout(() => {
            card.classList.add('match-fade-in');
        }, index * 50);
    });
}

function createMatchCard(user) {
    const card = document.createElement('div');
    card.className = 'match-card rounded-xl p-6 flex flex-col';
    card.style.opacity = '0';

    const hobbiesHtml = user.hobbies
        .map(h => `<span class="hobby-tag px-2 py-1 rounded text-xs">${h}</span>`)
        .join('');

    const compatibility = user.compatibility || 
        Math.floor(Math.random() * 26) + 75; // 75-100

    card.innerHTML = `
        <div class="flex items-start justify-between mb-4">
            <div>
                <h3 class="text-lg font-bold text-white">${user.username}</h3>
                <p class="text-xs text-slate-400 mt-1">${user.age || '?'} • ${user.gender || 'Unknown'}</p>
            </div>
            <div class="text-right">
                <div class="text-2xl font-bold text-purple-400">${compatibility}%</div>
                <p class="text-xs text-slate-400">Match</p>
            </div>
        </div>

        <div class="mb-4 pb-4 border-b border-white/10">
            <p class="text-sm text-slate-300">${user.bio || 'No bio provided'}</p>
        </div>

        <div class="mb-4">
            <p class="text-xs text-slate-400 mb-2 uppercase tracking-wider">Personality</p>
            <div class="inline-block bg-purple-900/30 text-purple-300 px-3 py-1 rounded text-xs border border-purple-500/30">
                ${formatPersona(user.persona)}
            </div>
        </div>

        <div class="mb-4">
            <p class="text-xs text-slate-400 mb-2 uppercase tracking-wider">Interests</p>
            <div class="flex flex-wrap gap-2">
                ${hobbiesHtml || '<span class="text-xs text-slate-500">No interests listed</span>'}
            </div>
        </div>

        <button onclick="startChat('${user.username}')" class="btn-start-chat text-white px-4 py-2 rounded-lg font-medium mt-auto transition-all">
            <i class="fa-solid fa-comments mr-2"></i>Start Chat
        </button>
    `;

    return card;
}

function formatPersona(persona) {
    const personas = {
        'job_seeker': 'Job Seeker',
        'awkward_texter': 'Awkward Texter',
        'conflict_avoider': 'Conflict Avoider'
    };
    return personas[persona] || persona;
}

async function startChat(username) {
    // Navigate to the group chat room
    window.location.href = '/chat';
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initializeMatching);
