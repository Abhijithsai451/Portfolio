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
        // This would be replaced with actual chart library in a real implementation
        heroGraph.innerHTML = '<div class="graph-placeholder">Data Visualization</div>';
    }
    
    // Project graphs
    for (let i = 1; i <= 6; i++) {
        const projectGraph = document.getElementById(`project-graph-${i}`);
        if (projectGraph) {
            // This would be replaced with actual chart library in a real implementation
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

// Initialize animations when the page loads
window.addEventListener('load', function() {
    initMathBackground();
    initGraphs();
    initCounter();
    
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