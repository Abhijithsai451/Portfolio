// Form submission handling
document.getElementById('contactForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = this.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    // Get form data
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        subject: document.getElementById('subject').value,
        message: document.getElementById('message').value
    };
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    submitBtn.disabled = true;
    
    try {
        // In a real implementation, you would send this to your backend
        // For now, we'll simulate an API call
        console.log('Form data:', formData);
        
        // Simulate API request delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Show success message
        showToast('Your message has been sent successfully!');
        
        // Reset form
        this.reset();
        
    } catch (error) {
        console.error('Error sending message:', error);
        showToast('There was an error sending your message. Please try again.', 'error');
    } finally {
        // Restore button
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
});

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    
    if (type === 'error') {
        toast.style.background = 'rgba(244, 67, 54, 0.9)';
    } else {
        toast.style.background = 'rgba(0, 201, 255, 0.9)';
    }
    
    toast.classList.add('visible');
    
    setTimeout(() => {
        toast.classList.remove('visible');
    }, 3000);
}

// In a real implementation, you would connect this to your backend
// Example using fetch:

async function sendEmail(formData) {
    const response = await fetch('/api/send-email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });
    
    if (!response.ok) {
        throw new Error('Failed to send email');
    }
    
    return response.json();
}
