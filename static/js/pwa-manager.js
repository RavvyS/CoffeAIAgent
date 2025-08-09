// PWA Installation and Mobile Features Manager
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.isInstalled = false;
        this.isStandalone = false;
        this.installPromptShown = false;
        
        this.init();
    }
    
    init() {
        this.checkInstallStatus();
        this.registerServiceWorker();
        this.bindInstallEvents();
        this.setupMobileOptimizations();
        this.initializeNotifications();
        this.setupOfflineDetection();
    }
    
    checkInstallStatus() {
        // Check if running as standalone app
        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                           window.navigator.standalone === true;
        
        // Check if already installed
        this.isInstalled = this.isStandalone || 
                          localStorage.getItem('pwa-installed') === 'true';
        
        console.log('📱 PWA Status:', {
            standalone: this.isStandalone,
            installed: this.isInstalled
        });
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });
                
                console.log('✅ Service Worker registered:', registration.scope);
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    console.log('🔄 Service Worker update found');
                    this.handleServiceWorkerUpdate(registration);
                });
                
                // Check for waiting service worker
                if (registration.waiting) {
                    this.showUpdateNotification(registration);
                }
                
                return registration;
            } catch (error) {
                console.error('❌ Service Worker registration failed:', error);
            }
        } else {
            console.warn('⚠️ Service Workers not supported');
        }
    }
    
    bindInstallEvents() {
        // Listen for install prompt
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('📱 Install prompt available');
            e.preventDefault(); // Prevent default mini-infobar
            this.deferredPrompt = e;
            this.showInstallButton();
        });
        
        // Listen for successful installation
        window.addEventListener('appinstalled', () => {
            console.log('🎉 PWA installed successfully');
            this.handleSuccessfulInstall();
        });
        
        // Handle iOS install instructions
        if (this.isIOS() && !this.isStandalone) {
            this.showIOSInstallInstructions();
        }
    }
    
    setupMobileOptimizations() {
        // Prevent zoom on input focus (iOS)
        if (this.isIOS()) {
            const metaViewport = document.querySelector('meta[name=viewport]');
            if (metaViewport) {
                metaViewport.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no';
            }
        }
        
        // Handle safe areas for iPhone X+
        this.setupSafeAreas();
        
        // Optimize scroll behavior
        this.optimizeScrolling();
        
        // Handle orientation changes
        this.handleOrientationChange();
        
        // Setup pull-to-refresh
        this.setupPullToRefresh();
    }
    
    async initializeNotifications() {
        if ('Notification' in window && 'serviceWorker' in navigator) {
            try {
                const permission = await this.requestNotificationPermission();
                if (permission === 'granted') {
                    console.log('✅ Notifications enabled');
                    this.setupPushNotifications();
                }
            } catch (error) {
                console.error('❌ Notification setup failed:', error);
            }
        }
    }
    
    setupOfflineDetection() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            console.log('🌐 Back online');
            this.showNetworkStatus('online');
            this.syncOfflineData();
        });
        
        window.addEventListener('offline', () => {
            console.log('📴 Gone offline');
            this.showNetworkStatus('offline');
        });
        
        // Initial status
        if (!navigator.onLine) {
            this.showNetworkStatus('offline');
        }
    }
    
    // Install Methods
    async promptInstall() {
        if (!this.deferredPrompt) {
            if (this.isIOS()) {
                this.showIOSInstallInstructions();
                return;
            }
            
            this.showManualInstallInstructions();
            return;
        }
        
        try {
            // Show install prompt
            this.deferredPrompt.prompt();
            
            // Wait for user response
            const { outcome } = await this.deferredPrompt.userChoice;
            
            console.log('📱 Install prompt result:', outcome);
            
            if (outcome === 'accepted') {
                this.handleSuccessfulInstall();
            } else {
                this.handleInstallDismissal();
            }
            
            // Clear the prompt
            this.deferredPrompt = null;
            
        } catch (error) {
            console.error('❌ Install prompt failed:', error);
        }
    }
    
    showInstallButton() {
        if (this.installPromptShown || this.isInstalled) return;
        
        const installButton = this.createInstallButton();
        document.body.appendChild(installButton);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            if (installButton.parentNode) {
                installButton.remove();
            }
        }, 10000);
        
        this.installPromptShown = true;
    }
    
    createInstallButton() {
        const button = document.createElement('div');
        button.className = 'pwa-install-prompt';
        button.innerHTML = `
            <div class="install-content">
                <div class="install-icon">📱</div>
                <div class="install-text">
                    <div class="install-title">Install Coffee Shop AI</div>
                    <div class="install-subtitle">Get the full app experience</div>
                </div>
                <button class="install-btn" onclick="window.pwaManager.promptInstall()">Install</button>
                <button class="install-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .pwa-install-prompt {
                position: fixed;
                bottom: 20px;
                left: 20px;
                right: 20px;
                background: linear-gradient(135deg, #8B4513 0%, #5D2F0A 100%);
                color: white;
                padding: 1rem;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
                z-index: 10000;
                animation: slideUp 0.3s ease-out;
            }
            
            .install-content {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .install-icon {
                font-size: 2rem;
            }
            
            .install-text {
                flex: 1;
            }
            
            .install-title {
                font-weight: 600;
                margin-bottom: 0.25rem;
            }
            
            .install-subtitle {
                font-size: 0.875rem;
                opacity: 0.9;
            }
            
            .install-btn {
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            }
            
            .install-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            
            .install-close {
                background: none;
                border: none;
                color: white;
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0.25rem;
                margin-left: 0.5rem;
            }
            
            @keyframes slideUp {
                from { transform: translateY(100%); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            
            @media (max-width: 768px) {
                .pwa-install-prompt {
                    left: 10px;
                    right: 10px;
                    bottom: 10px;
                }
                
                .install-content {
                    flex-direction: column;
                    text-align: center;
                    gap: 0.75rem;
                }
            }
        `;
        document.head.appendChild(style);
        
        return button;
    }
    
    showIOSInstallInstructions() {
        const modal = document.createElement('div');
        modal.className = 'ios-install-modal';
        modal.innerHTML = `
            <div class="modal-overlay" onclick="this.parentElement.remove()">
                <div class="modal-content" onclick="event.stopPropagation()">
                    <div class="modal-header">
                        <h3>Install Coffee Shop AI</h3>
                        <button onclick="this.closest('.ios-install-modal').remove()">×</button>
                    </div>
                    <div class="modal-body">
                        <p>To install this app on your iPhone:</p>
                        <ol>
                            <li>Tap the Share button <span class="ios-icon">📤</span></li>
                            <li>Scroll down and tap "Add to Home Screen" <span class="ios-icon">➕</span></li>
                            <li>Tap "Add" to confirm</li>
                        </ol>
                        <div class="ios-gif">
                            <img src="/static/images/ios-install.gif" alt="iOS Installation Steps" style="max-width: 100%; height: auto;">
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    handleSuccessfulInstall() {
        this.isInstalled = true;
        localStorage.setItem('pwa-installed', 'true');
        
        // Remove install prompts
        const installPrompt = document.querySelector('.pwa-install-prompt');
        if (installPrompt) {
            installPrompt.remove();
        }
        
        // Show success message
        this.showToast('App installed successfully! 🎉', 'success');
        
        // Track installation
        this.trackEvent('pwa_installed');
    }
    
    handleInstallDismissal() {
        // Don't show install prompt again for a while
        localStorage.setItem('install-dismissed', Date.now().toString());
        this.trackEvent('pwa_install_dismissed');
    }
    
    // Mobile Optimization Methods
    setupSafeAreas() {
        // Add CSS custom properties for safe areas
        const style = document.createElement('style');
        style.textContent = `
            :root {
                --safe-area-inset-top: env(safe-area-inset-top);
                --safe-area-inset-right: env(safe-area-inset-right);
                --safe-area-inset-bottom: env(safe-area-inset-bottom);
                --safe-area-inset-left: env(safe-area-inset-left);
            }
            
            .chat-container {
                padding-top: max(0px, var(--safe-area-inset-top));
                padding-bottom: max(0px, var(--safe-area-inset-bottom));
                padding-left: max(0px, var(--safe-area-inset-left));
                padding-right: max(0px, var(--safe-area-inset-right));
            }
        `;
        document.head.appendChild(style);
    }
    
    optimizeScrolling() {
        // Enable momentum scrolling on iOS
        document.addEventListener('touchstart', {}, {passive: true});
        document.addEventListener('touchmove', {}, {passive: true});
        
        // Prevent overscroll
        document.addEventListener('touchmove', (e) => {
            if (e.target.closest('.no-scroll')) {
                e.preventDefault();
            }
        }, {passive: false});
    }
    
    handleOrientationChange() {
        window.addEventListener('orientationchange', () => {
            // Delay to allow orientation to complete
            setTimeout(() => {
                // Trigger resize event
                window.dispatchEvent(new Event('resize'));
                
                // Scroll to top to fix viewport issues
                window.scrollTo(0, 0);
            }, 100);
        });
    }
    
    setupPullToRefresh() {
        let startY = 0;
        let currentY = 0;
        let pulling = false;
        
        const pullIndicator = this.createPullIndicator();
        
        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
            }
        }, {passive: true});
        
        document.addEventListener('touchmove', (e) => {
            if (window.scrollY === 0 && startY) {
                currentY = e.touches[0].clientY;
                const pullDistance = currentY - startY;
                
                if (pullDistance > 50 && !pulling) {
                    pulling = true;
                    pullIndicator.classList.add('visible');
                    
                    // Haptic feedback
                    if ('vibrate' in navigator) {
                        navigator.vibrate(50);
                    }
                }
            }
        }, {passive: true});
        
        document.addEventListener('touchend', () => {
            if (pulling) {
                pulling = false;
                pullIndicator.classList.remove('visible');
                
                // Refresh the page/data
                if (window.coffeeChat) {
                    window.coffeeChat.connect();
                }
                
                this.showToast('Refreshed!', 'info');
            }
            startY = 0;
        });
    }
    
    createPullIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'pull-refresh-indicator';
        indicator.innerHTML = '🔄 Pull to refresh';
        document.body.appendChild(indicator);
        return indicator;
    }
    
    // Notification Methods
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            return 'denied';
        }
        
        if (Notification.permission === 'granted') {
            return 'granted';
        }
        
        if (Notification.permission === 'denied') {
            return 'denied';
        }
        
        // Request permission
        const permission = await Notification.requestPermission();
        return permission;
    }
    
    async setupPushNotifications() {
        try {
            const registration = await navigator.serviceWorker.ready;
            
            // Check if push messaging is supported
            if (!('PushManager' in window)) {
                console.warn('Push messaging not supported');
                return;
            }
            
            // Get existing subscription or create new one
            let subscription = await registration.pushManager.getSubscription();
            
            if (!subscription) {
                // Create new subscription
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(
                        'YOUR_VAPID_PUBLIC_KEY' // Replace with actual VAPID key
                    )
                });
            }
            
            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);
            
            console.log('✅ Push notifications enabled');
            
        } catch (error) {
            console.error('❌ Push notification setup failed:', error);
        }
    }
    
    async sendSubscriptionToServer(subscription) {
        try {
            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscription)
            });
        } catch (error) {
            console.error('Failed to send subscription to server:', error);
        }
    }
    
    // Utility Methods
    isIOS() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    }
    
    isAndroid() {
        return /Android/.test(navigator.userAgent);
    }
    
    isMobile() {
        return this.isIOS() || this.isAndroid() || 
               /Mobile|Tablet/.test(navigator.userAgent);
    }
    
    showNetworkStatus(status) {
        const statusIndicator = document.querySelector('.network-status') || 
                               this.createNetworkStatusIndicator();
        
        statusIndicator.className = `network-status ${status}`;
        statusIndicator.textContent = status === 'online' ? 
            '🌐 Back online' : '📴 Offline mode';
        
        statusIndicator.style.display = 'block';
        
        if (status === 'online') {
            setTimeout(() => {
                statusIndicator.style.display = 'none';
            }, 3000);
        }
    }
    
    createNetworkStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'network-status';
        document.body.appendChild(indicator);
        return indicator;
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Animate in
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    async syncOfflineData() {
        // Trigger background sync if available
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            try {
                const registration = await navigator.serviceWorker.ready;
                await registration.sync.register('order-sync');
                await registration.sync.register('analytics-sync');
                console.log('🔄 Background sync registered');
            } catch (error) {
                console.error('❌ Background sync failed:', error);
            }
        }
    }
    
    trackEvent(eventName, data = {}) {
        // Track PWA events for analytics
        if (window.coffeeChat && window.coffeeChat.trackEvent) {
            window.coffeeChat.trackEvent(eventName, data);
        }
    }
    
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
    
    handleServiceWorkerUpdate(registration) {
        const newWorker = registration.installing;
        
        newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                this.showUpdateNotification(registration);
            }
        });
    }
    
    showUpdateNotification(registration) {
        const updateBanner = document.createElement('div');
        updateBanner.className = 'update-banner';
        updateBanner.innerHTML = `
            <div class="update-content">
                <span>🔄 New version available!</span>
                <button onclick="window.pwaManager.updateApp('${registration.scope}')">Update</button>
                <button onclick="this.parentElement.parentElement.remove()">Later</button>
            </div>
        `;
        
        document.body.appendChild(updateBanner);
    }
    
    updateApp(scope) {
        // Send message to service worker to skip waiting
        navigator.serviceWorker.controller.postMessage({type: 'SKIP_WAITING'});
        
        // Reload page when new service worker takes control
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            window.location.reload();
        });
    }
}

// Initialize PWA Manager
window.addEventListener('DOMContentLoaded', () => {
    window.pwaManager = new PWAManager();
    console.log('📱 PWA Manager initialized');
});

// Add PWA styles
const pwaStyles = document.createElement('style');
pwaStyles.textContent = `
    .network-status {
        position: fixed;
        top: 10px;
        left: 50%;
        transform: translateX(-50%);
        background: #333;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.875rem;
        z-index: 10001;
        display: none;
    }
    
    .network-status.offline {
        background: #EF4444;
    }
    
    .network-status.online {
        background: #22C55E;
    }
    
    .toast {
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%) translateY(100px);
        background: #333;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        z-index: 10002;
        transition: transform 0.3s ease;
    }
    
    .toast.show {
        transform: translateX(-50%) translateY(0);
    }
    
    .toast-success {
        background: #22C55E;
    }
    
    .toast-error {
        background: #EF4444;
    }
    
    .toast-info {
        background: #3B82F6;
    }
    
    .pull-refresh-indicator {
        position: fixed;
        top: -50px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(139, 69, 19, 0.9);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0 0 20px 20px;
        transition: top 0.3s ease;
        z-index: 10000;
    }
    
    .pull-refresh-indicator.visible {
        top: 0;
    }
    
    .update-banner {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: #8B4513;
        color: white;
        padding: 1rem;
        text-align: center;
        z-index: 10003;
    }
    
    .update-content {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 1rem;
    }
    
    .update-content button {
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.3);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        cursor: pointer;
    }
    
    @media (max-width: 768px) {
        .update-content {
            flex-direction: column;
            gap: 0.5rem;
        }
    }
`;
document.head.appendChild(pwaStyles);