particlesJS('particles-js', {
    particles: {
        number: { value: 80, density: { enable: true, value_area: 800 } },
        color: { value: '#00c9ff' },
        shape: { type: 'circle' },
        opacity: { value: 0.5, random: true, anim: { enable: true, speed: 1, opacity_min: 0.1 } },
        size: { value: 3, random: true, anim: { enable: true, speed: 2, size_min: 0.1 } },
        line_linked: { enable: true, distance: 150, color: '#00c9ff', opacity: 0.4, width: 1 },
        move: { enable: true, speed: 2, direction: 'none', random: true, out_mode: 'out' }
    },
    interactivity: {
        events: { onhover: { enable: true, mode: 'grab' }, onclick: { enable: true, mode: 'push' }, resize: true },
        modes: { grab: { distance: 140, line_linked: { opacity: 1 } }, push: { particles_nb: 4 } }
    },
    retina_detect: true
});

function animateCounter(elementId, finalValue, duration) {
    const element = document.getElementById(elementId);
    if (!element) return;
    let start = null;
    function step(timestamp) {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        element.textContent = Math.floor(progress * finalValue);
        if (progress < 1) requestAnimationFrame(step);
        else element.textContent = finalValue;
    }
    requestAnimationFrame(step);
}

function checkScroll() {
    document.querySelectorAll('.skill-card, .stat').forEach(el => {
        const pos = el.getBoundingClientRect().top;
        if (pos < window.innerHeight / 1.3) {
            el.style.opacity = 1;
            el.style.transform = 'translateY(0)';
        }
    });
}

document.querySelectorAll('.skill-card, .stat').forEach(el => {
    if (document.body.classList.contains('home-page') && el.classList.contains('stat')) {
        el.style.opacity = 1;
        el.style.transform = 'translateY(0)';
    } else {
        el.style.opacity = 0;
        el.style.transform = 'translateY(20px)';
    }
    el.style.transition = 'all 0.5s ease';
});

window.addEventListener('scroll', checkScroll);
window.addEventListener('load', checkScroll);

let chatMessagesContainer, chatInput, isVoiceMode = false, isRecording = false, recognition, synth;
let voiceMicBtn, chatSendBtn, voiceToggle, chatBox, voiceInterface, voiceActionBtn, voiceVisualizer, voiceStatus;

function addMessage(text, isUser = false) {
    if (!chatMessagesContainer) return;
    const msg = document.createElement('div');
    msg.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    msg.innerHTML = `
        <div class="message-avatar">${isUser ? '<i class="fas fa-user"></i>' : '<img src="images/as_logo.png" alt="AS">'}</div>
        <div class="message-content"><p>${text}</p></div>
    `;
    chatMessagesContainer.appendChild(msg);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
}

function showTyping() {
    if (!chatMessagesContainer) return null;
    const div = document.createElement('div');
    div.className = 'thinking';
    div.innerHTML = `<div class="message-avatar"><img src="images/as_logo.png" alt="AS"></div>
                     <div class="message-content"><div class="thinking-dots"><span></span><span></span><span></span></div></div>`;
    chatMessagesContainer.appendChild(div);
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    return div;
}

function hideTyping(el) { if (el && chatMessagesContainer) chatMessagesContainer.removeChild(el); }

function initVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SR) {
        recognition = new SR();
        recognition.onstart = () => {
            isRecording = true;
            if (voiceMicBtn) voiceMicBtn.classList.add('recording');
            if (voiceActionBtn) voiceActionBtn.classList.add('recording');
            if (voiceStatus) voiceStatus.textContent = "Listening...";
            if (voiceVisualizer) voiceVisualizer.classList.add('active');
        };
        recognition.onresult = (e) => {
            const t = e.results[0][0].transcript;
            if (chatInput) chatInput.value = t;
            if (e.results[0].isFinal) {
                stopRec();
                setTimeout(() => handleSend(t), 600);
            }
        };
        recognition.onend = stopRec;
    }
    if ('speechSynthesis' in window) synth = window.speechSynthesis;
}

function startRec() { if (recognition && !isRecording) recognition.start(); }
function stopRec() {
    if (recognition && isRecording) {
        recognition.stop();
        isRecording = false;
        [voiceMicBtn, voiceActionBtn].forEach(b => b?.classList.remove('recording'));
        if (voiceStatus) voiceStatus.textContent = "Processing...";
        if (voiceVisualizer) voiceVisualizer.classList.remove('active');
    }
}

