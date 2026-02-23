// WebSocket Client for Real-time Updates

class WebSocketClient {
    constructor(url = null) {
        this.url = url || this.getWebSocketURL();
        this.ws = null;
        this.reconnectInterval = 5000;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.isIntentionallyClosed = false;
        this.messageHandlers = new Map();
        
        this.connect();
    }
    
    getWebSocketURL() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws`;
    }
    
    connect() {
        if (this.isIntentionallyClosed) {
            return;
        }
        
        try {
            console.log('Connecting to WebSocket:', this.url);
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => this.onOpen();
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onclose = (event) => this.onClose(event);
            this.ws.onerror = (error) => this.onError(error);
            
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.scheduleReconnect();
        }
    }
    
    onOpen() {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        
        // Show connection notification
        if (typeof showNotification === 'function') {
            showNotification('Connected to server', 'success', 3000);
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('websocket-connected'));
    }
    
    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message received:', data);
            
            this.handleMessage(data);
            
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    }
    
    onClose(event) {
        console.log('WebSocket disconnected:', event.code, event.reason);
        
        if (!this.isIntentionallyClosed) {
            // Show disconnection notification
            if (typeof showNotification === 'function') {
                showNotification('Disconnected from server', 'warning', 3000);
            }
            
            // Trigger custom event
            window.dispatchEvent(new CustomEvent('websocket-disconnected'));
            
            // Schedule reconnect
            this.scheduleReconnect();
        }
    }
    
    onError(error) {
        console.error('WebSocket error:', error);
    }
    
    scheduleReconnect() {
        if (this.isIntentionallyClosed) {
            return;
        }
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnect attempts reached');
            if (typeof showNotification === 'function') {
                showNotification('Failed to connect to server. Please refresh the page.', 'error', 0);
            }
            return;
        }
        
        this.reconnectAttempts++;
        const delay = this.reconnectInterval * Math.min(this.reconnectAttempts, 5);
        
        console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, delay);
    }
    
    handleMessage(data) {
        const { type, ...payload } = data;
        
        // Call registered handlers for this message type
        if (this.messageHandlers.has(type)) {
            const handlers = this.messageHandlers.get(type);
            handlers.forEach(handler => {
                try {
                    handler(payload);
                } catch (error) {
                    console.error(`Error in message handler for type '${type}':`, error);
                }
            });
        }
        
        // Default handlers
        switch (type) {
            case 'vkp_update':
                this.handleVKPUpdate(payload);
                break;
            case 'etl_complete':
                this.handleETLComplete(payload);
                break;
            case 'error':
                this.handleError(payload);
                break;
            case 'system_health':
                this.handleSystemHealth(payload);
                break;
            case 'notification':
                this.handleNotification(payload);
                break;
            default:
                console.log('Unhandled message type:', type, payload);
        }
    }
    
    handleVKPUpdate(payload) {
        const { subject, grade, version, message } = payload;
        
        if (typeof showNotification === 'function') {
            showNotification(message || `New VKP available: ${subject} Kelas ${grade} v${version}`, 'info');
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('vkp-update', { detail: payload }));
        
        // Refresh VKP list if on VKP manager page
        if (typeof refreshVKPList === 'function') {
            refreshVKPList();
        }
    }
    
    handleETLComplete(payload) {
        const { job_id, status, message } = payload;
        
        const notificationType = status === 'completed' ? 'success' : 'error';
        
        if (typeof showNotification === 'function') {
            showNotification(message || `ETL pipeline ${status}: ${job_id}`, notificationType);
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('etl-complete', { detail: payload }));
        
        // Refresh job history if on job history page
        if (typeof refreshJobHistory === 'function') {
            refreshJobHistory();
        }
    }
    
    handleError(payload) {
        const { error_type, message } = payload;
        
        if (typeof showNotification === 'function') {
            showNotification(message || `System error: ${error_type}`, 'error');
        }
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('system-error', { detail: payload }));
    }
    
    handleSystemHealth(payload) {
        // Trigger custom event for system health updates
        window.dispatchEvent(new CustomEvent('system-health-update', { detail: payload }));
        
        // Update dashboard if on admin dashboard
        if (typeof loadSystemHealth === 'function') {
            loadSystemHealth();
        }
    }
    
    handleNotification(payload) {
        const { message, type = 'info', duration = 5000 } = payload;
        
        if (typeof showNotification === 'function') {
            showNotification(message, type, duration);
        }
    }
    
    // Register custom message handler
    on(messageType, handler) {
        if (!this.messageHandlers.has(messageType)) {
            this.messageHandlers.set(messageType, []);
        }
        this.messageHandlers.get(messageType).push(handler);
    }
    
    // Unregister message handler
    off(messageType, handler) {
        if (this.messageHandlers.has(messageType)) {
            const handlers = this.messageHandlers.get(messageType);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    // Send message to server
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected. Message not sent:', data);
        }
    }
    
    // Close connection
    close() {
        this.isIntentionallyClosed = true;
        if (this.ws) {
            this.ws.close();
        }
    }
    
    // Reconnect manually
    reconnect() {
        this.isIntentionallyClosed = false;
        this.reconnectAttempts = 0;
        if (this.ws) {
            this.ws.close();
        }
        this.connect();
    }
    
    // Get connection status
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Initialize WebSocket client globally
let wsClient = null;

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if not already initialized
    if (!wsClient) {
        wsClient = new WebSocketClient();
        
        // Make it globally accessible
        window.wsClient = wsClient;
        
        console.log('WebSocket client initialized');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (wsClient) {
        wsClient.close();
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketClient;
}
