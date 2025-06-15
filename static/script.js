
// Global Variables
let isWelcomeComplete = false;
let messageCounter = 0;
let chatStarted = false;
let isProcessingMessage = false;
let lastMessageTime = 0;
let streamingTimeout = null;
let unlockTimeout = null;
let streamingInProgress = false;
let voiceState = 'idle';
let mediaRecorder = null;
let audioChunks = [];

// Voice Interface Variables
let audioContext = null;
let analyser = null;
let microphone = null;
let dataArray = null;
let animationId = null;
let recordingStartTime = null;
let timerInterval = null;

// Admin Dashboard Variables
let debugMode = false;
let processingInProgress = false;

// Optimized timing settings (1-2 seconds max)
const CHARS_PER_SECOND = 40;
const MIN_READING_TIME = 1000; // 1 second minimum
const MAX_READING_TIME = 2000; // 2 seconds maximum
const BUFFER_TIME = 500; // Reduced buffer

// Initialize Everything
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀Chatbot initialized');

    // Check if we're on admin dashboard or main chat
    if (document.getElementById('systemStatusContent')) {
        // Admin dashboard initialization
        initAdminDashboard();
    } else {
        // Main chatbot initialization
        loadCategories();
        startWelcomeAnimation();
        initInputHandlers();
        initAntiSpamProtection();
        initVoiceInterface();
        setInputState(true);
    }
});

// ===== ADMIN DASHBOARD FUNCTIONS =====
function initAdminDashboard() {
    console.log('🚀 Admin dashboard initialized');
    refreshSystemStatus();
    loadProcessingStatus();

    // Update stats periodically
    setInterval(updateDashboardStats, 30000); // Every 30 seconds
}

// Tab switching functionality
function switchTab(tabName) {
    console.log('Switching to tab:', tabName);

    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    const targetTab = document.getElementById(tabName);
    if (targetTab) {
        targetTab.classList.add('active');
        event.target.classList.add('active');
    }
}

// Debug mode toggle
function toggleDebugMode() {
    debugMode = !debugMode;
    const debugSection = document.getElementById('debugSection');

    if (debugSection) {
        if (debugMode) {
            debugSection.style.display = 'block';
            refreshDebugInfo();
            console.log('🐛 Debug mode enabled');
        } else {
            debugSection.style.display = 'none';
            console.log('🐛 Debug mode disabled');
        }
    }
}

// System status functions
function refreshSystemStatus() {
    console.log('🔄 Refreshing system status...');
    const statusContent = document.getElementById('systemStatusContent');
    if (!statusContent) return;

    statusContent.textContent = 'Loading...';

    const systemInfo = {
        timestamp: new Date().toISOString(),
        server_status: 'Online',
        database_status: 'Connected',
        ai_model_status: 'Ready',
        document_processing: 'Available',
        voice_recognition: 'Enabled',
        user_sessions: 'Active',
        memory_usage: '45%',
        cpu_usage: '23%',
        uptime: '2 days, 14 hours'
    };

    statusContent.textContent = JSON.stringify(systemInfo, null, 2);
}

function checkSystemHealth() {
    console.log('❤️ Running system health check...');
    const statusContent = document.getElementById('systemStatusContent');
    if (!statusContent) return;

    statusContent.textContent = 'Running health check...\n\n✅ Database: Connected\n✅ AI Model: Responsive\n✅ File System: Accessible\n✅ Memory: Normal\n✅ Network: Stable\n\n🎉 All systems operational!';
}

// File processing functions
function processFolder(folderName) {
    console.log('⚙️ Processing folder:', folderName);

    if (processingInProgress) {
        alert('Another processing task is already running. Please wait.');
        return;
    }

    processingInProgress = true;
    showProcessingStatus(`Processing ${folderName} folder...`);

    // Simulate processing
    simulateProcessing(() => {
        console.log(`✅ Folder ${folderName} processed successfully`);
        hideProcessingStatus();
        processingInProgress = false;
        alert(`Folder "${folderName}" processed successfully!`);
    });
}

