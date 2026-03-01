// chat.js - Group chat functionality

let currentUser = null;
let currentRoomId = null;
let participants = new Set();
let lastMessageId = null;

async function initChat() {
    try {
        const token = localStorage.getItem('ss_token');
        if (!token) {
            window.location.href = '/';
            return;
        }

        // Get current user
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

        // Get or create room ID (using a hash-based room for matched users)
        const matchedResp = await fetch('/api/users/matching/get-matches', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (matchedResp.ok) {
            const matchData = await matchedResp.json();
            const matches = matchData.matches || [];
            
            // Create a room ID from matched user IDs
            if (matches.length > 0) {
                const matchIds = matches.map(m => m._id || m.username).sort();
                currentRoomId = `room-${currentUser.user_id}-${matchIds.join('-')}`.substring(0, 100);
                
                // Build participant list
                participants.add(currentUser.username);
                matches.forEach(m => participants.add(m.username));

                // Update UI
                document.getElementById('chat-title').textContent = `Chat with ${matches.length} ${matches.length === 1 ? 'person' : 'people'}`;
                renderParticipants();
            }
        }

        // Setup event handlers
        document.getElementById('btn-send').addEventListener('click', sendMessage);
        document.getElementById('message-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Load messages and start auto-refresh (only when page is focused)
        await loadMessages();
        
        // Use visibility API to only refresh when page is focused
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                loadMessages(false);  // Refresh immediately when user refocuses (no animation)
            }
        });
        
        // Auto-refresh only when page is visible
        setInterval(() => {
            if (!document.hidden) {
                loadMessages(false);  // Auto-refresh without animation
            }
        }, 3000);  // Refresh every 3 seconds when focused

    } catch (err) {
        console.error('Chat init error:', err);
    }
}

async function loadMessages() {
    try {
        if (!currentRoomId) return;

        const resp = await fetch(`/api/chat/get-messages?room_id=${encodeURIComponent(currentRoomId)}&limit=50`, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('ss_token')}` }
        });

        if (resp.ok) {
            const data = await resp.json();
            const messages = data.messages || [];
            renderMessages(messages);
        }
    } catch (err) {
        console.error('Error loading messages:', err);
    }
}

function renderMessages(messages, isInitialLoad = true) {
    const container = document.getElementById('messages-container');
    const token = localStorage.getItem('ss_token');

    // Clear and rebuild
    container.innerHTML = '';

    messages.forEach((msg) => {
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        const msgContent = document.createElement('div');
        msgContent.className = `message-content ${msg.has_harmful_content ? 'content-flagged' : ''}`;

        // Username and timestamp
        const header = document.createElement('div');
        header.className = 'message-username';
        header.textContent = msg.username;
        msgContent.appendChild(header);

        // Message text
        if (msg.text) {
            const textEl = document.createElement('div');
            textEl.style.marginBottom = '8px';
            textEl.textContent = msg.text;
            msgContent.appendChild(textEl);
        }

        // Image if present
        if (msg.image_url) {
            const img = document.createElement('img');
            img.className = 'message-image';
            img.src = msg.image_url;
            img.alt = 'Message image';
            img.addEventListener('click', () => openImageModal(msg.image_url));
            msgContent.appendChild(img);
        }

        // Reaction buttons (for all messages)
        const reactionsDiv = document.createElement('div');
        reactionsDiv.className = 'reactions-container';

        const reactions = msg.reactions || {};
        const emojis = ['👍', '❤️', '😂', '🎉', '🤔', '😍'];

        emojis.forEach(emoji => {
            const btn = document.createElement('button');
            btn.className = 'reaction-btn';
            const usernames = reactions[emoji] || [];
            btn.innerHTML = `${emoji} ${usernames.length > 0 ? usernames.length : ''}`;

            if (usernames.includes(currentUser.username)) {
                btn.classList.add('active');
            }

            btn.addEventListener('click', () => reactToMessage(msg._id, emoji, token));
            reactionsDiv.appendChild(btn);
        });

        msgContent.appendChild(reactionsDiv);

        // Timestamp
        const timeEl = document.createElement('div');
        timeEl.className = 'message-timestamp';
        const date = new Date(msg.timestamp);
        timeEl.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        msgContent.appendChild(timeEl);

        // Add double-click handler for emoji reactions
        bubble.addEventListener('dblclick', (e) => {
            e.preventDefault();
            showEmojiPicker(msg._id, token);
        });

        bubble.appendChild(msgContent);

        // Content warning if flagged
        if (msg.has_harmful_content) {
            const warning = document.createElement('div');
            warning.className = 'text-xs text-rose-400 mt-2';
            warning.textContent = `⚠️ This message contained unkind language and was filtered.`;
            bubble.appendChild(warning);
        }

        container.appendChild(bubble);
    });

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function renderParticipants() {
    const list = document.getElementById('participants-list');
    list.innerHTML = '';

    Array.from(participants).forEach(username => {
        const item = document.createElement('div');
        item.className = 'participant-item';
        item.innerHTML = `
            <span class="participant-online"></span>
            <span>${username}</span>
        `;
        list.appendChild(item);
    });
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const text = input.value.trim();
    const warning = document.getElementById('content-warning');

    if (!text) return;

    try {
        const resp = await fetch('/api/chat/post-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('ss_token')}`
            },
            body: JSON.stringify({
                room_id: currentRoomId,
                text: text
            })
        });

        if (resp.ok) {
            const data = await resp.json();
            input.value = '';
            warning.classList.add('hidden');

            // Show content warning if applicable
            if (data.content_warning) {
                warning.textContent = data.content_warning;
                warning.classList.remove('hidden');
            }

            // Reload messages immediately (without animation)
            await loadMessages(false);
        } else {
            const err = await resp.json();
            alert(`Error: ${err.message}`);
        }
    } catch (err) {
        console.error('Error sending message:', err);
        alert('Failed to send message');
    }
}

