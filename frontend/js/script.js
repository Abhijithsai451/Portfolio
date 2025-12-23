particlesJS('particles-js', {
    particles: {
        number: {
            value: 80,
            density: {
                enable: true,
                value_area: 800
            }
        },
        color: {
            value: '#00c9ff'
        },
        shape: {
            type: 'circle',
            stroke: {
                width: 0,
                color: '#000000'
            }
        },
        opacity: {
            value: 0.5,
            random: true,
            anim: {
                enable: true,
                speed: 1,
                opacity_min: 0.1,
                sync: false
            }
        },
        size: {
            value: 3,
            random: true,
            anim: {
                enable: true,
                speed: 2,
                size_min: 0.1,
                sync: false
            }
        },
        line_linked: {
            enable: true,
            distance: 150,
            color: '#00c9ff',
            opacity: 0.4,
            width: 1
        },
        move: {
            enable: true,
            speed: 2,
            direction: 'none',
            random: true,
            straight: false,
            out_mode: 'out',
            bounce: false,
            attract: {
                enable: false,
                rotateX: 600,
                rotateY: 1200
            }
        }
    },
    interactivity: {
        detect_on: 'canvas',
        events: {
            onhover: {
                enable: true,
                mode: 'grab'
            },
            onclick: {
                enable: true,
                mode: 'push'
            },
            resize: true
        },
        modes: {
            grab: {
                distance: 140,
                line_linked: {
                    opacity: 1
                }
            },
            push: {
                particles_nb: 4
            }
        }
    },
    retina_detect: true
});

// Counter animation for stats
function animateCounter(elementId, finalValue, duration) {
    let startTime = null;
    const element = document.getElementById(elementId);
    const initialValue = 0;

    function updateCounter(timestamp) {
        if (!startTime) startTime = timestamp;
        const progress = Math.min((timestamp - startTime) / duration, 1);

        const currentValue = Math.floor(progress * (finalValue - initialValue) + initialValue);
        element.textContent = currentValue;

        if (progress < 1) {
            requestAnimationFrame(updateCounter);
        } else {
            element.textContent = finalValue;
        }
    }

    requestAnimationFrame(updateCounter);
}

// Add scroll animation for elements
function checkScroll() {
    const elements = document.querySelectorAll('.skill-card, .stat');

    elements.forEach(element => {
        const elementPosition = element.getBoundingClientRect().top;
        const screenPosition = window.innerHeight / 1.3;

        if (elementPosition < screenPosition) {
            element.style.opacity = 1;
            element.style.transform = 'translateY(0)';
        }
    });
}

// Initialize element styles for animation
document.querySelectorAll('.skill-card, .stat').forEach(element => {
    element.style.opacity = 0;
    element.style.transform = 'translateY(20px)';
    element.style.transition = 'all 0.5s ease';
});

window.addEventListener('scroll', checkScroll);
window.addEventListener('load', checkScroll);


// --- Global Chat Variables and Helper Functions ---
let chatMessagesContainer;
let chatInput;

// Add message to chat display
function addMessage(text, isUser = false) {
    if (!chatMessagesContainer) {
        console.error("Chat messages container not found. Make sure element with class '.ai-messages' exists and is initialized.");
        return;
    }
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', isUser ? 'user-message' : 'ai-message');

    const avatar = document.createElement('div');
    avatar.classList.add('message-avatar');
    avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<i class="fas fa-sparkles"></i>';

    const content = document.createElement('div');
    content.classList.add('message-content');
    content.innerHTML = `<p>${text}</p>`;

    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);

    chatMessagesContainer.appendChild(messageDiv);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

// Show typing indicator
function showTypingIndicator() {
    if (!chatMessagesContainer) {
        console.error("Chat messages container not found for typing indicator. Make sure element with class '.ai-messages' exists and is initialized.");
        return null;
    }
    const thinkingIndicator = document.createElement('div');
    thinkingIndicator.classList.add('thinking');
    thinkingIndicator.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-sparkles"></i>
        </div>
        <div class="message-content">
            <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessagesContainer.appendChild(thinkingIndicator);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    return thinkingIndicator;
}

// Hide typing indicator
function hideTypingIndicator(indicatorElement) {
    if (indicatorElement && chatMessagesContainer && chatMessagesContainer.contains(indicatorElement)) {
        chatMessagesContainer.removeChild(indicatorElement);
    }
}

// API configuration - Update for production
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-backend-production-url.railway.app'; // <--- IMPORTANT: Update this URL for your production environment