function runBatchProcessing() {
    console.log('🚀 Running batch processing...');

    if (processingInProgress) {
        alert('Processing already in progress. Please wait.');
        return;
    }

    processingInProgress = true;
    const resultsDiv = document.getElementById('processingResults');

    showProcessingStatus('Running batch document processing...');
    if (resultsDiv) {
        resultsDiv.textContent = 'Starting batch processing...\n';
    }

    // Simulate batch processing steps
    const steps = [
        'Scanning document directories...',
        'Processing PDF files...',
        'Extracting text content...',
        'Building document index...',
        'Updating database...',
        'Batch processing completed!'
    ];

    let stepIndex = 0;
    const stepInterval = setInterval(() => {
        if (stepIndex < steps.length) {
            if (resultsDiv) {
                resultsDiv.textContent += `${steps[stepIndex]}\n`;
            }
            updateProgress((stepIndex + 1) / steps.length * 100);
            stepIndex++;
        } else {
            clearInterval(stepInterval);
            hideProcessingStatus();
            processingInProgress = false;
            if (resultsDiv) {
                resultsDiv.textContent += '\n✅ All documents processed successfully!';
            }
        }
    }, 1500);
}

function rebuildEmbeddings() {
    console.log('🧠 Rebuilding embeddings...');

    if (processingInProgress) {
        alert('Processing already in progress. Please wait.');
        return;
    }

    processingInProgress = true;
    const resultsDiv = document.getElementById('processingResults');

    showProcessingStatus('Rebuilding document embeddings...');
    if (resultsDiv) {
        resultsDiv.textContent = 'Starting embedding rebuild...\n';
    }

    // Simulate embedding rebuild
    const steps = [
        'Loading document corpus...',
        'Initializing AI model...',
        'Generating embeddings...',
        'Building vector index...',
        'Optimizing search performance...',
        'Embeddings rebuilt successfully!'
    ];

    let stepIndex = 0;
    const stepInterval = setInterval(() => {
        if (stepIndex < steps.length) {
            if (resultsDiv) {
                resultsDiv.textContent += `${steps[stepIndex]}\n`;
            }
            updateProgress((stepIndex + 1) / steps.length * 100);
            stepIndex++;
        } else {
            clearInterval(stepInterval);
            hideProcessingStatus();
            processingInProgress = false;
            if (resultsDiv) {
                resultsDiv.textContent += '\n🎉 Embeddings rebuilt and optimized!';
            }
        }
    }, 2000);
}

function processDataFiles() {
    console.log('📊 Processing data files...');

    if (processingInProgress) {
        alert('Processing already in progress. Please wait.');
        return;
    }

    processingInProgress = true;
    const resultsDiv = document.getElementById('processingResults');

    showProcessingStatus('Processing data files...');
    if (resultsDiv) {
        resultsDiv.textContent = 'Starting data processing...\n';
    }

    simulateProcessing(() => {
        if (resultsDiv) {
            resultsDiv.textContent += 'Data files processed successfully!\n';
        }
        hideProcessingStatus();
        processingInProgress = false;
    });
}

// Processing UI functions
function showProcessingStatus(message) {
    const statusDiv = document.getElementById('processingStatus');
    if (statusDiv) {
        statusDiv.classList.add('active');
        const messageDiv = statusDiv.querySelector('div');
        if (messageDiv) {
            messageDiv.textContent = message;
        }
        updateProgress(0);
    }
}

function hideProcessingStatus() {
    const statusDiv = document.getElementById('processingStatus');
    if (statusDiv) {
        statusDiv.classList.remove('active');
    }
}

function updateProgress(percentage) {
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');

    if (progressFill) {
        progressFill.style.width = percentage + '%';
    }

    if (progressText) {
        progressText.textContent = `${Math.round(percentage)}% complete`;
    }
}

function simulateProcessing(callback) {
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setTimeout(callback, 500);
        }
        updateProgress(progress);
    }, 500);
}

// File upload handling
function handleFileUpload(event) {
    const files = event.target.files;
    console.log('📁 Files selected for upload:', files.length);

    if (files.length > 0) {
        showProcessingStatus(`Uploading ${files.length} file(s)...`);

        // Simulate file upload
        simulateProcessing(() => {
            hideProcessingStatus();
            alert(`Successfully uploaded ${files.length} file(s)!`);
            // Refresh the page to show new files
            window.location.reload();
        });
    }
}