async function reactToMessage(messageId, emoji, token) {
    try {
        const resp = await fetch('/api/chat/react', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message_id: messageId,
                emoji: emoji
            })
        });

        if (resp.ok) {
            // Reload messages to show updated reactions (without animation)
            await loadMessages(false);
        }
    } catch (err) {
        console.error('Error reacting:', err);
    }
}

function openImageModal(imageUrl) {
    // Simple modal for viewing image
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        cursor: pointer;
    `;

    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        border-radius: 12px;
    `;

    modal.appendChild(img);
    modal.addEventListener('click', () => document.body.removeChild(modal));
    document.body.appendChild(modal);
}

function showEmojiPicker(messageId, token) {
    // Show modal with emoji options for quick reaction
    const emojis = ['👍', '❤️', '😂', '🎉', '🤔', '😍'];
    
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        backdrop-filter: blur(4px);
    `;

    const picker = document.createElement('div');
    picker.style.cssText = `
        background: rgba(15, 23, 42, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 16px;
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        max-width: 300px;
        backdrop-filter: blur(10px);
    `;

    emojis.forEach(emoji => {
        const btn = document.createElement('button');
        btn.innerHTML = emoji;  // Use innerHTML to ensure proper emoji rendering
        btn.style.cssText = `
            font-size: 48px;
            font-family: 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji', sans-serif;
            background: none;
            border: none;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 12px;
            transition: all 0.2s;
            line-height: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 60px;
            text-rendering: auto;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        `;
        
        btn.addEventListener('mouseenter', () => {
            btn.style.background = 'rgba(168, 85, 247, 0.2)';
            btn.style.transform = 'scale(1.2)';
        });
        
        btn.addEventListener('mouseleave', () => {
            btn.style.background = 'none';
            btn.style.transform = 'scale(1)';
        });
        
        btn.addEventListener('click', async () => {
            await reactToMessage(messageId, emoji, token);
            document.body.removeChild(modal);
        });
        
        picker.appendChild(btn);
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });

    modal.appendChild(picker);
    document.body.appendChild(modal);
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', initChat);
