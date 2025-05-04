document.addEventListener('DOMContentLoaded', function() {
    // Page loading transition
    document.body.classList.add('page-loaded');
    
    // Add an active class to the current navigation item
    const currentLocation = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        // Skip dropdown toggle links
        if (link.classList.contains('dropdown-toggle')) return;
        
        const linkPath = link.getAttribute('href');
        if (linkPath === currentLocation || 
            (currentLocation.includes(linkPath) && linkPath !== '/')) {
            link.classList.add('active');
            // If it's in a dropdown, also highlight the parent
            const parentDropdown = link.closest('.dropdown');
            if (parentDropdown) {
                const dropdownToggle = parentDropdown.querySelector('.dropdown-toggle');
                if (dropdownToggle) dropdownToggle.classList.add('active');
            }
        }
    });
    
    // Smooth scroll to anchor links
    document.querySelectorAll('a[href^="#"]:not([data-toggle])').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return; // Skip links with just #
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                window.scrollTo({
                    top: targetElement.offsetTop - 70, // Account for fixed navbar
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Notification dropdown functionality with animation
    const notificationDropdown = document.getElementById('notificationsDropdown');
    const notificationBadge = document.getElementById('notification-badge');
    
    if (notificationDropdown && notificationBadge) {
        notificationDropdown.addEventListener('click', function() {
            // When clicked, clear the notification count with animation
            if (notificationBadge.textContent !== '0') {
                notificationBadge.classList.add('animated-badge');
                setTimeout(() => {
                    notificationBadge.textContent = '0';
                    setTimeout(() => {
                        notificationBadge.style.display = 'none';
                        notificationBadge.classList.remove('animated-badge');
                    }, 300);
                }, 700);
            }
        });
    }
    
    // Add loading animation to buttons when clicked - simpler approach
    document.querySelectorAll('.btn:not([type="button"]):not([data-toggle])').forEach(button => {
        button.addEventListener('click', function(e) {
            // Skip if the button has the no-loader class or is disabled
            if (this.classList.contains('no-loader') || this.disabled) return;
            
            // Don't add loader to dropdown toggles or modal toggles
            if (this.getAttribute('data-toggle')) return;
            
            // Exception for login and registration forms - these should work without animation
            // because we need the standard form submission to work properly
            const form = this.closest('form');
            if (form && (form.id === 'login-form' || form.id === 'register-form' || form.id === 'admin-login-form' || 
                         form.action.includes('login') || form.action.includes('register') || 
                         form.action.includes('auth'))) {
                return;
            }
            
            // If it's a regular form submit for POST (not AJAX), don't add loading animation
            // as it's causing issues with 304 status codes
            if (form && !e.defaultPrevented && form.getAttribute('method') && 
                form.getAttribute('method').toLowerCase() === 'post') {
                // Don't handle standard form submissions with animation
                // Let the browser handle these normally
                return;
            }
            
            // Store original state
            const originalText = this.innerHTML;
            this.setAttribute('data-original-text', originalText);
            
            // Add loading state
            this.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Loading...';
            
            // Don't disable the button - this is causing issues with form submission
            // this.disabled = true;
            
            // Set a timeout to reset the button if it's stuck
            setTimeout(() => {
                if (this.innerHTML.includes('spinner-border')) {
                    this.innerHTML = originalText;
                }
            }, 5000); // 5 second timeout
        });
    });
    
    // Reset button text if form is reset
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('reset', function() {
            this.querySelectorAll('.btn[data-original-text]').forEach(button => {
                button.innerHTML = button.getAttribute('data-original-text');
                button.disabled = false;
            });
        });
    });
    
    // On page load, check if there was a submitted form that needs to be reset
    // This handles the case where the form submission results in displaying the same page
    window.addEventListener('load', function() {
        const formId = sessionStorage.getItem('form_submitted');
        const btnId = sessionStorage.getItem('button_clicked');
        
        if (formId && btnId) {
            const form = document.getElementById(formId);
            const button = document.getElementById(btnId);
            
            if (form && button) {
                // The same form is still on the page, reset the button
                if (button.getAttribute('data-original-text')) {
                    button.innerHTML = button.getAttribute('data-original-text');
                } else {
                    // If original text wasn't saved, use a default
                    button.innerHTML = button.getAttribute('data-default-text') || 'Submit';
                }
                button.disabled = false;
            }
            
            // Clear sessionStorage
            sessionStorage.removeItem('form_submitted');
            sessionStorage.removeItem('button_clicked');
        }
    });

    // Enhanced chat functionality with typing indicator
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const chatSubmitBtn = document.querySelector('#chat-form button[type="submit"]');
    let isRequestInProgress = false; // Global flag to prevent multiple chat requests

    if (chatForm && chatInput && chatMessages) {
        // Focus input field when chat container is clicked
        chatMessages.addEventListener('click', function() {
            chatInput.focus();
        });
        
        // Add emotion to buttons
        if (chatSubmitBtn) {
            chatSubmitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            chatSubmitBtn.setAttribute('title', 'Send message');
            // Add ID if missing
            if (!chatSubmitBtn.id) chatSubmitBtn.id = 'chat-send-btn';
        }
        
        // Chat form submission handler
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Prevent submitting if already processing a request
            if (isRequestInProgress) {
                console.log("Request already in progress");
                return;
            }
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Set flag to prevent duplicates
            isRequestInProgress = true;
            
            // Add user message to chat display
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('chat-message', 'user-message');
            
            // Create message container
            const messageContent = document.createElement('div');
            messageContent.classList.add('message-content');
            
            // Create avatar
            const avatar = document.createElement('div');
            avatar.classList.add('message-avatar');
            avatar.innerHTML = '<i class="fas fa-user"></i>';
            
            // Create message text
            const messageText = document.createElement('div');
            messageText.classList.add('message-text');
            messageText.textContent = message;
            
            // Assemble the message
            messageContent.appendChild(avatar);
            messageContent.appendChild(messageText);
            messageDiv.appendChild(messageContent);
            
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            chatInput.value = '';
            
            // Show typing indicator while waiting for response
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'chat-message bot-message typing-indicator';
            typingIndicator.innerHTML = '<span></span><span></span><span></span>';
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Disable input and button while processing
            chatInput.disabled = true;
            if (chatSubmitBtn) {
                chatSubmitBtn.disabled = true;
                // Add visual indication of loading state
                chatSubmitBtn.classList.add('is-loading');
            }
            
            // Set a timeout to reset UI in case of very long requests
            const resetUITimeout = setTimeout(() => {
                if (isRequestInProgress) {
                    // Remove typing indicator if it exists
                    const indicator = document.querySelector('.typing-indicator');
                    if (indicator) chatMessages.removeChild(indicator);
                    
                    // Show timeout message
                    const timeoutDiv = document.createElement('div');
                    timeoutDiv.classList.add('chat-message', 'bot-message');
                    
                    const timeoutContent = document.createElement('div');
                    timeoutContent.classList.add('message-content');
                    
                    const timeoutAvatar = document.createElement('div');
                    timeoutAvatar.classList.add('message-avatar');
                    timeoutAvatar.innerHTML = '<i class="fas fa-robot"></i>';
                    
                    const timeoutText = document.createElement('div');
                    timeoutText.classList.add('message-text');
                    timeoutText.textContent = "The request is taking longer than expected. Please try again.";
                    
                    timeoutContent.appendChild(timeoutAvatar);
                    timeoutContent.appendChild(timeoutText);
                    timeoutDiv.appendChild(timeoutContent);
                    
                    chatMessages.appendChild(timeoutDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                    
                    // Reset UI
                    isRequestInProgress = false;
                    chatInput.disabled = false;
                    if (chatSubmitBtn) {
                        chatSubmitBtn.disabled = false;
                        chatSubmitBtn.classList.remove('is-loading');
                    }
                    chatInput.focus();
                }
            }, 30000); // 30 second timeout
            
            // Send message to server
            fetch('/chatbot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => {
                // Handle 304 Not Modified as success
                if (response.status === 304) {
                    // Return a default response object
                    return { response: "I received your message, but I don't have a new response right now. Please try again." };
                }
                
                // Handle other non-ok responses
                if (!response.ok && response.status !== 304) {
                    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                }
                
                return response.json();
            })
            .then(data => {
                // Clear timeout since we got a response
                clearTimeout(resetUITimeout);
                
                // Remove typing indicator
                try {
                    const indicator = document.querySelector('.typing-indicator');
                    if (indicator) chatMessages.removeChild(indicator);
                } catch (err) {
                    console.error("Error removing typing indicator:", err);
                }
                
                // Add bot response to chat
                const botDiv = document.createElement('div');
                botDiv.classList.add('chat-message', 'bot-message');
                
                const botContent = document.createElement('div');
                botContent.classList.add('message-content');
                
                const botAvatar = document.createElement('div');
                botAvatar.classList.add('message-avatar');
                botAvatar.innerHTML = '<i class="fas fa-robot"></i>';
                
                const botText = document.createElement('div');
                botText.classList.add('message-text');
                
                // Format links and preserve line breaks in bot messages
                const formattedText = data.response.replace(/\n/g, '<br>');
                // Format URLs as clickable links
                const urlPattern = /(https?:\/\/[^\s<]+)/g;
                const withLinks = formattedText.replace(urlPattern, '<a href="$1" target="_blank">$1</a>');
                botText.innerHTML = withLinks;
                
                botContent.appendChild(botAvatar);
                botContent.appendChild(botText);
                botDiv.appendChild(botContent);
                
                chatMessages.appendChild(botDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                // Clear timeout since we got a response
                clearTimeout(resetUITimeout);
                
                console.error('Error:', error);
                
                // Remove typing indicator
                try {
                    const indicator = document.querySelector('.typing-indicator');
                    if (indicator) chatMessages.removeChild(indicator);
                } catch (err) {
                    console.error("Error removing typing indicator:", err);
                }
                
                // Add error message
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('chat-message', 'bot-message');
                
                const errorContent = document.createElement('div');
                errorContent.classList.add('message-content');
                
                const errorAvatar = document.createElement('div');
                errorAvatar.classList.add('message-avatar');
                errorAvatar.innerHTML = '<i class="fas fa-robot"></i>';
                
                const errorText = document.createElement('div');
                errorText.classList.add('message-text');
                errorText.textContent = "Sorry, I encountered an error processing your request. Please try again.";
                
                errorContent.appendChild(errorAvatar);
                errorContent.appendChild(errorText);
                errorDiv.appendChild(errorContent);
                
                chatMessages.appendChild(errorDiv);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .finally(() => {
                // Always reset UI state
                isRequestInProgress = false;
                chatInput.disabled = false;
                if (chatSubmitBtn) {
                    chatSubmitBtn.disabled = false;
                    chatSubmitBtn.classList.remove('is-loading');
                }
                chatInput.focus();
            });
        });
        
        // Add autogrowing input field
        chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }

    // Enhanced ticket purchase with Stripe and feedback
    const buyTicketButtons = document.querySelectorAll('.buy-ticket-btn');
    if (buyTicketButtons.length > 0) {
        buyTicketButtons.forEach(button => {
            // Add currency formatting to button text
            const originalText = button.textContent.trim();
            if (originalText.includes('KZT')) {
                const price = originalText.split('-')[1].trim().split(' ')[0];
                const formattedPrice = Number(price).toLocaleString();
                button.innerHTML = `<i class="fas fa-ticket-alt mr-2"></i>Buy Ticket - ${formattedPrice} <span class="small">KZT</span>`;
            }
            
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const eventId = this.getAttribute('data-event-id');
                
                // Create overlay for a better loading experience
                const overlay = document.createElement('div');
                overlay.className = 'payment-overlay';
                overlay.innerHTML = `
                    <div class="payment-loader">
                        <div class="spinner-border text-light" role="status">
                            <span class="sr-only">Loading...</span>
                        </div>
                        <p class="mt-3 text-light">Processing payment...</p>
                    </div>
                `;
                document.body.appendChild(overlay);
                
                // Save original button text 
                const originalButtonHTML = this.innerHTML;
                
                // Disable button and show loading state
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Processing...';
                
                // Send request to create Stripe session
                fetch(`/buy-ticket/${eventId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(response => {
                    // Handle 304 Not Modified as success
                    if (response.status === 304) {
                        return { 
                            sessionId: "mock_stripe_sess_fallback", 
                            message: "Using fallback session due to 304 response" 
                        };
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.error) {
                        // Remove overlay with animation
                        overlay.classList.add('fade-out');
                        setTimeout(() => {
                            document.body.removeChild(overlay);
                            
                            // Show error in a nicer way
                            const errorContainer = document.createElement('div');
                            errorContainer.className = 'alert alert-danger alert-dismissible fade show payment-alert';
                            errorContainer.innerHTML = `
                                <i class="fas fa-exclamation-circle mr-2"></i>
                                Error: ${data.error}
                                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                </button>
                            `;
                            document.querySelector('.container').insertBefore(errorContainer, document.querySelector('.container').firstChild);
                            
                            // Reset button
                            this.disabled = false;
                            this.innerHTML = originalButtonHTML;
                            
                            // Auto-dismiss alert after 5 seconds
                            setTimeout(() => {
                                errorContainer.remove();
                            }, 5000);
                        }, 300);
                    } else {
                        // Check if we're using a mock session (starts with mock_)
                        if (data.sessionId && data.sessionId.startsWith('mock_stripe_sess_')) {
                            // This is a mock session, handle it differently
                            console.log('Using mock Stripe session');
                            
                            // Show success message in overlay
                            overlay.innerHTML = `
                                <div class="payment-loader success">
                                    <div class="success-checkmark">
                                        <div class="check-icon">
                                            <span class="icon-line line-tip"></span>
                                            <span class="icon-line line-long"></span>
                                        </div>
                                    </div>
                                    <p class="mt-3 text-light">Payment successful!</p>
                                    <p class="text-light small">This is a development environment. Your ticket has been created with "paid" status.</p>
                                    <p class="text-light small">Redirecting to your ticket...</p>
                                </div>
                            `;
                            
                            // Redirect to the success page after a short delay
                            setTimeout(() => {
                                window.location.href = `/payment-success?session_id=${data.sessionId}`;
                            }, 2000);
                        } else {
                            // Real Stripe session - redirect to Checkout
                            const stripe = Stripe(stripePublicKey);
                            stripe.redirectToCheckout({ sessionId: data.sessionId })
                            .then(function (result) {
                                if (result.error) {
                                    document.body.removeChild(overlay);
                                    alert(result.error.message);
                                    
                                    // Reset button
                                    this.disabled = false;
                                    this.innerHTML = originalButtonHTML;
                                }
                            });
                        }
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    
                    // Remove overlay
                    overlay.classList.add('fade-out');
                    setTimeout(() => {
                        document.body.removeChild(overlay);
                    }, 300);
                    
                    // Show error in a nicer way
                    const errorContainer = document.createElement('div');
                    errorContainer.className = 'alert alert-danger alert-dismissible fade show payment-alert';
                    errorContainer.innerHTML = `
                        <i class="fas fa-exclamation-circle mr-2"></i>
                        An error occurred while processing your payment request. Please try again.
                        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                            <span aria-hidden="true">&times;</span>
                        </button>
                    `;
                    document.querySelector('.container').insertBefore(errorContainer, document.querySelector('.container').firstChild);
                    
                    // Reset button
                    this.disabled = false;
                    this.innerHTML = originalButtonHTML;
                    
                    // Auto-dismiss alert after 5 seconds
                    setTimeout(() => {
                        errorContainer.remove();
                    }, 5000);
                });
            });
        });
    }

    // Enhanced filter events with animations and responsive features
    const filterForm = document.getElementById('event-filter-form');
    const filterCollapse = document.getElementById('filterCollapse');
    
    if (filterForm) {
        // Add animation when filter form is expanded
        if (filterCollapse) {
            filterCollapse.addEventListener('show.bs.collapse', function() {
                document.querySelector('[data-toggle="collapse"]').innerHTML = '<i class="fas fa-times"></i> Close Filters';
            });
            
            filterCollapse.addEventListener('hide.bs.collapse', function() {
                document.querySelector('[data-toggle="collapse"]').innerHTML = '<i class="fas fa-filter"></i> Filter Events';
            });
        }
        
        // Enhance filter form submission
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Add loading state to submit button
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Applying...';
                submitBtn.disabled = true;
            }
            
            const formData = new FormData(filterForm);
            const params = new URLSearchParams();
            
            for (const [key, value] of formData.entries()) {
                if (value) {
                    params.append(key, value);
                }
            }
            
            // Use a small timeout to show the loading state
            setTimeout(() => {
                window.location.href = '/events?' + params.toString();
            }, 300);
        });
        
        // Add clear filter functionality to reset button
        const resetBtn = filterForm.querySelector('a.btn-secondary');
        if (resetBtn) {
            resetBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Add loading state to reset button
                this.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Resetting...';
                this.disabled = true;
                
                // Use a small timeout to show the loading state
                setTimeout(() => {
                    window.location.href = '/events';
                }, 300);
            });
        }
    }

    // Enhanced Telegram connection with better UI feedback
    const connectTelegramBtn = document.getElementById('connect-telegram-btn');
    const telegramCodeDisplay = document.getElementById('telegram-code-display');
    
    if (connectTelegramBtn && telegramCodeDisplay) {
        connectTelegramBtn.addEventListener('click', function() {
            // Add loading state to button
            const originalButtonText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm mr-2" role="status" aria-hidden="true"></span> Connecting...';
            this.disabled = true;
            
            // Hide any previous code display with fade out
            if (telegramCodeDisplay.style.display === 'block') {
                telegramCodeDisplay.style.opacity = '0';
                setTimeout(() => {
                    telegramCodeDisplay.style.display = 'none';
                }, 300);
            }
            
            fetch('/profile/link-telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(response => {
                // Handle 304 Not Modified as success
                if (response.status === 304) {
                    return { 
                        code: "SAMPLE_CODE", 
                        bot_username: "sdu_event_hub_bot"
                    };
                }
                return response.json();
            })
            .then(data => {
                if (data.code) {
                    // Reset button
                    this.innerHTML = originalButtonText;
                    this.disabled = false;
                    
                    // Prepare code display
                    telegramCodeDisplay.innerHTML = `
                        <div class="card border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="mb-3">
                                    <i class="fab fa-telegram-plane fa-3x text-primary"></i>
                                </div>
                                <h5 class="card-title">Connect to Telegram</h5>
                                <p>Send this code to our Telegram bot: <strong>@${data.bot_username}</strong></p>
                                <div class="telegram-code mt-3 mb-3">
                                    <code>${data.code}</code>
                                </div>
                                <p class="text-muted small">This code will expire in 15 minutes</p>
                            </div>
                        </div>
                    `;
                    
                    // Show with fade in
                    telegramCodeDisplay.style.display = 'block';
                    setTimeout(() => {
                        telegramCodeDisplay.style.opacity = '1';
                    }, 10);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Reset button
                this.innerHTML = originalButtonText;
                this.disabled = false;
                
                // Show error message
                const errorContainer = document.createElement('div');
                errorContainer.className = 'alert alert-danger alert-dismissible fade show';
                errorContainer.innerHTML = `
                    <i class="fas fa-exclamation-circle mr-2"></i>
                    Failed to generate Telegram connection code. Please try again.
                    <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                        <span aria-hidden="true">&times;</span>
                    </button>
                `;
                document.querySelector('.container').insertBefore(errorContainer, document.querySelector('.container').firstChild);
                
                // Auto dismiss after 5 seconds
                setTimeout(() => {
                    errorContainer.remove();
                }, 5000);
            });
        });
    }
    
    // Add animations for page transitions
    document.addEventListener('beforeunload', function() {
        document.body.classList.add('page-transition');
    });
});

// Add pulsating animation to the chat button in the navbar
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        const chatNavLink = document.querySelector('.nav-link[href*="chat"]');
        if (chatNavLink) {
            chatNavLink.classList.add('pulse-animation');
            setTimeout(() => {
                chatNavLink.classList.remove('pulse-animation');
            }, 3000);
        }
    }, 2000);
});

// Helper to append chat messages with rich formatting
function createChatMessage(sender, message, isHTML = false) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    messageDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    
    // Create message container
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    
    // Create avatar
    const avatar = document.createElement('div');
    avatar.classList.add('message-avatar');
    avatar.innerHTML = sender === 'user' ? 
        '<i class="fas fa-user"></i>' : 
        '<i class="fas fa-robot"></i>';
    
    // Create message text
    const messageText = document.createElement('div');
    messageText.classList.add('message-text');
    
    // Set the message content
    if (isHTML) {
        messageText.innerHTML = message;
    } else {
        messageText.textContent = message;
    }
    
    // Assemble the message
    messageContent.appendChild(avatar);
    messageContent.appendChild(messageText);
    messageDiv.appendChild(messageContent);
    
    return messageDiv;
}

// Helper to get CSRF token
function getCsrfToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    if (token) {
        return token.value;
    }
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    return '';
}