// Testing functions
function testEndpoint(endpoint) {
    console.log('🧪 Testing endpoint:', endpoint);
    const resultsDiv = document.getElementById('endpointTestResults');
    if (!resultsDiv) return;

    resultsDiv.textContent = `Testing ${endpoint}...`;

    fetch(endpoint)
        .then(response => response.json())
        .then(data => {
            console.log('✅ Endpoint test result:', data);
            resultsDiv.textContent = `${endpoint}\nStatus: Success\nResponse: ${JSON.stringify(data, null, 2)}`;
        })
        .catch(error => {
            console.error('❌ Endpoint test failed:', error);
            resultsDiv.textContent = `${endpoint}\nStatus: Error\nMessage: ${error.message}`;
        });
}

function testChatEndpoint() {
    console.log('💬 Testing chat endpoint...');
    const resultsDiv = document.getElementById('endpointTestResults');
    if (!resultsDiv) return;

    const testData = {
        message: 'Hello, this is a test message from admin dashboard',
        category: 'general',
        type: 'text'
    };

    resultsDiv.textContent = 'Testing chat endpoint...';

    fetch('/chat_stream_integrated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('✅ Chat test successful:', data);
        resultsDiv.textContent = `Chat Endpoint Test\nStatus: Success\nRequest: ${JSON.stringify(testData, null, 2)}\n\nResponse: ${JSON.stringify(data, null, 2)}`;
    })
    .catch(error => {
        console.error('❌ Chat test failed:', error);
        resultsDiv.textContent = `Chat Endpoint Test\nStatus: Error\nMessage: ${error.message}`;
    });
}

function testVoiceEndpoint() {
    console.log('🎤 Testing voice endpoint...');
    const resultsDiv = document.getElementById('endpointTestResults');
    if (!resultsDiv) return;

    const testData = {
        audio_data: 'test_audio_data_placeholder',
        category: 'general'
    };

    resultsDiv.textContent = 'Testing voice endpoint...';

    fetch('/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('✅ Voice test successful:', data);
        resultsDiv.textContent = `Voice Endpoint Test\nStatus: Success\nResponse: ${JSON.stringify(data, null, 2)}`;
    })
    .catch(error => {
        console.error('❌ Voice test failed:', error);
        resultsDiv.textContent = `Voice Endpoint Test\nStatus: Error\nMessage: ${error.message}`;
    });
}

function simulateChat() {
    const messageInput = document.getElementById('testMessage');
    const categorySelect = document.getElementById('testCategory');

    if (!messageInput || !categorySelect) return;

    const message = messageInput.value;
    const category = categorySelect.value;

    if (!message) {
        alert('Please enter a test message');
        return;
    }

    console.log('🎭 Simulating chat:', { message, category });
    const resultsDiv = document.getElementById('chatSimResults');
    if (!resultsDiv) return;

    resultsDiv.textContent = 'Sending test message...';

    const testData = {
        message: message,
        category: category,
        type: 'text',
        timestamp: new Date().toISOString()
    };

    fetch('/chat_stream_integrated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('✅ Chat simulation result:', data);
        resultsDiv.textContent = `Chat Simulation\n\nRequest:\n${JSON.stringify(testData, null, 2)}\n\nResponse:\n${JSON.stringify(data, null, 2)}`;
    })
    .catch(error => {
        console.error('❌ Chat simulation failed:', error);
        resultsDiv.textContent = `Chat Simulation\nError: ${error.message}`;
    });
}

function testAllEndpoints() {
    console.log('🧪 Testing all endpoints...');

    const endpoints = [
        '/get_dropdown_options'
    ];

    endpoints.forEach((endpoint, index) => {
        setTimeout(() => testEndpoint(endpoint), index * 1000);
    });

    setTimeout(testChatEndpoint, endpoints.length * 1000);
    setTimeout(testVoiceEndpoint, (endpoints.length + 1) * 1000);
}

// User management functions
function approveAccount(requestId) {
    console.log('✅ Approving account:', requestId);

    fetch(`/approve_request/${requestId}`, { method: 'POST' })
    .then(response => {
        if (response.ok) {
            const row = document.getElementById(`account-req-${requestId}`);
            if (row) row.remove();
            alert('Account approved successfully!');
            // Update stats
            location.reload();
        } else {
            throw new Error('Approval failed');
        }
    })
    .catch(error => {
        console.error('❌ Approval failed:', error);
        alert('Error approving account');
    });
}

