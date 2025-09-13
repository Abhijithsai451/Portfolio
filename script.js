// Preloader
window.addEventListener('load', function() {
    const preloader = document.getElementById('preloader');
    setTimeout(() => {
        preloader.style.opacity = '0';
        setTimeout(() => {
            preloader.style.display = 'none';
        }, 500);
    }, 1500);
});

// Initialize Math Background
function initMathBackground() {
    const canvas = document.getElementById('math-canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    
    // Math symbols to draw
    const symbols = ['∑', '∫', '∂', '√', 'π', '∞', '±', '≈', '≠', '≤', '≥', '→', '∀', '∃', '∈'];
    const particles = [];
    
    // Create particles
    for (let i = 0; i < 50; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 20 + 10,
            speed: Math.random() * 0.5 + 0.2,
            symbol: symbols[Math.floor(Math.random() * symbols.length)],
            opacity: Math.random() * 0.5 + 0.1
        });
    }
    
    // Draw function
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.font = '16px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        particles.forEach(particle => {
            ctx.fillStyle = `rgba(74, 111, 165, ${particle.opacity})`;
            ctx.fillText(particle.symbol, particle.x, particle.y);
            
            // Move particles
            particle.y += particle.speed;
            
            // Reset particles that go off screen
            if (particle.y > canvas.height) {
                particle.y = 0 - particle.size;
                particle.x = Math.random() * canvas.width;
            }
        });
        
        requestAnimationFrame(draw);
    }
    
    draw();
}

// Initialize animated graphs
function initGraphs() {
    // Hero graph animation
    const heroGraph = document.getElementById('hero-graph');
    if (heroGraph) {
        heroGraph.innerHTML = '<div class="graph-placeholder">Data Visualization</div>';
    }
    
    // Project graphs
    for (let i = 1; i <= 6; i++) {
        const projectGraph = document.getElementById(`project-graph-${i}`);
        if (projectGraph) {
            projectGraph.innerHTML = `<div class="graph-placeholder">Graph ${i}</div>`;
        }
    }
}

// Sticky Header
window.addEventListener('scroll', function() {
    const header = document.getElementById('header');
    const backToTop = document.getElementById('back-to-top');
    
    if (window.scrollY > 50) {
        header.classList.add('scrolled');
    } else {
        header.classList.remove('scrolled');
    }
    
    if (window.scrollY > 500) {
        backToTop.classList.add('visible');
    } else {
        backToTop.classList.remove('visible');
    }
});

// Mobile Menu Toggle
const menuBtn = document.querySelector('.menu-btn');
const closeBtn = document.querySelector('.close-btn');
const navLinks = document.querySelector('.nav-links');

if (menuBtn) {
    menuBtn.addEventListener('click', () => {
        navLinks.classList.add('active');
    });
}

if (closeBtn) {
    closeBtn.addEventListener('click', () => {
        navLinks.classList.remove('active');
    });
}

// Close menu when clicking on a link
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        navLinks.classList.remove('active');
    });
});

// Theme Toggle
const themeToggle = document.getElementById('theme-toggle');
const body = document.body;

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        if (body.getAttribute('data-theme') === 'light') {
            body.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            body.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    });
}

// Check for saved theme preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    body.setAttribute('data-theme', savedTheme);
}

// Animated counter for stats
function initCounter() {
    const counters = document.querySelectorAll('.stat-value');
    const speed = 200;
    
    counters.forEach(counter => {
        const target = +counter.getAttribute('data-count');
        const count = +counter.innerText;
        const increment = Math.ceil(target / speed);
        
        if (count < target) {
            counter.innerText = Math.min(count + increment, target);
            setTimeout(() => initCounter(), 1);
        }
    });
}

// Project Filtering
const filterButtons = document.querySelectorAll('.filter-btn');
const projectCards = document.querySelectorAll('.project-card');

if (filterButtons.length > 0) {
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to clicked button
            button.classList.add('active');
            
            const filterValue = button.getAttribute('data-filter');
            
            projectCards.forEach(card => {
                if (filterValue === 'all' || card.getAttribute('data-category') === filterValue) {
                    card.classList.add('visible');
                } else {
                    card.classList.remove('visible');
                }
            });
        });
    });
}

// Research tabs
const researchTabs = document.querySelectorAll('.research-tab');
const researchItems = document.querySelectorAll('.research-item');

if (researchTabs.length > 0) {
    researchTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            researchTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            const tabValue = tab.getAttribute('data-tab');
            
            researchItems.forEach(item => {
                if (tabValue === 'papers' || item.getAttribute('data-category') === tabValue) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
}

// Form submission with toast notification
const contactForm = document.getElementById('contact-form');
const toast = document.getElementById('toast');

if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show toast notification
        toast.classList.add('visible');
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('visible');
        }, 3000);
        
        this.reset();
    });
}

// Download Resume
const downloadResume = document.getElementById('download-resume');
if (downloadResume) {
    downloadResume.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Create a temporary link for download
        const link = document.createElement('a');
        link.href = '#'; // In a real implementation, this would be a PDF file
        link.download = 'Data_Scientist_Resume.pdf';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Show toast notification
        toast.textContent = 'Resume download started!';
        toast.classList.add('visible');
        
        // Hide toast after 3 seconds
        setTimeout(() => {
            toast.classList.remove('visible');
        }, 3000);
    });
}

// ============================================================================
// ENHANCED AI CHAT SECTION FUNCTIONALITY
// ============================================================================

// Chat Section Elements
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');
const sampleQuestionBtns = document.querySelectorAll('.sample-question-btn');

