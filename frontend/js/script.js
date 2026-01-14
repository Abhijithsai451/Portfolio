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
    const element = document.getElementById(elementId);
    if (!element) return;

    let startTime = null;
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
    // If it's the home page, we want stats to be visible immediately
    if (document.body.classList.contains('home-page') && element.classList.contains('stat')) {
        element.style.opacity = 1;
        element.style.transform = 'translateY(0)';
    } else {
        element.style.opacity = 0;
        element.style.transform = 'translateY(20px)';
    }
    element.style.transition = 'all 0.5s ease';
});

window.addEventListener('scroll', checkScroll);
window.addEventListener('load', checkScroll);


// --- Global Chat Variables and Helper Functions ---
let chatMessagesContainer;
let chatInput;
let isVoiceMode = false;
let isRecording = false;
let recognition;
let synth;
let voiceMicBtn;
let chatSendBtn;
let voiceToggle;

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
    avatar.innerHTML = isUser ? '<i class="fas fa-user"></i>' : '<img src="images/as_logo.png" alt="AS">';

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
            <img src="images/as_logo.png" alt="AS">
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

// --- Voice Mode Logic ---
function initVoiceMode() {
    // Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isRecording = true;
            if (voiceMicBtn) voiceMicBtn.classList.add('recording');
            if (chatInput) chatInput.placeholder = "Listening...";
        };

        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0])
                .map(result => result.transcript)
                .join('');

            if (chatInput) chatInput.value = transcript;

            if (event.results[0].isFinal) {
                stopRecording();
                setTimeout(() => {
                    handleSendMessage(transcript);
                }, 600);
            }
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            stopRecording();
        };

        recognition.onend = () => {
            stopRecording();
        };
    }

    // Speech Synthesis
    if ('speechSynthesis' in window) {
        synth = window.speechSynthesis;
    }
}

function startRecording() {
    if (recognition && !isRecording) {
        try {
            recognition.start();
        } catch (e) {
            console.error("Failed to start recognition:", e);
        }
    }
}

function stopRecording() {
    if (recognition && isRecording) {
        recognition.stop();
        isRecording = false;
        if (voiceMicBtn) voiceMicBtn.classList.remove('recording');
        if (chatInput) chatInput.placeholder = "Ask a question about my experience...";
    }
}

// Play high-quality audio from base64 string
function playAudio(base64Audio) {
    if (!base64Audio) return;

    try {
        // Convert base64 to blob
        const byteCharacters = atob(base64Audio);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'audio/mpeg' });

        // Create URL and play
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play().catch(e => console.error("Audio playback failed:", e));

        // Cleanup URL after playing
        audio.onended = () => URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error playing audio:", error);
    }
}

// API configuration - Update for production
const API_BASE_URL = window.location.origin; // Dynamically use the current origin

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
            body: JSON.stringify({
                message: question,
                is_voice: isVoiceMode // Pass the current mode
            })
        });

        hideTypingIndicator(typingIndicator);
        addMessage(data.response, false); // AI response

        // Play high-quality audio if returned
        if (data.audio) {
            playAudio(data.audio);
        }

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
        chatInput.value = '';
        chatInput.focus();
    }


    const typingIndicator = showTypingIndicator();

    try {
        const data = await makeApiRequest('/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: message,
                is_voice: isVoiceMode // Pass the current mode
            })
        });

        hideTypingIndicator(typingIndicator);
        addMessage(data.response, false); // AI response

        // Play high-quality audio if returned
        if (data.audio) {
            playAudio(data.audio);
        }

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

// Flag to prevent multiple initializations
let isChatInitialized = false;

// Initialize Chat Event Listeners
function initChatSection() {
    if (isChatInitialized) return;

    chatSendBtn = document.querySelector('.ai-send-btn');
    voiceMicBtn = document.getElementById('voice-mic');
    voiceToggle = document.getElementById('voice-toggle');

    if (!chatInput) {
        console.error("Chat input element with class '.ai-input' not found. Cannot initialize chat section fully.");
        return;
    }

    // Initialize Voice Mode
    initVoiceMode();

    // Mode Toggle Logic
    if (voiceToggle) {
        const modeOptions = document.querySelectorAll('.mode-option');

        modeOptions.forEach(option => {
            option.addEventListener('click', () => {
                const isVoice = option.id === 'mode-voice';
                voiceToggle.checked = isVoice;
                voiceToggle.dispatchEvent(new Event('change'));
            });
        });

        voiceToggle.addEventListener('change', () => {
            isVoiceMode = voiceToggle.checked;

            // Update UI active states
            if (isVoiceMode) {
                document.getElementById('mode-voice').classList.add('active');
                document.getElementById('mode-text').classList.remove('active');
                chatSendBtn.style.display = 'none';
                voiceMicBtn.style.display = 'flex';
                chatInput.placeholder = "Click the mic to speak...";
            } else {
                document.getElementById('mode-text').classList.add('active');
                document.getElementById('mode-voice').classList.remove('active');
                chatSendBtn.style.display = 'flex';
                voiceMicBtn.style.display = 'none';
                chatInput.placeholder = "Ask a question about my experience...";
                stopRecording();
                if (synth) synth.cancel();
            }
        });
    }

    // Mic Button Logic
    if (voiceMicBtn) {
        voiceMicBtn.addEventListener('click', () => {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });
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
    if (chatSendBtn) {
        chatSendBtn.addEventListener('click', () => {
            const message = chatInput.value.trim();
            if (message) {
                handleSendMessage(message);
            }
        });
    }

    // Send message on Enter key (use keydown to prevent default form submission if applicable)
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent default behavior
            const message = chatInput.value.trim();
            if (message) {
                handleSendMessage(message);
            }
        }
    });

    isChatInitialized = true;
    console.log("Chat section initialized successfully.");
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
// Initialize when the page loads
document.addEventListener('DOMContentLoaded', function () {
    // Only run if not already running (though DOMContentLoaded should only fire once per page load)
    if (document.body.getAttribute('data-chat-initialized') === 'true') return;
    document.body.setAttribute('data-chat-initialized', 'true');

    animateCounter('project-count', 42, 2000);
    animateCounter('client-count', 28, 2000);
    animateCounter('algorithm-count', 15, 2000);

    // Initialize chat messages container and input globally using class selectors
    chatMessagesContainer = document.querySelector('.ai-messages');
    chatInput = document.querySelector('.ai-input');

    // Initialize Chat if elements exist
    if (chatMessagesContainer && chatInput) {
        initChatSection();
    }
});