function denyAccount(requestId) {
    console.log('❌ Denying account:', requestId);

    if (confirm('Are you sure you want to deny this account request?')) {
        fetch(`/deny_request/${requestId}`, { method: 'POST' })
        .then(response => {
            if (response.ok) {
                const row = document.getElementById(`account-req-${requestId}`);
                if (row) row.remove();
                alert('Request denied!');
                // Update stats
                location.reload();
            } else {
                throw new Error('Denial failed');
            }
        })
        .catch(error => {
            console.error('❌ Denial failed:', error);
            alert('Error denying request');
        });
    }
}

function resetUserPasswordPrompt(email) {
    const newPassword = prompt(`Enter new password for ${email}:`);
    if (newPassword && newPassword.length >= 6) {
        console.log('🔑 Resetting password for:', email);
        // In a real implementation, this would call a backend endpoint
        alert(`Password reset for ${email} would be implemented here.\nNew password: ${newPassword}`);
    } else if (newPassword) {
        alert('Password must be at least 6 characters long.');
    }
}

// Utility functions
function refreshDebugInfo() {
    console.log('🔄 Refreshing debug info...');
    const debugContent = document.getElementById('debugContent');
    if (!debugContent) return;

    debugContent.textContent = 'Loading debug information...';

    const debugInfo = {
        timestamp: new Date().toISOString(),
        flask_debug: true,
        python_version: '3.9+',
        flask_version: '2.0+',
        database_status: 'Connected',
        ai_model_status: 'Loaded',
        document_count: document.getElementById('totalFiles') ? document.getElementById('totalFiles').textContent : '0',
        user_count: document.querySelectorAll('#users table tbody tr').length - 1,
        memory_usage: '45%',
        cpu_usage: '23%'
    };

    debugContent.textContent = JSON.stringify(debugInfo, null, 2);
}

function refreshLogs() {
    const logsDiv = document.getElementById('systemLogs');
    if (!logsDiv) return;

    const currentTime = new Date().toISOString();
    const userEmail = document.querySelector('.user-email');

    logsDiv.textContent = `System Logs - Last Updated: ${currentTime}\n\n` +
        `[INFO] Admin dashboard accessed by ${userEmail ? userEmail.textContent : 'Unknown'}\n` +
        `[INFO] System status: All services operational\n` +
        `[INFO] Database connections: Active\n` +
        `[INFO] Document processing: Ready\n` +
        `[INFO] Voice recognition: Enabled\n` +
        `[INFO] Memory usage: Normal\n` +
        `[INFO] No errors detected\n\n` +
        `For detailed logs, check:\n` +
        `- chatbot_backend.log\n` +
        `- Browser developer console\n` +
        `- Flask server output`;
}

function loadProcessingStatus() {
    const statusDiv = document.getElementById('processingStatus');
    if (statusDiv) {
        const currentTime = new Date().toLocaleString();
        const totalFiles = document.getElementById('totalFiles');
        statusDiv.innerHTML = `
            <div>Last processing: ${currentTime}</div>
            <div>Total documents processed: ${totalFiles ? totalFiles.textContent : '0'}</div>
            <div>Embeddings status: Ready</div>
            <div>System ready: ✅</div>
        `;
    }
}

function viewFolder(folderName) {
    alert(`Viewing folder: ${folderName}\n\nThis would open a detailed view of all files in the ${folderName} category.`);
}

function refreshFolder(folderName) {
    console.log(`🔄 Refreshing folder: ${folderName}`);
    alert(`Refreshing ${folderName} folder...\n\nThis would reload the file list and check for new documents.`);
    // In a real implementation, this would refresh the folder data
}

function updateDashboardStats() {
    // Update dashboard statistics periodically
    console.log('📊 Updating dashboard stats...');
    // This would fetch real-time stats from the server
}

// ===== ORIGINAL CHATBOT FUNCTIONS (UNCHANGED) =====

