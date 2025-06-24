// --- Configuration ---
const WEBSOCKET_URL = "ws://127.0.0.1:9001";

// --- DOM Elements ---
const statusElement = document.getElementById('connection-status');
const logBox = document.getElementById('log-box');
const statsGrid = document.getElementById('stats-grid');
const resetButton = document.getElementById('reset-button');

// --- State Management ---
// This will hold the data, e.g., stats['Rust']['matrix_multiplication'] = { runs: 123, ... }
let stats = {};
const LANGUAGES = ["Python", "Ruby", "Java", "Rust"];
const ALGORITHMS = [
    "array_sort", "fibonacci", "game_of_life",
    "matrix_multiplication", "prime_factors", "is_leap_year"
];

/**
 * Adds a message to the on-screen log panel.
 * @param {string} message - The message to log.
 * @param {string} level - 'info', 'error', or 'warn'.
 */
function logMessage(message, level = 'info') {
    const log = document.createElement('div');
    log.className = `log-message ${level}`;
    log.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logBox.appendChild(log);
    // Auto-scroll to the bottom
    logBox.scrollTop = logBox.scrollHeight;
}


/**
 * Initializes the statistics data structure and UI grid.
 */
function initializeState() {
    // Clear existing data and UI
    stats = {};
    statsGrid.innerHTML = '';

    LANGUAGES.forEach(lang => {
        stats[lang] = {};

        const card = document.createElement('div');
        card.className = 'lang-card';
        card.id = `card-${lang.toLowerCase()}`;

        let algoHtml = '';
        ALGORITHMS.forEach(algo => {
            // Initialize stats object for each algorithm
            stats[lang][algo] = { runs: 0, total_duration: 0 };

            // Create the HTML structure for each algorithm's stats display
            algoHtml += `
                <div class="algo-stat" id="stat-${lang.toLowerCase()}-${algo}">
                    <span class="algo-name">${algo}</span>
                    <span class="algo-runs">0</span>
                </div>
            `;
        });

        card.innerHTML = `<h2>${lang}</h2><div class="algo-list">${algoHtml}</div>`;
        statsGrid.appendChild(card);
    });
    logMessage("Dashboard reset and initialized.", "info");
}


/**
 * Handles incoming WebSocket messages from the orchestrator.
 * @param {MessageEvent} event - The event containing the message data.
 */
function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);

        // Log every raw message for debugging purposes
        console.log("Received data:", data);

        // Check the message type to distinguish between stats and status updates
        if (data.type === 'status') {
            logMessage(`[STATUS] ${data.message}`, data.level);
        } else {
            // This is a benchmark result, so update our stats
            const { lang, algo, duration } = data;

            // Update the in-memory state
            if (stats[lang] && stats[lang][algo]) {
                stats[lang][algo].runs++;
                stats[lang][algo].total_duration += duration;

                // Update the UI
                const runElement = document.querySelector(`#stat-${lang.toLowerCase()}-${algo} .algo-runs`);
                if (runElement) {
                    runElement.textContent = stats[lang][algo].runs;
                }
            }
        }

    } catch (error) {
        logMessage(`Error parsing message: ${error}`, 'error');
        console.error("Failed to parse WebSocket message:", error);
    }
}


/**
 * Main function to set up WebSocket connection and event listeners.
 */
function connect() {
    logMessage("Attempting to connect to orchestrator...");
    const socket = new WebSocket(WEBSOCKET_URL);

    socket.onopen = () => {
        statusElement.textContent = '● Connected';
        statusElement.className = 'connected';
        logMessage('Successfully connected to WebSocket server.', 'info');
    };

    socket.onmessage = handleWebSocketMessage;

    socket.onclose = () => {
        statusElement.textContent = '● Disconnected';
        statusElement.className = 'disconnected';
        logMessage('Connection closed. Attempting to reconnect in 3 seconds...', 'warn');
        setTimeout(connect, 3000); // Attempt to reconnect after a delay
    };

    socket.onerror = (error) => {
        logMessage(`WebSocket error: An error occurred. Check browser console for details.`, 'error');
        console.error('WebSocket Error:', error);
        socket.close(); // This will trigger the onclose event for reconnection logic
    };
}

// --- Event Listeners ---
resetButton.addEventListener('click', initializeState);

// --- Initial Setup ---
document.addEventListener('DOMContentLoaded', () => {
    initializeState();
    connect();
});
