// Enforcer Modal Validation Script
// This script provides real-time validation for the Add Enforcer modal

document.addEventListener('DOMContentLoaded', function() {
    const addEnforcerForm = document.querySelector('#addEnforcerModal form');
    const usernameInput = document.getElementById('username');
    const mobileInput = document.getElementById('mobile_number');
    
    // Username validation
    let usernameTimeout;
    if (usernameInput) {
        usernameInput.addEventListener('input', function() {
            clearTimeout(usernameTimeout);
            const username = this.value.trim();
            
            // Remove previous validation messages
            const existingFeedback = this.parentElement.querySelector('.username-feedback');
            if (existingFeedback) {
                existingFeedback.remove();
            }
            
            if (username.length >= 3) {
                usernameTimeout = setTimeout(() => {
                    // Check username availability via AJAX
                    fetch(`/api/check-username/?username=${encodeURIComponent(username)}`)
                        .then(response => response.json())
                        .then(data => {
                            const feedback = document.createElement('small');
                            feedback.className = 'username-feedback d-block mt-1';
                            
                            if (data.exists) {
                                feedback.className += ' text-danger';
                                feedback.innerHTML = '<i class="fas fa-times-circle"></i> Username already exists';
                                usernameInput.classList.add('is-invalid');
                                usernameInput.classList.remove('is-valid');
                            } else {
                                feedback.className += ' text-success';
                                feedback.innerHTML = '<i class="fas fa-check-circle"></i> Username available';
                                usernameInput.classList.add('is-valid');
                                usernameInput.classList.remove('is-invalid');
                            }
                            
                            usernameInput.parentElement.appendChild(feedback);
                        })
                        .catch(error => {
                            console.error('Error checking username:', error);
                        });
                }, 500); // Wait 500ms after user stops typing
            }
        });
    }
    
    // Mobile number validation (exactly 11 digits)
    if (mobileInput) {
        mobileInput.addEventListener('input', function() {
            // Remove non-digit characters
            this.value = this.value.replace(/\D/g, '');
            
            // Limit to 11 digits
            if (this.value.length > 11) {
                this.value = this.value.slice(0, 11);
            }
            
            // Remove previous validation messages
            const existingFeedback = this.parentElement.querySelector('.mobile-feedback');
            if (existingFeedback) {
                existingFeedback.remove();
            }
            
            const feedback = document.createElement('small');
            feedback.className = 'mobile-feedback d-block mt-1';
            
            if (this.value.length === 0) {
                this.classList.remove('is-valid', 'is-invalid');
            } else if (this.value.length === 11) {
                feedback.className += ' text-success';
                feedback.innerHTML = '<i class="fas fa-check-circle"></i> Valid mobile number';
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
                this.parentElement.appendChild(feedback);
            } else {
                feedback.className += ' text-danger';
                feedback.innerHTML = `<i class="fas fa-times-circle"></i> Must be exactly 11 digits (${this.value.length}/11)`;
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
                this.parentElement.appendChild(feedback);
            }
        });
    }
    
    // Form submission validation
    if (addEnforcerForm) {
        addEnforcerForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Check username
            if (usernameInput && usernameInput.classList.contains('is-invalid')) {
                e.preventDefault();
                alert('Please choose a different username. The current username already exists.');
                isValid = false;
            }
            
            // Check mobile number
            if (mobileInput) {
                const mobile = mobileInput.value.trim();
                if (mobile.length !== 11 || !/^\d{11}$/.test(mobile)) {
                    e.preventDefault();
                    alert('Mobile number must be exactly 11 digits.');
                    mobileInput.focus();
                    isValid = false;
                }
            }
            
            return isValid;
        });
    }
});