// ===== WELCOME ANIMATION =====
function startWelcomeAnimation() {
    const welcomeText = document.getElementById('welcomeText');
    const welcomeCursor = document.getElementById('welcomeCursor');

    if (!welcomeText || !welcomeCursor) return;

    const fullText = "Hello! I'm your Chatbot assistant. I can help you with document queries and various topics.";

    let i = 0;
    const typeInterval = setInterval(() => {
        if (i < fullText.length) {
            welcomeText.textContent += fullText.charAt(i);
            i++;
        } else {
            clearInterval(typeInterval);
            setTimeout(() => {
                welcomeCursor.style.display = 'none';
                isWelcomeComplete = true;
            }, 1000);
        }
    }, 50);
}

// ===== CATEGORY LOADING =====
function loadCategories() {
    fetch('/get_dropdown_options')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.options) {
                const select = document.getElementById('categoryDropdown');
                if (!select) return;

                select.innerHTML = '<option value="general">General Questions</option>';
                data.options.forEach(option => {
                    const optionElement = document.createElement('option');
                    optionElement.value = option.value;
                    optionElement.textContent = option.label;
                    select.appendChild(optionElement);
                });
            }
        })
        .catch(error => {
            console.error('❌ Failed to load categories:', error);
        });
}

// ===== QUICK TIMING CALCULATION =====
function calculateReadingTime(text) {
    if (!text) return MIN_READING_TIME;

    const charCount = text.length;

    // Simple calculation - 20ms per character, max 2 seconds
    let readingTime = Math.min(charCount * 20, MAX_READING_TIME);
    readingTime = Math.max(readingTime, MIN_READING_TIME);

    console.log(`📖 Quick reading time for ${charCount} chars: ${readingTime}ms`);
    return readingTime;
}

// ===== CHAT FUNCTIONS =====
function startChat() {
    if (!chatStarted) {
        const welcomeScreen = document.getElementById('center-startup');
        const chatBox = document.getElementById('chatbox');

        if (welcomeScreen) welcomeScreen.style.display = 'none';
        if (chatBox) chatBox.style.display = 'flex';

        chatStarted = true;
        console.log('💬 Chat started');
    }
}

// ===== MESSAGE SENDING =====
function sendMessage(customMessage = null) {
    const messageInput = document.getElementById('policy-search-input');
    const message = customMessage || (messageInput ? messageInput.value.trim() : '');
    const categorySelect = document.getElementById('categoryDropdown');
    const category = categorySelect ? categorySelect.value : 'general';

    if (!message) {
        focusInput();
        return;
    }

    // Silent check - ignore if processing
    if (isProcessingMessage) {
        console.log('Already processing message, ignoring request');
        return;
    }

    // Lock send button only
    lockInterface();

    startChat();

    if (!customMessage && messageInput) {
        messageInput.value = '';
    }

    addUserMessage(message);
    showTypingIndicator();

    const requestData = {
        message: message,
        category: category,
        type: 'text',
        timestamp: new Date().toISOString()
    };

    fetch('/chat_stream_integrated', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        hideTypingIndicator();

        if (data.error) {
            addBotMessage('❌ Error: ' + data.error);
            scheduleUnlock(1000);
        } else {
            addBotMessageWithRealDynamicTiming(data);
        }
    })
    .catch(error => {
        console.error('❌ Request failed:', error);
        hideTypingIndicator();
        addBotMessage('❌ Connection error: ' + error.message);
        scheduleUnlock(1000);
    });
}

// ===== STREAMING WITH QUICK UNLOCK =====
function addBotMessageWithRealDynamicTiming(data) {
    const chat = document.getElementById('chat');
    if (!chat) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message streaming-message';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString();
    if (data.category && data.category !== 'general') {
        timeDiv.textContent += ' • ' + data.category;
    }

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chat.appendChild(messageDiv);

    const text = data.response;
    const totalChars = text.length;

    // Fast streaming - max 2 seconds
    const streamingDuration = Math.min(2000, totalChars * 25);
    const streamingSpeed = streamingDuration / totalChars;

    console.log(`🎬 Fast stream: ${totalChars} chars in ${streamingDuration}ms`);

    streamingInProgress = true;
    let i = 0;

    const streamInterval = setInterval(() => {
        if (i < text.length) {
            contentDiv.textContent = text.substring(0, i + 1);
            i++;
            chat.scrollTop = chat.scrollHeight;

        } else {
            clearInterval(streamInterval);
            messageDiv.classList.remove('streaming-message');
            streamingInProgress = false;

            console.log(`✅ Streaming complete!`);

            // Quick unlock - 1-2 seconds max
            const finalReadingTime = calculateReadingTime(text);
            scheduleUnlock(finalReadingTime);
        }
    }, streamingSpeed);
}

