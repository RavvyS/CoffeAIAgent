// Coffee Shop AI Chat Client
class CoffeeShopChat {
    constructor() {
        this.ws = null;
        this.sessionId = this.generateSessionId();
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        
        // DOM elements
        this.elements = {
            messages: document.getElementById('chatMessages'),
            input: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendButton'),
            statusDot: document.getElementById('connectionStatus'),
            statusText: document.getElementById('statusText'),
            suggestions: document.getElementById('suggestions'),
            suggestionsContainer: document.getElementById('suggestionsContainer'),
            typingIndicator: document.getElementById('typingIndicator'),
            charCount: document.getElementById('charCount'),
            orderSidebar: document.getElementById('orderSidebar'),
            orderCount: document.getElementById('orderCount'),
            // Quick action buttons
            menuBtn: document.getElementById('menuBtn'),
            orderBtn: document.getElementById('orderBtn'),
            helpBtn: document.getElementById('helpBtn'),
            closeSidebar: document.getElementById('closeSidebar')
        };
        
this.currentOrder = { items: [], total: 0.0 };
        this.messageQueue = [];
        this.emotionalSupport = null;
        this.queueStatus = null;
        this.tableInfo = null;
        
        // Check for table/QR parameters
        this.checkTableContext();
        
        this.initializeEventListeners();
        this.connect();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    initializeEventListeners() {
        // Send message on button click
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.elements.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Character counter
        this.elements.input.addEventListener('input', () => {
            const length = this.elements.input.value.length;
            this.elements.charCount.textContent = length;
            
            // Enable/disable send button
            this.elements.sendBtn.disabled = length === 0 || !this.isConnected;
        });
        
// Quick action buttons
        this.elements.menuBtn.addEventListener('click', () => this.showMenu());
        this.elements.orderBtn.addEventListener('click', () => this.toggleOrderSidebar());
        this.elements.helpBtn.addEventListener('click', () => this.showHelp());
        this.elements.closeSidebar.addEventListener('click', () => this.closeOrderSidebar());
        
        // Add new quick action buttons
        const queueBtn = document.getElementById('queueBtn');
        const appointmentBtn = document.getElementById('appointmentBtn');
        const supportBtn = document.getElementById('supportBtn');
        
        if (queueBtn) queueBtn.addEventListener('click', () => this.joinQueue());
        if (appointmentBtn) appointmentBtn.addEventListener('click', () => this.scheduleAppointment());
        if (supportBtn) supportBtn.addEventListener('click', () => this.requestEmotionalSupport());
        
        // Handle window beforeunload
        window.addEventListener('beforeunload', () => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.close();
            }
        });
        