// Enhanced error handling for API calls
async function makeApiRequest(endpoint, options = {}) {
    try {
        console.log(`Making API request to: ${API_BASE_URL}${endpoint}`);
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        console.log(`API response status: ${response.status}`);
        if (!response.ok) {
            throw new Error(`API error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// Enhanced sample question handler
async function handleSampleQuestion(question, btn) {
    const originalText = btn.innerHTML;
    btn.innerHTML = 'Asking...';
    btn.style.opacity = '0.7';
    btn.disabled = true;

    addMessage(question, true); // User message

    const typingIndicator = showTypingIndicator();

    try {
        const data = await makeApiRequest('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message: question })
        });

        hideTypingIndicator(typingIndicator);
        addMessage(data.response, false); // AI response

    } catch (error) {
        hideTypingIndicator(typingIndicator);
        addMessage("I'm having trouble connecting to my knowledge base. Please try again later.", false); // AI error message
        console.error('Chat error:', error);
    } finally {
        btn.innerHTML = originalText;
        btn.style.opacity = '1';
        btn.disabled = false;
    }
}

// Enhanced message sending
async function handleSendMessage(message) {
    if (!message.trim()) return;

    addMessage(message, true); // User message

    if (chatInput) {
        chatInput.style.opacity = '0.5';
        setTimeout(() => {
            chatInput.value = '';
            chatInput.style.opacity = '1';
        }, 300);
    }


    const typingIndicator = showTypingIndicator();

    try {
        const data = await makeApiRequest('/api/chat', {
            method: 'POST',
            body: JSON.stringify({ message: message })
        });

        hideTypingIndicator(typingIndicator);
        addMessage(data.response, false); // AI response

    } catch (error) {
        hideTypingIndicator(typingIndicator);
        addMessage("I'm having trouble connecting right now. Please try again.", false); // AI error message
        console.error('Send message error:', error);
    }
}

// Initialize Chat Window Toggle Logic
function initChatToggle() {
    const launcher = document.getElementById('chat-launcher');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('chat-close');

    if (launcher && chatWindow) {
        launcher.addEventListener('click', () => {
            chatWindow.classList.toggle('hidden');
            const icon = launcher.querySelector('i');
            if (chatWindow.classList.contains('hidden')) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-robot');
            } else {
                // Focus input when opened
                const input = document.querySelector('.ai-input');
                if (input) setTimeout(() => input.focus(), 300);
            }
        });
    }

    if (closeBtn && chatWindow) {
        closeBtn.addEventListener('click', () => {
            chatWindow.classList.add('hidden');
            const launcherIcon = document.getElementById('chat-launcher').querySelector('i');
            launcherIcon.classList.remove('fa-times');
            launcherIcon.classList.add('fa-robot');
        });
    }
}

// Initialize Chat Event Listeners
function initChatSection() {
    const chatSendBtn = document.querySelector('.ai-send-btn'); // Using class selector

    if (!chatInput) {
        console.error("Chat input element with class '.ai-input' not found. Cannot initialize chat section fully.");
        return;
    }
    if (!chatSendBtn) {
        console.error("Chat send button element with class '.ai-send-btn' not found. Cannot initialize chat section fully.");
        return;
    }

    // Sample question buttons
    const sampleQuestionBtns = document.querySelectorAll('.sample-question-btn');
    sampleQuestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.textContent;
            handleSampleQuestion(question, btn);
        });
    });

    // Send message on button click
    chatSendBtn.addEventListener('click', () => {
        const message = chatInput.value.trim();
        if (message) {
            handleSendMessage(message);
        }
    });

    // Send message on Enter key
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const message = chatInput.value.trim();
            if (message) {
                handleSendMessage(message);
            }
        }
    });
}

// Add connection status indicator
function updateConnectionStatus() {
    const statusIndicator = document.getElementById('connection-status') || createConnectionStatus();

    fetch(`${API_BASE_URL}/api/health`)
        .then(response => {
            if (response.ok) {
                statusIndicator.className = 'connection-status connected';
                statusIndicator.title = 'AI Agent: Connected';
            } else {
                statusIndicator.className = 'connection-status disconnected';
                statusIndicator.title = 'AI Agent: Disconnected';
            }
        })
        .catch(error => {
            statusIndicator.className = 'connection-status disconnected';
            statusIndicator.title = 'AI Agent: Disconnected';
        });
}

function createConnectionStatus() {
    // Disabled to remove unused icon
    return null;
}

// Check backend connection on page load - Disabled to remove unused icon
function checkBackendConnection() {
    // const statusIndicator = document.getElementById('connection-status') || createConnectionStatus();

    fetch(`${API_BASE_URL}/api/health`)
        .then(response => {
            if (response.ok) {
                // statusIndicator.style.backgroundColor = '#4CAF50';
                console.log('✅ Backend connection successful');
            } else {
                // statusIndicator.style.backgroundColor = '#F44336';
                console.log('❌ Backend connection failed');
            }
        })
        .catch(error => {
            // statusIndicator.style.backgroundColor = '#F44336';
            console.log('❌ Backend connection error:', error);
        });
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function () {
    animateCounter('project-count', 42, 2000);
    animateCounter('client-count', 28, 2000);
    animateCounter('algorithm-count', 15, 2000);

    // Initialize chat messages container and input globally using class selectors
    chatMessagesContainer = document.querySelector('.ai-messages');
    chatInput = document.querySelector('.ai-input');

    if (!chatMessagesContainer) {
        console.error("CRITICAL: Chat messages container element with class '.ai-messages' not found. Chat functionality will be limited.");
    }
    if (!chatInput) {
        console.error("CRITICAL: Chat input element with class '.ai-input' not found. Chat functionality will be limited.");
    }

    if (!chatInput) {
        console.error("CRITICAL: Chat input element with class '.ai-input' not found. Chat functionality will be limited.");
    }

    initChatSection();
    initChatSection();
    // initChatToggle(); // Floating widget toggle no longer used
    // checkBackendConnection(); - Removed to hide unused icon

    // Check connection every 30 seconds - Removed
    // setInterval(updateConnectionStatus, 30000);
});