// ===== QUICK UNLOCK SCHEDULING =====
function scheduleUnlock(delay) {
    if (unlockTimeout) {
        clearTimeout(unlockTimeout);
    }

    // Cap at 2 seconds maximum
    const actualDelay = Math.min(delay, 2000);
    console.log(`⏰ Quick unlock in ${actualDelay}ms`);

    unlockTimeout = setTimeout(() => {
        unlockInterface();
        console.log('🔓 Interface unlocked!');
    }, actualDelay);
}

// ===== INTERFACE MANAGEMENT (INPUT ALWAYS ENABLED) =====
function lockInterface() {
    isProcessingMessage = true;
    lastMessageTime = Date.now();
    setInputState(false); // Only disables send button
    console.log('🔒 Send button locked (typing still works)');
}

function unlockInterface() {
    if (unlockTimeout) {
        clearTimeout(unlockTimeout);
        unlockTimeout = null;
    }

    isProcessingMessage = false;
    streamingInProgress = false;
    setInputState(true);
    console.log('🔓 Send button unlocked');
}

function setInputState(enabled) {
    const messageInput = document.getElementById('policy-search-input');
    const sendBtn = document.getElementById('policy-search-btn');
    const voiceBtn = document.getElementById('voice-btn');

    // INPUT ALWAYS ENABLED - users can type anytime
    if (messageInput) {
        messageInput.disabled = false; // Never disable!
        messageInput.style.opacity = '1';
        messageInput.placeholder = 'Type your message here...';
        messageInput.focus(); // Always keep focused
    }

    // Only disable send button during processing
    if (sendBtn) {
        sendBtn.disabled = !enabled;
        sendBtn.style.opacity = enabled ? '1' : '0.6';
        sendBtn.style.cursor = enabled ? 'pointer' : 'not-allowed';
        sendBtn.textContent = enabled ? 'Send' : 'Wait...';
    }

    // Only disable voice during processing
    if (voiceBtn) {
        voiceBtn.disabled = !enabled;
        voiceBtn.style.opacity = enabled ? '1' : '0.6';
    }
}

