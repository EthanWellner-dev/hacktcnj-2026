// auth.js handles login and register pages

async function loginHandler(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const status = document.getElementById('status');
    status.textContent = '';

    try {
        const resp = await fetch('/api/users/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();
        if (resp.ok && data.status === 'success') {
            // store JWT and redirect to dashboard
            localStorage.setItem('ss_token', data.token);
            window.location.href = '/dashboard';
        } else {
            status.textContent = data.message || 'Login failed';
            status.style.color = 'var(--rose, #fb7185)';
        }
    } catch (err) {
        console.error(err);
        status.textContent = 'Server error';
        status.style.color = 'var(--rose, #fb7185)';
    }
}

async function registerHandler(e) {
    e.preventDefault();
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const persona = document.getElementById('persona').value;
    const age = document.getElementById('age').value;
    const gender = document.getElementById('gender').value || null;
    const bio = document.getElementById('bio').value.trim();
    const status = document.getElementById('status');
    
    // Collect hobbies
    const hobbyCheckboxes = document.querySelectorAll('.hobby-checkbox:checked');
    const hobbies = Array.from(hobbyCheckboxes).map(cb => cb.value);
    
    status.textContent = '';

    try {
        const resp = await fetch('/api/users/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                username, 
                password, 
                persona,
                age: age ? parseInt(age) : null,
                gender,
                hobbies,
                bio
            })
        });
        const data = await resp.json();
        if (resp.ok && data.status === 'success') {
            status.textContent = 'Account created. Redirecting to login...';
            status.style.color = '#34d399';
            setTimeout(() => window.location.href = '/', 1200);
        } else {
            status.textContent = data.message || 'Signup failed';
            status.style.color = '#fb7185';
        }
    } catch (err) {
        console.error(err);
        status.textContent = 'Server error';
        status.style.color = '#fb7185';
    }
}

// attach to forms if present
const loginForm = document.getElementById('login-form');
if (loginForm) loginForm.addEventListener('submit', loginHandler);
const registerForm = document.getElementById('register-form');
if (registerForm) registerForm.addEventListener('submit', registerHandler);
