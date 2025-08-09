// Coffee Shop PWA Service Worker
const CACHE_NAME = 'coffee-shop-v1.0.0';
const STATIC_CACHE = 'coffee-shop-static-v1';
const DYNAMIC_CACHE = 'coffee-shop-dynamic-v1';

// Assets to cache for offline functionality
const STATIC_ASSETS = [
    '/',
    '/static/css/chat.css',
    '/static/js/chat.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/manifest.json',
    // Fallback pages
    '/offline.html'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/menu',
    '/health'
];

// Cache strategies
const CACHE_STRATEGIES = {
    // Cache first for static assets
    CACHE_FIRST: 'cache-first',
    // Network first for dynamic content
    NETWORK_FIRST: 'network-first',
    // Stale while revalidate for frequently updated content
    STALE_WHILE_REVALIDATE: 'stale-while-revalidate'
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        Promise.all([
            // Cache static assets
            caches.open(STATIC_CACHE).then((cache) => {
                console.log('📦 Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            }),
            // Cache API endpoints
            caches.open(DYNAMIC_CACHE).then((cache) => {
                console.log('📦 Pre-caching API endpoints');
                return Promise.allSettled(
                    API_ENDPOINTS.map(url => 
                        fetch(url).then(response => {
                            if (response.ok) {
                                return cache.put(url, response);
                            }
                        }).catch(() => {
                            // Ignore fetch errors during install
                        })
                    )
                );
            })
        ]).then(() => {
            console.log('✅ Service Worker installed successfully');
            // Skip waiting to activate immediately
            return self.skipWaiting();
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        Promise.all([
            // Clean up old caches
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && 
                            cacheName !== DYNAMIC_CACHE && 
                            cacheName !== CACHE_NAME) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            // Take control of all clients
            self.clients.claim()
        ]).then(() => {
            console.log('✅ Service Worker activated successfully');
        })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Only handle GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip WebSocket and chrome-extension requests
    if (url.protocol === 'ws:' || url.protocol === 'wss:' || 
        url.protocol === 'chrome-extension:') {
        return;
    }
    
    // Determine caching strategy based on request
    const strategy = getCacheStrategy(request, url);
    
    event.respondWith(
        handleFetchWithStrategy(request, strategy)
    );
});

// Message event - handle messages from main thread
self.addEventListener('message', (event) => {
    const { type, payload } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'GET_CACHE_STATUS':
            getCacheStatus().then(status => {
                event.ports[0].postMessage(status);
            });
            break;
            
        case 'CLEAR_CACHE':
            clearCache(payload?.cacheName).then(() => {
                event.ports[0].postMessage({ success: true });
            });
            break;
            
        case 'CACHE_URL':
            cacheUrl(payload?.url).then((success) => {
                event.ports[0].postMessage({ success });
            });
            break;
    }
});

// Background sync for offline orders
self.addEventListener('sync', (event) => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    if (event.tag === 'order-sync') {
        event.waitUntil(syncOfflineOrders());
    } else if (event.tag === 'analytics-sync') {
        event.waitUntil(syncAnalytics());
    }
});

// Push notifications
self.addEventListener('push', (event) => {
    console.log('📱 Push notification received');
    
    const options = {
        body: 'Your coffee order is ready for pickup!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        tag: 'order-ready',
        data: {
            url: '/',
            action: 'order_ready'
        },
        actions: [
            {
                action: 'view',
                title: 'View Order',
                icon: '/static/icons/action-view.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/icons/action-dismiss.png'
            }
        ],
        vibrate: [200, 100, 200],
        requireInteraction: true
    };
    
    if (event.data) {
        try {
            const data = event.data.json();
            options.body = data.body || options.body;
            options.data = { ...options.data, ...data };
        } catch (e) {
            console.error('Error parsing push data:', e);
        }
    }
    
    event.waitUntil(
        self.registration.showNotification('Coffee Shop AI', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Notification clicked:', event.action);
    
    event.notification.close();
    
    const { action, data } = event;
    
    if (action === 'view' || !action) {
        // Open the app
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((clientList) => {
                // Check if app is already open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(data?.url || '/');
                }
            })
        );
    }
    // Dismiss action does nothing (notification already closed)
});

// Utility Functions

function getCacheStrategy(request, url) {
    // Static assets - cache first
    if (STATIC_ASSETS.some(asset => url.pathname.endsWith(asset)) ||
        url.pathname.includes('/static/')) {
        return CACHE_STRATEGIES.CACHE_FIRST;
    }
    
    // API endpoints - network first
    if (url.pathname.startsWith('/api/') || 
        url.pathname.startsWith('/analytics/') ||
        API_ENDPOINTS.includes(url.pathname)) {
        return CACHE_STRATEGIES.NETWORK_FIRST;
    }
    
    // WebSocket connections - no caching
    if (url.pathname.startsWith('/ws/')) {
        return null;
    }
    
    // Default to stale while revalidate
    return CACHE_STRATEGIES.STALE_WHILE_REVALIDATE;
}

async function handleFetchWithStrategy(request, strategy) {
    const url = new URL(request.url);
    
    switch (strategy) {
        case CACHE_STRATEGIES.CACHE_FIRST:
            return cacheFirst(request);
            
        case CACHE_STRATEGIES.NETWORK_FIRST:
            return networkFirst(request);
            
        case CACHE_STRATEGIES.STALE_WHILE_REVALIDATE:
            return staleWhileRevalidate(request);
            
        default:
            // No caching strategy - just fetch
            return fetch(request);
    }
}

async function cacheFirst(request) {
    const cache = await caches.open(STATIC_CACHE);
    const cached = await cache.match(request);
    
    if (cached) {
        return cached;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('Cache first strategy failed:', error);
        return getOfflineFallback(request);
    }
}

async function networkFirst(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            // Update cache with fresh response
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }
        
        return getOfflineFallback(request);
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cached = await cache.match(request);
    
    // Start fetch in background
    const fetchPromise = fetch(request).then(response => {
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    }).catch(() => null);
    
    // Return cached version immediately if available
    if (cached) {
        return cached;
    }
    
    // Wait for network if no cache
    return fetchPromise || getOfflineFallback(request);
}