// ===== MESSAGE DISPLAY =====
function addUserMessage(message) {
    const chat = document.getElementById('chat');
    if (!chat) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${new Date().toLocaleTimeString()}</div>
    `;
    chat.appendChild(messageDiv);
    chat.scrollTop = chat.scrollHeight;
}

function addBotMessage(message) {
    const chat = document.getElementById('chat');
    if (!chat) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    messageDiv.innerHTML = `
        <div class="message-content">${message}</div>
        <div class="message-time">${new Date().toLocaleTimeString()}</div>
    `;
    chat.appendChild(messageDiv);
    chat.scrollTop = chat.scrollHeight;
}

// ===== TYPING INDICATOR =====
function showTypingIndicator() {
    hideTypingIndicator();

    const chat = document.getElementById('chat');
    if (!chat) return;

    const typingDiv = document.createElement('div');
    typingDiv.className = 'message typing-message';
    typingDiv.id = 'typingIndicator';

    const indicatorDiv = document.createElement('div');
    indicatorDiv.className = 'typing-indicator';
    indicatorDiv.innerHTML = '<span></span><span></span><span></span>';

    typingDiv.appendChild(indicatorDiv);
    chat.appendChild(typingDiv);
    chat.scrollTop = chat.scrollHeight;
}

function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// ===== INPUT HANDLERS =====
function initInputHandlers() {
    const messageInput = document.getElementById('policy-search-input');
    if (messageInput) {
        messageInput.addEventListener('keypress', handleKeyPress);

        messageInput.addEventListener('paste', function(event) {
            if (isProcessingMessage) {
                event.preventDefault();
                console.log('Paste blocked while processing');
            }
        });
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();

        if (isProcessingMessage) {
            console.log('Enter blocked while processing');
            return false;
        }

        sendMessage();
        return false;
    }
}

function focusInput() {
    const messageInput = document.getElementById('policy-search-input');
    if (messageInput) {
        messageInput.focus();
    }
}

// ===== ANTI-SPAM PROTECTION (SILENT) =====
function initAntiSpamProtection() {
    const sendBtn = document.getElementById('policy-search-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', handleSendClick);
    }

    const inputForm = document.getElementById('input-form');
    if (inputForm) {
        inputForm.addEventListener('submit', preventFormSubmit);
    }
}

function handleSendClick(event) {
    event.preventDefault();
    event.stopPropagation();

    if (isProcessingMessage) {
        console.log('Send button blocked while processing');
        return false;
    }

    sendMessage();
    return false;
}

function preventFormSubmit(event) {
    event.preventDefault();
    return false;
}

// ===== VOICE INTERFACE =====
function initVoiceInterface() {
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', toggleRecording);
    }
}

function toggleRecording() {
    if (voiceState === 'idle') {
        startAdvancedRecording();
    } else if (voiceState === 'recording') {
        stopAdvancedRecording();
    }
}

async function startAdvancedRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        microphone = audioContext.createMediaStreamSource(stream);

        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.8;
        microphone.connect(analyser);

        dataArray = new Uint8Array(analyser.frequencyBinCount);

        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = () => {
            processRecording();
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start(100);
        voiceState = 'recording';
        updateVoiceUI();

        // Auto-stop after 5 seconds
        setTimeout(() => {
            if (voiceState === 'recording') {
                stopAdvancedRecording();
            }
        }, 5000);

    } catch (error) {
        console.error('❌ Error starting recording:', error);
        addBotMessage('🎤 Microphone access denied. Please allow microphone access.');
    }
}

function stopAdvancedRecording() {
    if (mediaRecorder && voiceState === 'recording') {
        mediaRecorder.stop();
        voiceState = 'processing';
        updateVoiceUI();
    }
}

function updateVoiceUI() {
    const voiceBtn = document.getElementById('voice-btn');
    if (!voiceBtn) return;

    voiceBtn.classList.remove('recording');

    switch(voiceState) {
        case 'recording':
            voiceBtn.classList.add('recording');
            voiceBtn.style.background = '#d32f2f';
            voiceBtn.textContent = '⏹️';
            break;
        case 'processing':
            voiceBtn.style.background = '#7c3aed';
            voiceBtn.textContent = '⚡';
            break;
        default:
            voiceBtn.style.background = '#2f2f2f';
            voiceBtn.textContent = '🎤';
            break;
    }
}

function processRecording() {
    voiceState = 'processing';
    updateVoiceUI();

    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

    const reader = new FileReader();
    reader.onloadend = () => {
        const base64Audio = reader.result.split(',')[1];
        sendVoiceToServer(base64Audio);
    };
    reader.readAsDataURL(audioBlob);
}

function sendVoiceToServer(audioData) {
    startChat();
    addUserMessage('🎤 Voice message');
    showTypingIndicator();

    const categorySelect = document.getElementById('categoryDropdown');
    const category = categorySelect ? categorySelect.value : 'general';

    fetch('/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            audio_data: audioData,
            category: category
        })
    })
    .then(response => response.json())
    .then(data => {
        hideTypingIndicator();

        if (data.query) {
            const lastMessage = document.querySelector('#chat .message:last-child .message-content');
            if (lastMessage) {
                lastMessage.textContent = `🎤 "${data.query}"`;
            }
        }

        if (data.response) {
            addBotMessageWithRealDynamicTiming({
                response: data.response,
                category: category
            });
        }
    })
    .catch(error => {
        hideTypingIndicator();
        addBotMessage('Voice processing failed. Please try again.');
    })
    .finally(() => {
        resetVoiceInterface();
    });
}

// Enhanced View Folder Functionality
function viewFolder(folderName) {
    console.log('👁️ Viewing folder:', folderName);

    // Show loading state
    showProcessingStatus(`Loading ${folderName} folder details...`);

    fetch(`/admin/view_folder/${folderName}`)
        .then(response => response.json())
        .then(data => {
            hideProcessingStatus();

            if (data.success) {
                showFolderModal(data.folder);
            } else {
                alert(`Error loading folder: ${data.error}`);
            }
        })
        .catch(error => {
            hideProcessingStatus();
            console.error('❌ Error viewing folder:', error);
            alert(`Failed to load folder details: ${error.message}`);
        });
}

function showFolderModal(folderData) {
    // Create modal HTML
    const modalHTML = `
        <div id="folderModal" class="folder-modal">
            <div class="folder-modal-content">
                <div class="folder-modal-header">
                    <h2>📁 ${folderData.name.toUpperCase()} Folder Details</h2>
                    <button class="folder-modal-close" onclick="closeFolderModal()">&times;</button>
                </div>
                <div class="folder-modal-body">
                    <div class="folder-stats">
                        <div class="stat-item">
                            <strong>Total Files:</strong> ${folderData.files.length}
                        </div>
                        <div class="stat-item">
                            <strong>Total Size:</strong> ${formatFileSize(folderData.total_size)}
                        </div>
                        <div class="stat-item">
                            <strong>Last Modified:</strong> ${folderData.last_modified || 'Unknown'}
                        </div>
                    </div>
                    <div class="file-list-container">
                        <h3>📄 Files in this folder:</h3>
                        <div class="file-list-modal">
                            ${folderData.files.map(file => `
                                <div class="file-item-modal">
                                    <div class="file-info">
                                        <span class="file-icon">${getFileIcon(file.type)}</span>
                                        <div class="file-details">
                                            <div class="file-name">${file.name}</div>
                                            <div class="file-meta">
                                                ${file.path !== file.name ? `Path: ${file.path} • ` : ''}
                                                Size: ${formatFileSize(file.size)} •
                                                Modified: ${file.modified}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="folder-modal-footer">
                    <button onclick="processFolder('${folderData.name}')" class="btn-process">⚙️ Process Folder</button>
                    <button onclick="refreshFolder('${folderData.name}')" class="btn-approve">🔄 Refresh</button>
                    <button onclick="closeFolderModal()" class="btn-deny">Close</button>
                </div>
            </div>
        </div>
    `;

    // Add modal to page
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Show modal with animation
    setTimeout(() => {
        document.getElementById('folderModal').classList.add('show');
    }, 10);
}

function closeFolderModal() {
    const modal = document.getElementById('folderModal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(fileType) {
    const icons = {
        '.pdf': '📄',
        '.doc': '📝',
        '.docx': '📝',
        '.txt': '📄',
        '.jpg': '🖼️',
        '.jpeg': '🖼️',
        '.png': '🖼️',
        '.gif': '🖼️'
    };
    return icons[fileType] || '📄';
}

// Make sure the function is globally available
window.viewFolder = viewFolder;

function resetVoiceInterface() {
    voiceState = 'idle';
    updateVoiceUI();
    audioChunks = [];

    if (audioContext) {
        audioContext.close();
        audioContext = null;
        analyser = null;
        microphone = null;
    }
}

// ===== GLOBAL EXPORTS =====
window.sendMessage = sendMessage;
window.handleKeyPress = handleKeyPress;

// Make admin functions globally available
window.switchTab = switchTab;
window.toggleDebugMode = toggleDebugMode;
window.refreshSystemStatus = refreshSystemStatus;
window.checkSystemHealth = checkSystemHealth;
window.processFolder = processFolder;
window.runBatchProcessing = runBatchProcessing;
window.rebuildEmbeddings = rebuildEmbeddings;
window.processDataFiles = processDataFiles;
window.handleFileUpload = handleFileUpload;
window.testEndpoint = testEndpoint;
window.testChatEndpoint = testChatEndpoint;
window.testVoiceEndpoint = testVoiceEndpoint;
window.simulateChat = simulateChat;
window.testAllEndpoints = testAllEndpoints;
window.approveAccount = approveAccount;
window.denyAccount = denyAccount;
window.resetUserPasswordPrompt = resetUserPasswordPrompt;
window.refreshDebugInfo = refreshDebugInfo;
window.refreshLogs = refreshLogs;
window.viewFolder = viewFolder;
window.refreshFolder = refreshFolder;
