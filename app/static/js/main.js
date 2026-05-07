// Global JS — available on every page

async function logout() {
    const res = await fetch('/api/auth/logout', { method: 'POST' })
    if (res.ok) window.location.href = '/'
}

// Close modals when clicking the dark backdrop
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('fixed')) {
        e.target.classList.add('hidden')
    }
})

// Close modals with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.fixed:not(.hidden)').forEach(modal => {
            modal.classList.add('hidden')
        })
    }
})