async function getOfflineFallback(request) {
    const url = new URL(request.url);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
        const cache = await caches.open(STATIC_CACHE);
        return cache.match('/offline.html') || 
               new Response('Offline - Please check your connection', {
                   status: 503,
                   statusText: 'Service Unavailable'
               });
    }
    
    // Return empty response for other requests
    return new Response('', {
        status: 503,
        statusText: 'Service Unavailable'
    });
}

async function syncOfflineOrders() {
    try {
        // Get offline orders from IndexedDB
        const db = await openOrderDB();
        const orders = await getOfflineOrders(db);
        
        for (const order of orders) {
            try {
                const response = await fetch('/api/orders', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(order)
                });
                
                if (response.ok) {
                    await removeOfflineOrder(db, order.id);
                    console.log('✅ Synced offline order:', order.id);
                }
            } catch (error) {
                console.error('Failed to sync order:', order.id, error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

async function syncAnalytics() {
    try {
        // Sync cached analytics events
        console.log('🔄 Syncing analytics events...');
        // Implementation would sync analytics data
    } catch (error) {
        console.error('Analytics sync failed:', error);
    }
}

async function getCacheStatus() {
    const cacheNames = await caches.keys();
    const status = {};
    
    for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        status[cacheName] = {
            size: keys.length,
            urls: keys.map(request => request.url)
        };
    }
    
    return status;
}

async function clearCache(cacheName) {
    if (cacheName) {
        return caches.delete(cacheName);
    } else {
        const cacheNames = await caches.keys();
        return Promise.all(cacheNames.map(name => caches.delete(name)));
    }
}

async function cacheUrl(url) {
    try {
        const cache = await caches.open(DYNAMIC_CACHE);
        const response = await fetch(url);
        if (response.ok) {
            await cache.put(url, response);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Failed to cache URL:', url, error);
        return false;
    }
}

// IndexedDB helpers for offline orders
async function openOrderDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('OfflineOrders', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('orders')) {
                const store = db.createObjectStore('orders', { keyPath: 'id' });
                store.createIndex('timestamp', 'timestamp');
            }
        };
    });
}

async function getOfflineOrders(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['orders'], 'readonly');
        const store = transaction.objectStore('orders');
        const request = store.getAll();
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function removeOfflineOrder(db, orderId) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['orders'], 'readwrite');
        const store = transaction.objectStore('orders');
        const request = store.delete(orderId);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

console.log('🎯 Coffee Shop Service Worker loaded');