// Add Message to Chat with enhanced animation
function addMessage(text, isUser = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(20px)';
    
    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = text;
    
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Animate message in
    setTimeout(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
        messageDiv.style.transition = 'all 0.3s ease-out';
    }, 50);
    
    // Scroll to bottom
    setTimeout(() => {
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
    }, 100);
}

// Show enhanced typing indicator
function showTypingIndicator() {
    // Remove existing typing indicator if any
    const existingIndicator = document.querySelector('.typing-indicator');
    if (existingIndicator) {
        existingIndicator.remove();
    }
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator active';
    indicator.innerHTML = 'Thinking<span class="typing-dots"></span>';
    
    // Add animated dots
    const dots = document.createElement('div');
    dots.className = 'typing-dots';
    dots.innerHTML = '<span>.</span><span>.</span><span>.</span>';
    indicator.appendChild(dots);
    
    chatMessages.appendChild(indicator);
    
    // Scroll to bottom
    chatMessages.scrollTo({
        top: chatMessages.scrollHeight,
        behavior: 'smooth'
    });
    
    return indicator;
}

// Hide Typing Indicator
function hideTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.style.opacity = '0';
        indicator.style.transform = 'translateY(10px)';
        indicator.style.transition = 'all 0.3s ease-out';
        
        setTimeout(() => {
            if (indicator.parentNode) {
                indicator.remove();
            }
        }, 300);
    }
}

// Enhanced sample question handler
function handleSampleQuestion(question, btn) {
    // Add visual feedback to the clicked button
    const originalText = btn.innerHTML;
    btn.innerHTML = 'Asking...';
    btn.style.opacity = '0.7';
    btn.disabled = true;
    
    // Add user message
    addMessage(question, true);
    
    // Show typing indicator
    const typingIndicator = showTypingIndicator();
    
    // Simulate AI response (to be replaced with real API)
    setTimeout(() => {
        hideTypingIndicator(typingIndicator);
        
        // Restore button
        btn.innerHTML = originalText;
        btn.style.opacity = '1';
        btn.disabled = false;
        
        // Enhanced simulated responses
        const responses = [
            "I'd be happy to tell you about that! I'm currently being trained on Abhijith's portfolio data. Soon I'll provide detailed, accurate answers about his skills and projects.",
            "Excellent question! The AI is learning from Abhijith's work in mathematics and data science. Check back soon for comprehensive answers.",
            "I'm analyzing Abhijith's portfolio data to give you the best possible answer. The system is almost ready to provide detailed insights!",
            "That's a great question about Abhijith's expertise. I'm currently processing his project information to give you the most accurate response possible."
        ];
        
        const randomResponse = responses[Math.floor(Math.random() * responses.length)];
        addMessage(randomResponse);
    }, 1800 + Math.random() * 1200); // Random delay between 1.8-3 seconds
}

// Enhanced message sending
function handleSendMessage(message) {
    if (!message.trim()) return;
    
    // Add user message
    addMessage(message, true);
    
    // Clear input with animation
    chatInput.style.opacity = '0.5';
    setTimeout(() => {
        chatInput.value = '';
        chatInput.style.opacity = '1';
    }, 300);
    
    // Show typing indicator
    const typingIndicator = showTypingIndicator();
    
    // Simulate AI response
    setTimeout(() => {
        hideTypingIndicator(typingIndicator);
        
        // Enhanced response based on message content
        let response;
        if (message.toLowerCase().includes('skill') || message.toLowerCase().includes('technology')) {
            response = "I see you're asking about technical skills. Abhijith has expertise in Python, R, machine learning, statistical analysis, and data visualization. Would you like me to elaborate on any specific area?";
        } else if (message.toLowerCase().includes('project') || message.toLowerCase().includes('work')) {
            response = "You're interested in projects! Abhijith has worked on machine learning implementations, statistical analyses, and optimization problems. Which type of project are you most curious about?";
        } else if (message.toLowerCase().includes('research') || message.toLowerCase().includes('paper')) {
            response = "Research inquiries! Abhijith has published papers on stochastic optimization, topological data analysis, and graph neural networks. Would you like details on a specific research area?";
        } else {
            response = "Thank you for your question! I'm still learning about Abhijith's complete portfolio, but I can tell you about his skills, projects, or research. Feel free to ask about any of these areas!";
        }
        
        addMessage(response);
    }, 2000 + Math.random() * 1000);
}

// Initialize Chat Event Listeners
function initChatSection() {
    // Sample question buttons
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
    
    // Send message on Enter key
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const message = chatInput.value.trim();
                if (message) {
                    handleSendMessage(message);
                }
            }
        });
    }
}

// Initialize animations when the page loads
window.addEventListener('load', function() {
    initMathBackground();
    initGraphs();
    initCounter();
    
    // Initialize chat section
    initChatSection();
    
    // Animate skill bars
    const skillBars = document.querySelectorAll('.skill-progress');
    skillBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        bar.style.width = width;
    });
    
    // Animate elements on scroll
    const animatedElements = document.querySelectorAll('.project-card, .research-item, .stat');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
            }
        });
    }, { threshold: 0.1 });
    
    animatedElements.forEach(el => observer.observe(el));
});

// Add CSS for typing dots animation
const style = document.createElement('style');
style.textContent = `
    .typing-dots {
        display: inline-block;
        margin-left: 5px;
    }
    
    .typing-dots span {
        animation: typingDots 1.4s infinite ease-in-out;
        opacity: 0;
        display: inline-block;
    }
    
    .typing-dots span:nth-child(1) { animation-delay: 0s; }
    .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
    .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typingDots {
        0% { opacity: 0; transform: translateY(0px); }
        50% { opacity: 1; transform: translateY(-2px); }
        100% { opacity: 0; transform: translateY(0px); }
    }
`;
document.head.appendChild(style);