function playAudio(b64) {
    if (!b64) return;
    const blob = new Blob([new Uint8Array(atob(b64).split("").map(c => c.charCodeAt(0)))], { type: 'audio/mpeg' });
    const audio = new Audio(URL.createObjectURL(blob));
    if (voiceVisualizer) voiceVisualizer.classList.add('active');
    if (voiceStatus) voiceStatus.textContent = "Speaking...";
    audio.play();
    audio.onended = () => {
        if (voiceVisualizer) voiceVisualizer.classList.remove('active');
        if (voiceStatus) voiceStatus.textContent = "Tap to speak";
    };
}

const API_BASE = window.location.origin;
async function apiReq(url, opt = {}) {
    const res = await fetch(API_BASE + url, { headers: { 'Content-Type': 'application/json' }, ...opt });
    if (!res.ok) throw new Error(res.statusText);
    return res.json();
}

async function handleSend(msg) {
    if (!msg.trim()) return;
    addMessage(msg, true);
    if (chatInput) { chatInput.value = ''; chatInput.focus(); }
    const loader = showTyping();
    try {
        const data = await apiReq('/api/chat', { method: 'POST', body: JSON.stringify({ message: msg, is_voice: isVoiceMode }) });
        hideTyping(loader);
        addMessage(data.response);
        if (data.audio) playAudio(data.audio);
    } catch (e) {
        hideTyping(loader);
        addMessage("Error connecting to assistant.");
    }
}

function initChat() {
    const launcher = document.getElementById('chat-launcher'), win = document.getElementById('chat-window'), close = document.getElementById('chat-close');
    if (launcher && win) launcher.onclick = () => {
        win.classList.toggle('hidden');
        const icon = launcher.querySelector('i');
        icon.classList.toggle('fa-robot', win.classList.contains('hidden'));
        icon.classList.toggle('fa-times', !win.classList.contains('hidden'));
        if (!win.classList.contains('hidden')) setTimeout(() => chatInput?.focus(), 300);
    };
    if (close && win) close.onclick = () => win.classList.add('hidden');

    chatSendBtn = document.querySelector('.ai-send-btn');
    voiceMicBtn = document.getElementById('voice-mic-main');
    voiceToggle = document.getElementById('voice-toggle');
    chatBox = document.querySelector('.chat-box');
    voiceInterface = document.getElementById('voice-interface');
    voiceActionBtn = document.getElementById('voice-action-btn');
    voiceVisualizer = document.getElementById('voice-visualizer');
    voiceStatus = document.getElementById('voice-status');

    initVoice();

    if (voiceToggle) {
        document.querySelectorAll('.mode-option').forEach(opt => {
            opt.onclick = () => { voiceToggle.checked = opt.id === 'mode-voice'; voiceToggle.dispatchEvent(new Event('change')); };
        });
        voiceToggle.onchange = () => {
            isVoiceMode = voiceToggle.checked;
            document.getElementById('mode-voice').classList.toggle('active', isVoiceMode);
            document.getElementById('mode-text').classList.toggle('active', !isVoiceMode);
            chatBox.style.display = isVoiceMode ? 'none' : 'flex';
            voiceInterface.style.display = isVoiceMode ? 'flex' : 'none';
            if (!isVoiceMode) { stopRec(); synth?.cancel(); }
        };
    }

    [voiceMicBtn, voiceActionBtn].forEach(b => b && (b.onclick = () => isRecording ? stopRec() : startRec()));
    document.querySelectorAll('.sample-question-btn').forEach(b => b.onclick = () => handleSend(b.textContent));
    chatSendBtn && (chatSendBtn.onclick = () => handleSend(chatInput.value));
    chatInput && (chatInput.onkeydown = (e) => e.key === 'Enter' && handleSend(chatInput.value));
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.body.dataset.chatInit) return;
    document.body.dataset.chatInit = "true";
    animateCounter('project-count', 12, 2000);
    animateCounter('publication-count', 25, 2000);
    animateCounter('algorithm-count', 18, 2000);
    chatMessagesContainer = document.querySelector('.ai-messages');
    chatInput = document.querySelector('.ai-input');
    if (chatMessagesContainer && chatInput) initChat();
});