// Handle Play Button Click
function handlePlayClick() {
    const message = 'Ready to claim your free daily match? 🔥\n\nNavigate to the game arena and prepare your hottest take!';
    showNotification(message);
    console.log('[Akobato] Play button clicked - Redirecting to game...');
    // In a real app, this would redirect to /game or open the game interface
    // window.location.href = '/game';
}

// Handle Token Bundles Button Click
function handleTokensClick() {
    const message = 'Token Bundles 💰\n\n🟡 Starter Pack: 5 tokens - $2.99\n🟠 Grudge Master: 15 tokens - $7.99\n🔴 Roast Legend: 50 tokens - $19.99\n\nGrab unlimited arguments. Let the victories pile up!';
    showNotification(message);
    console.log('[Akobato] Tokens button clicked - Showing bundle options...');
    // In a real app, this would open a modal or redirect to checkout
    // window.location.href = '/checkout';
}

// Show notification popup
function showNotification(message) {
    // Create overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
    `;

    // Create modal
    const modal = document.createElement('div');
    modal.style.cssText = `
        background: linear-gradient(135deg, #1e1e3f 0%, #16213e 100%);
        border: 2px solid #05D9E8;
        border-radius: 12px;
        padding: 40px;
        max-width: 400px;
        width: 90%;
        text-align: center;
        box-shadow: 0 0 40px rgba(5, 217, 232, 0.3);
        animation: popIn 0.3s ease-out;
    `;

    // Create message
    const messageEl = document.createElement('p');
    messageEl.style.cssText = `
        color: #e0e0e0;
        font-size: 1.05rem;
        line-height: 1.8;
        margin-bottom: 30px;
        white-space: pre-line;
    `;
    messageEl.textContent = message;

    // Create close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Got It! 🚀';
    closeBtn.style.cssText = `
        padding: 12px 30px;
        background-color: #FF2A6D;
        color: #0a0a0a;
        border: none;
        border-radius: 6px;
        font-weight: 700;
        cursor: pointer;
        font-size: 1rem;
        transition: all 0.3s ease;
    `;

    closeBtn.addEventListener('mouseover', () => {
        closeBtn.style.backgroundColor = '#ff1155';
        closeBtn.style.boxShadow = '0 0 30px rgba(255, 42, 109, 0.5)';
    });

    closeBtn.addEventListener('mouseout', () => {
        closeBtn.style.backgroundColor = '#FF2A6D';
        closeBtn.style.boxShadow = 'none';
    });

    closeBtn.addEventListener('click', () => {
        overlay.remove();
    });

    // Add keyframe animation if not already in CSS
    if (!document.getElementById('popIn-animation')) {
        const style = document.createElement('style');
        style.id = 'popIn-animation';
        style.textContent = `
            @keyframes popIn {
                from {
                    opacity: 0;
                    transform: scale(0.8);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
        `;
        document.head.appendChild(style);
    }

    modal.appendChild(messageEl);
    modal.appendChild(closeBtn);
    overlay.appendChild(modal);
    document.body.appendChild(overlay);

    // Close on overlay click
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            overlay.remove();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            overlay.remove();
        }
    }, { once: true });
}

// Scroll animations for cards
function observeCards() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
    });

    const cards = document.querySelectorAll('.game-card');
    cards.forEach((card) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Akobato] Landing page loaded');
    observeCards();
});