        // Auto-focus input when page loads
        window.addEventListener('load', () => {
            this.elements.input.focus();
        });
    }
    
    connect() {
        try {
            // Determine WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/${this.sessionId}`;
            
            console.log('Connecting to:', wsUrl);
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => this.handleConnection();
            this.ws.onmessage = (event) => this.handleMessage(event);
            this.ws.onclose = (event) => this.handleDisconnection(event);
            this.ws.onerror = (error) => this.handleError(error);
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.updateConnectionStatus('disconnected', 'Connection failed');
            this.scheduleReconnect();
        }
    }
    
    handleConnection() {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.updateConnectionStatus('connected', 'Connected');
        
        // Enable input
        this.elements.input.disabled = false;
        this.elements.input.placeholder = 'Type your message here...';
        this.elements.input.focus();
        
        // Process queued messages
        this.processMessageQueue();
    }
    
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received:', data);
            
  switch (data.type) {
                case 'system':
                case 'assistant':
                    this.hideTypingIndicator();
                    this.addMessage('assistant', data.message, data.timestamp);
                    
                    // Handle emotional support data
                    if (data.emotional_support) {
                        this.showEmotionalSupport(data.emotional_support);
                    }
                    
                    // Update context if provided
                    if (data.context) {
                        this.updateContext(data.context);
                    }
                    
                    // Show suggestions if provided
                    if (data.suggestions && data.suggestions.length > 0) {
                        this.showSuggestions(data.suggestions);
                    }
                    break;
                    
                case 'typing':
                    if (data.typing) {
                        this.showTypingIndicator();
                    } else {
                        this.hideTypingIndicator();
                    }
                    break;
                    
                case 'pong':
                    // Handle ping/pong for keepalive
                    console.log('Received pong');
                    break;
                    
                case 'session_expired':
                    this.addMessage('system', data.message, data.timestamp);
                    this.updateConnectionStatus('disconnected', 'Session expired');
                    break;
                    
                default:
                    console.log('Unknown message type:', data.type);
            }
            
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    }
    
    handleDisconnection(event) {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected = false;
        this.elements.input.disabled = true;
        this.elements.sendBtn.disabled = true;
        
        if (event.code !== 1000) { // Not a normal closure
            this.updateConnectionStatus('disconnected', 'Connection lost');
            this.scheduleReconnect();
        } else {
            this.updateConnectionStatus('disconnected', 'Disconnected');
        }
    }
    
    handleError(error) {
        console.error('WebSocket error:', error);
        this.updateConnectionStatus('disconnected', 'Connection error');
    }
    
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
            
            this.updateConnectionStatus('connecting', `Reconnecting in ${delay/1000}s... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                this.updateConnectionStatus('connecting', 'Reconnecting...');
                this.connect();
            }, delay);
        } else {
            this.updateConnectionStatus('disconnected', 'Connection failed. Please refresh.');
            this.addMessage('system', 'Connection lost. Please refresh the page to continue.', new Date().toISOString());
        }
    }
    
    updateConnectionStatus(status, text) {
        this.elements.statusDot.className = `status-dot ${status}`;
        this.elements.statusText.textContent = text;
    }
    
    sendMessage() {
        const message = this.elements.input.value.trim();
        if (!message || !this.isConnected) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        
        // Clear input
        this.elements.input.value = '';
        this.elements.charCount.textContent = '0';
        this.elements.sendBtn.disabled = true;
        
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send via WebSocket
        const messageData = {
            type: 'message',
            message: message,
            timestamp: new Date().toISOString(),
            context: {
                // Add any client-side context here
                user_agent: navigator.userAgent,
                screen_size: `${window.innerWidth}x${window.innerHeight}`
            }
        };
        
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(messageData));
        } else {
            // Queue message if not connected
            this.messageQueue.push(messageData);
            this.addMessage('system', 'Message queued. Attempting to reconnect...', new Date().toISOString());
        }
        
        // Hide suggestions after user sends message
        this.hideSuggestions();
    }
    
    addMessage(sender, content, timestamp = null) {
        const messageContainer = document.createElement('div');
        messageContainer.className = `message message-${sender}`;
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'message-bubble';
        messageBubble.innerHTML = this.formatMessageContent(content);
        
        const messageTimestamp = document.createElement('div');
        messageTimestamp.className = 'message-timestamp';
        messageTimestamp.textContent = this.formatTimestamp(timestamp || new Date().toISOString());
        
        messageBubble.appendChild(messageTimestamp);
        messageContainer.appendChild(messageBubble);
        
        // Remove welcome message if it exists
        const welcomeMessage = this.elements.messages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        this.elements.messages.appendChild(messageContainer);
        this.scrollToBottom();
    }
    
    formatMessageContent(content) {
        // Basic formatting for message content
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    }
    
    formatTimestamp(isoString) {
        const date = new Date(isoString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    showSuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }
        
        this.elements.suggestions.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('div');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.addEventListener('click', () => {
                this.elements.input.value = suggestion;
                this.elements.input.focus();
                this.hideSuggestions();
                // Optionally auto-send the suggestion
                // this.sendMessage();
            });
            this.elements.suggestions.appendChild(chip);
        });
        
        this.elements.suggestionsContainer.style.display = 'block';
    }
    
    hideSuggestions() {
        this.elements.suggestionsContainer.style.display = 'none';
    }
    
    showTypingIndicator() {
        this.elements.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.elements.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }
    
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.ws.readyState === WebSocket.OPEN) {
            const message = this.messageQueue.shift();
            this.ws.send(JSON.stringify(message));
        }
    }
    
    updateContext(context) {
        // Update current order if provided
        if (context.current_order) {
            this.currentOrder = context.current_order;
            this.updateOrderDisplay();
        }
    }
    
    updateOrderDisplay() {
        const itemCount = this.currentOrder.items.length;
        
        if (itemCount > 0) {
            this.elements.orderCount.textContent = itemCount;
            this.elements.orderCount.style.display = 'block';
        } else {
            this.elements.orderCount.style.display = 'none';
        }
    }
    
    // Quick Action Methods
    showMenu() {
        this.elements.input.value = 'Show me the menu';
        this.sendMessage();
    }
    
    toggleOrderSidebar() {
        this.elements.orderSidebar.classList.toggle('open');
    }
    
    closeOrderSidebar() {
        this.elements.orderSidebar.classList.remove('open');
    }
    
    showHelp() {
        this.elements.input.value = 'Help me get started';
        this.sendMessage();
    }
    
    // Utility methods
    ping() {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }
    
    startPingInterval() {
        // Send ping every 30 seconds to keep connection alive
        setInterval(() => this.ping(), 30000);
    }

    checkTableContext() {
        // Check URL parameters for table context
        const urlParams = new URLSearchParams(window.location.search);
        const tableNumber = urlParams.get('table');
        const qrId = urlParams.get('qr_id');
        const providedSessionId = urlParams.get('session_id');
        
        if (tableNumber && qrId) {
            this.tableInfo = {
                tableNumber: parseInt(tableNumber),
                qrId: qrId
            };
            
            // Use provided session ID if available
            if (providedSessionId) {
                this.sessionId = providedSessionId;
            }
            
            console.log(`Table context detected: Table ${tableNumber}`);
            
            // Show table welcome message
            setTimeout(() => {
                this.addMessage('system', 
                    `Welcome to Table ${tableNumber}! I'm your AI assistant. ` +
                    `I can help you browse our menu, place orders, join our queue, or just chat. ` +
                    `What can I do for you today?`
                );
            }, 1000);
        }
    }
    
    async joinQueue() {
        try {
            const customerName = prompt('Enter your name for the queue:');
            if (!customerName) return;
            
            const partySize = parseInt(prompt('Party size:', '1')) || 1;
            const phone = prompt('Phone number (optional for notifications):') || null;
            
            const response = await fetch('/api/queue/join', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    customer_name: customerName,
                    queue_type: 'walk_in',
                    party_size: partySize,
                    customer_phone: phone,
                    session_id: this.sessionId
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.queueStatus = data.queue_entry;
                this.addMessage('system', data.message);
                this.showQueueStatus();
                
                // Start polling for queue updates
                this.startQueuePolling();
            } else {
                this.addMessage('system', 'Sorry, there was an error joining the queue. Please try again.');
            }
            
        } catch (error) {
            console.error('Error joining queue:', error);
            this.addMessage('system', 'Sorry, there was an error joining the queue. Please try again.');
        }
    }
    
    startQueuePolling() {
        if (this.queuePolling) {
            clearInterval(this.queuePolling);
        }
        
        this.queuePolling = setInterval(async () => {
            await this.updateQueueStatus();
        }, 30000); // Check every 30 seconds
    }
    
    async updateQueueStatus() {
        if (!this.queueStatus) return;
        
        try {
            const response = await fetch(`/api/queue/status/${this.queueStatus.queue_id}`);
            const data = await response.json();
            
            if (data.success) {
                const oldPosition = this.queueStatus.position;
                const newPosition = data.status.position;
                
                this.queueStatus = data.status;
                
                // Notify if position changed significantly
                if (oldPosition && newPosition < oldPosition) {
                    this.addMessage('system', 
                        `Good news! You've moved up to position #${newPosition} in line. ` +
                        `Estimated wait: ${data.status.estimated_wait_time} minutes.`
                    );
                }
                
                // Notify if called
                if (data.status.status === 'called') {
                    this.addMessage('system', 
                        `🔔 Your table is ready! Please come to the front desk. ` +
                        (data.status.table_number ? `Table #${data.status.table_number}` : '')
                    );
                    this.playNotificationSound();
                }
                
                this.showQueueStatus();
            }
            
        } catch (error) {
            console.error('Error updating queue status:', error);
        }
    }
    
    showQueueStatus() {
        if (!this.queueStatus) return;
        
        const statusElement = document.getElementById('queueStatus') || this.createQueueStatusElement();
        
        const statusText = this.queueStatus.status === 'waiting' ? 
            `Position #${this.queueStatus.position} • Wait: ~${this.queueStatus.estimated_wait_time}min` :
            `Status: ${this.queueStatus.status.replace('_', ' ').toUpperCase()}`;
        
        statusElement.innerHTML = `
            <div style="background: var(--coffee-light); padding: 1rem; border-radius: var(--radius-lg); margin: 1rem 0;">
                <strong>Queue Status:</strong> ${statusText}
                <br><small>We'll notify you when it's your turn!</small>
            </div>
        `;
    }
    
    createQueueStatusElement() {
        const statusElement = document.createElement('div');
        statusElement.id = 'queueStatus';
        
        // Insert after suggestions container
        const suggestionsContainer = this.elements.suggestionsContainer;
        if (suggestionsContainer && suggestionsContainer.parentNode) {
            suggestionsContainer.parentNode.insertBefore(statusElement, suggestionsContainer.nextSibling);
        } else {
            // Fallback: insert before input container
            const inputContainer = document.querySelector('.chat-input-container');
            if (inputContainer && inputContainer.parentNode) {
                inputContainer.parentNode.insertBefore(statusElement, inputContainer);
            }
        }
        
        return statusElement;
    }
    
    playNotificationSound() {
        // Simple notification sound using AudioContext
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'square';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.log('Could not play notification sound:', error);
        }
    }
    
    showEmotionalSupport(emotionalData) {
        if (!emotionalData) return;
        
        // Show breathing exercise if provided
        if (emotionalData.breathing_exercise) {
            this.showBreathingExercise(emotionalData.breathing_exercise);
        }
        
        // Show positive affirmation if provided
        if (emotionalData.positive_affirmation) {
            setTimeout(() => {
                this.addMessage('system', `💙 ${emotionalData.positive_affirmation}`);
            }, 2000);
        }
        
        // Show drink recommendations
        if (emotionalData.drink_recommendations && emotionalData.drink_recommendations.length > 0) {
            this.showTherapeuticRecommendations(emotionalData.drink_recommendations);
        }
    }
    
    showBreathingExercise(exercise) {
        const breathingElement = document.createElement('div');
        breathingElement.id = 'breathingExercise';
        breathingElement.innerHTML = `
            <div style="background: linear-gradient(135deg, #e3f2fd, #f3e5f5); padding: 1.5rem; border-radius: var(--radius-lg); margin: 1rem 0; text-align: center; border: 1px solid #b3e5fc;">
                <h4 style="color: var(--coffee-dark); margin-bottom: 1rem;">🫁 Breathing Exercise</h4>
                <p style="margin-bottom: 1rem;">${exercise}</p>
                <button onclick="this.parentElement.style.display='none'" style="background: var(--coffee-primary); color: white; border: none; padding: 0.5rem 1rem; border-radius: var(--radius-md); cursor: pointer;">
                    Thanks, I feel better
                </button>
            </div>
        `;
        
        // Insert before input container
        const inputContainer = document.querySelector('.chat-input-container');
        if (inputContainer && inputContainer.parentNode) {
            inputContainer.parentNode.insertBefore(breathingElement, inputContainer);
            
            // Auto-remove after 30 seconds
            setTimeout(() => {
                if (breathingElement.parentNode) {
                    breathingElement.remove();
                }
            }, 30000);
        }
    }
    
    showTherapeuticRecommendations(recommendations) {
        const recElement = document.createElement('div');
        recElement.innerHTML = `
            <div style="background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-lg); margin: 1rem 0; border-left: 4px solid var(--coffee-primary);">
                <h4 style="color: var(--coffee-dark); margin-bottom: 0.5rem;">💚 Therapeutic Recommendations</h4>
                ${recommendations.map(rec => `
                    <div style="margin: 0.5rem 0; padding: 0.5rem; background: var(--bg-primary); border-radius: var(--radius-md);">
                        <strong>${rec.drink_name}</strong> - $${rec.price.toFixed(2)}
                        <br><small style="color: var(--text-secondary);">${rec.emotional_benefit}</small>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Insert after last message
        this.elements.messages.appendChild(recElement);
        this.scrollToBottom();
    }
    
    scheduleAppointment() {
        // Open appointment scheduling interface
        const appointmentHtml = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;" onclick="this.remove()">
                <div style="background: white; padding: 2rem; border-radius: var(--radius-xl); max-width: 500px; width: 90%;" onclick="event.stopPropagation()">
                    <h3 style="margin-bottom: 1rem;">Schedule an Appointment</h3>
                    <form id="appointmentForm">
                        <div style="margin-bottom: 1rem;">
                            <label>Your Name:</label>
                            <input type="text" id="organizerName" required style="width: 100%; padding: 0.5rem; margin-top: 0.25rem;">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label>Appointment Type:</label>
                            <select id="appointmentType" style="width: 100%; padding: 0.5rem; margin-top: 0.25rem;">
                                <option value="coffee_meeting">Coffee Meeting</option>
                                <option value="coffee_date">Coffee Date</option>
                                <option value="business_meeting">Business Meeting</option>
                                <option value="study_session">Study Session</option>
                                <option value="therapy_session">Emotional Support Session</option>
                            </select>
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label>Date & Time:</label>
                            <input type="datetime-local" id="scheduledTime" required style="width: 100%; padding: 0.5rem; margin-top: 0.25rem;">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label>Duration (minutes):</label>
                            <input type="number" id="duration" value="60" min="15" max="240" style="width: 100%; padding: 0.5rem; margin-top: 0.25rem;">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label>Party Size:</label>
                            <input type="number" id="participantCount" value="2" min="1" max="8" style="width: 100%; padding: 0.5rem; margin-top: 0.25rem;">
                        </div>
                        <div style="margin-bottom: 1rem;">
                            <label>Phone (optional):</label>
                            <input type="tel" id="organizerPhone" style="width: 100%; padding: 0.5rem; margin-top: 0.25rem;">
                        </div>
                        <div style="display: flex; gap: 1rem;">
                            <button type="submit" style="background: var(--coffee-primary); color: white; padding: 0.75rem 1.5rem; border: none; border-radius: var(--radius-md); cursor: pointer; flex: 1;">
                                Schedule Appointment
                            </button>
                            <button type="button" onclick="this.closest('div[style*=\"position: fixed\"]').remove()" style="background: var(--text-secondary); color: white; padding: 0.75rem 1rem; border: none; border-radius: var(--radius-md); cursor: pointer;">
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', appointmentHtml);
        
        // Handle form submission
        document.getElementById('appointmentForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const appointmentData = {
                organizer_name: document.getElementById('organizerName').value,
                appointment_type: document.getElementById('appointmentType').value,
                scheduled_time: document.getElementById('scheduledTime').value,
                duration_minutes: parseInt(document.getElementById('duration').value),
                participant_count: parseInt(document.getElementById('participantCount').value),
                organizer_phone: document.getElementById('organizerPhone').value
            };
            
            try {
                const response = await fetch('/api/appointments/schedule', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(appointmentData)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.addMessage('system', data.message);
                    document.querySelector('div[style*="position: fixed"]').remove();
                } else {
                    alert('Error scheduling appointment: ' + data.error);
                }
                
            } catch (error) {
                console.error('Error scheduling appointment:', error);
                alert('Error scheduling appointment. Please try again.');
            }
        });
    }
    
    requestEmotionalSupport() {
        const messages = [
            "I'm feeling a bit stressed today",
            "I could use some comfort",
            "I'm having a rough day",
            "I need something to lift my spirits"
        ];
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        this.elements.input.value = randomMessage;
        this.sendMessage();
    }
}

// Initialize chat when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing Coffee Shop AI Chat...');
    const chat = new CoffeeShopChat();
    
    // Start ping interval
    chat.startPingInterval();
    
    // Make chat globally available for debugging
    window.coffeeChat = chat;
});

// Service Worker registration for PWA (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => console.log('SW registered'))
            .catch(error => console.log('SW registration failed'));
    });
}

// Add this to the end of static/js/chat.js or create a separate file

// Service Worker registration for PWA (fixed path)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Try multiple paths to find the service worker
        const swPaths = ['/sw.js', '/static/sw.js'];
        
        async function registerSW() {
            for (const path of swPaths) {
                try {
                    const registration = await navigator.serviceWorker.register(path);
                    console.log('✅ SW registered successfully at:', path);
                    console.log('SW scope:', registration.scope);
                    return;
                } catch (error) {
                    console.log(`❌ Failed to register SW at ${path}:`, error.message);
                }
            }
            console.log('⚠️ Could not register service worker at any path');
        }
        
        registerSW();
    });
}