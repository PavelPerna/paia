import os
import json
from ai import PAIAConfig, PAIALogger

# Initialize logger and config via global singletons
logger = PAIALogger().getLogger()
config = PAIAConfig().getConfig()
UI_DIR = PAIAConfig().ui_dir

os.makedirs(UI_DIR, exist_ok=True)
os.makedirs(os.path.join(UI_DIR, "image"), exist_ok=True)

INDEX_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PAIA - AI Microservice UI</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container" id="container">
        <div class="header">
            <h1>PAIA AI Microservice</h1>
            <div class="header-buttons">
                <button id="theme-toggle" title="Toggle Dark/Light Mode">🌙</button>
                <button id="fullscreen-toggle" title="Toggle Fullscreen/Window">⛶</button>
            </div>
        </div>
        <div id="history" class="history"></div>
        <div class="input-section">
            <select id="service-select">
                <option value="" disabled selected>Select a service</option>
            </select>
            <div id="dynamic-selectors" class="dynamic-selectors"></div>
            <div class="query-container">
                <input type="text" id="query-input" placeholder="Enter your query">
            </div>
            <button id="submit-btn">Submit</button>
        </div>
    </div>
    <script type="module" src="api.js"></script>
    <script type="module" src="script.js"></script>
</body>
</html>
"""

STYLES_CSS = """:root {
    --background-color: #f4f4f4;
    --container-bg: white;
    --text-color: #333;
    --border-color: #ccc;
    --request-bg: #e6f3ff;
    --response-bg: #e6ffe6;
    --error-bg: #ffe6e6;
    --button-bg: #007bff;
    --button-hover-bg: #0056b3;
    --play-btn-bg: #28a745;
    --play-btn-hover-bg: #218838;
    --mic-btn-bg: #007bff;
    --mic-btn-hover-bg: #0056b3;
    --mic-btn-recording-bg: #dc3545;
    --mic-btn-recording-hover-bg: #c82333;
    --fullscreen-btn-bg: #6c757d;
    --fullscreen-btn-hover-bg: #5a6268;
}

[data-theme="dark"] {
    --background-color: #1a1a1a;
    --container-bg: #2c2c2c;
    --text-color: #e0e0e0;
    --border-color: #555;
    --request-bg: #2a3f5f;
    --response-bg: #2f5f2a;
    --error-bg: #5f2a2a;
    --button-bg: #1e90ff;
    --button-hover-bg: #1c86ee;
    --play-btn-bg: #2ecc71;
    --play-btn-hover-bg: #27ae60;
    --mic-btn-bg: #1e90ff;
    --mic-btn-hover-bg: #1c86ee;
    --mic-btn-recording-bg: #ff5555;
    --mic-btn-recording-hover-bg: #ff3333;
    --fullscreen-btn-bg: #adb5bd;
    --fullscreen-btn-hover-bg: #909296;
}

body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: var(--background-color);
    color: var(--text-color);
}
.content-wide{
    max-width: 100%;
}
.content-narrow{
    max-width: 800px;
}
.container {
    margin: 0 auto;
    background: var(--container-bg);
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.header-buttons {
    display: flex;
    gap: 10px;
}

#theme-toggle, #fullscreen-toggle {
    padding: 8px 12px;
    background-color: var(--button-bg);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

#theme-toggle:hover {
    background-color: var(--button-hover-bg);
}

#fullscreen-toggle {
    background-color: var(--fullscreen-btn-bg);
}

#fullscreen-toggle:hover {
    background-color: var(--fullscreen-btn-hover-bg);
}

h1 {
    text-align: center;
    color: var(--text-color);
    margin: 0;
}

.history {
    min-height: 200px;
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid var(--border-color);
    padding: 10px;
    margin-bottom: 20px;
    background-color: var(--container-bg);
}

.history-entry {
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.history-entry.request {
    background-color: var(--request-bg);
}

.history-entry.response {
    background-color: var(--response-bg);
}

.history-entry.error {
    background-color: var(--error-bg);
}

.history-entry img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin-top: 5px;
}

.history-entry audio {
    max-width: 100%;
    margin-top: 5px;
}

.history-entry .play-btn {
    padding: 5px 10px;
    background-color: var(--play-btn-bg);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

.history-entry .play-btn:hover {
    background-color: var(--play-btn-hover-bg);
}

.input-section {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.dynamic-selectors {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.dynamic-selectors select,
.dynamic-selectors input[type="text"],
.dynamic-selectors input[type="range"],
.dynamic-selectors textarea {
    padding: 10px;
    font-size: 16px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--container-bg);
    color: var(--text-color);
}

.dynamic-selectors select:focus,
.dynamic-selectors input[type="text"]:focus,
.dynamic-selectors input[type="range"]:focus,
.dynamic-selectors textarea:focus {
    outline: none;
    border-color: var(--button-bg);
}

.dynamic-selectors label {
    font-size: 14px;
    margin-right: 5px;
    color: var(--text-color);
}

.slider-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

.slider-value {
    font-size: 14px;
    width: 60px;
    text-align: right;
    color: var(--text-color);
}

#service-select {
    padding: 10px;
    font-size: 16px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--container-bg);
    color: var(--text-color);
}

#service-select:focus {
    outline: none;
    border-color: var(--button-bg);
}

.query-container {
    display: flex;
    gap: 10px;
    align-items: center;
}

#query-input {
    flex: 1;
    padding: 10px;
    font-size: 16px;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background-color: var(--container-bg);
    color: var(--text-color);
}

#query-input:focus {
    outline: none;
    border-color: var(--button-bg);
}

#file-upload {
    padding: 10px;
}

#mic-btn {
    padding: 10px;
    background-color: var(--mic-btn-bg);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

#mic-btn.recording {
    background-color: var(--mic-btn-recording-bg);
}

#mic-btn:hover {
    background-color: var(--mic-btn-hover-bg);
}

#mic-btn.recording:hover {
    background-color: var(--mic-btn-recording-hover-bg);
}

#submit-btn {
    padding: 10px 20px;
    background-color: var(--button-bg);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

#submit-btn:hover {
    background-color: var(--button-hover-bg);
}
"""

API_JS = """// ui/api.js
export async function fetchServices(serverUrl) {
    try {
        const response = await fetchWithRetry(`${serverUrl}/services`, { method: 'GET' });
        const data = await response.json();
        console.log(`Services fetched: ${data.services}`);
        return data.services;
    } catch (error) {
        console.error(`Services fetch error: ${error.message}`);
        throw error;
    }
}

export async function fetchConfig(serverUrl) {
    try {
        const response = await fetchWithRetry(`${serverUrl}/config`, { method: 'GET' });
        const data = await response.json();
        console.log(`Config fetched: ${JSON.stringify(data)}`);
        return data;
    } catch (error) {
        console.error(`Config fetch error: ${error.message}`);
        throw error;
    }
}

export async function queryService(serverUrl, payload) {
    try {
        const response = await fetch(serverUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response;
    } catch (error) {
        console.error(`Query error: ${error.message}`);
        throw error;
    }
}

async function fetchWithRetry(url, options, retries = 3, delay = 1000) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            return response;
        } catch (error) {
            console.error(`Fetch attempt ${i+1} failed for ${url}: ${error.message}`);
            if (i === retries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
}
"""

SCRIPT_JS = """// ui/script.js
import { fetchServices, fetchConfig, queryService } from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    const serviceSelect = document.getElementById('service-select');
    const dynamicSelectors = document.getElementById('dynamic-selectors');
    const queryInput = document.getElementById('query-input');
    const micBtn = document.getElementById('mic-btn');
    const submitBtn = document.getElementById('submit-btn');
    const historyDiv = document.getElementById('history');
    const themeToggle = document.getElementById('theme-toggle');
    const fullscreenToggle = document.getElementById('fullscreen-toggle');
    let config = {};
    let serverUrl = 'http://localhost:8000';
    let recognition = null;
    let isRecording = false;

    // Theme Toggle Handler
    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
        localStorage.setItem('theme', theme);
    };

    // Load saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);

    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    // Fullscreen Toggle Handler
    const setFullscreen = (isFullscreen) => {
        const content_element = document.getElementById("container");
        if (isFullscreen) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error(`Fullscreen error: ${err.message}`);
                addToHistory(`Error: Failed to enter fullscreen - ${err.message}`, 'error');
            });
            fullscreenToggle.textContent = '🗕';
            fullscreenToggle.title = 'Exit Fullscreen';
            content_element.setAttribute('class', 'container content-wide');
        } else {
            document.exitFullscreen().catch(err => {
                console.error(`Exit fullscreen error: ${err.message}`);
                addToHistory(`Error: Failed to exit fullscreen - ${err.message}`, 'error');
            });
            fullscreenToggle.textContent = '⛶';
            fullscreenToggle.title = 'Enter Fullscreen';
            content_element.setAttribute('class', 'container content-narrow');
        }
    };

    fullscreenToggle.addEventListener('click', () => {
        const isFullscreen = document.fullscreenElement !== null;
        setFullscreen(!isFullscreen);
    });

    // Update button state when fullscreen changes
    document.addEventListener('fullscreenchange', () => {
        const isFullscreen = document.fullscreenElement !== null;
        fullscreenToggle.textContent = isFullscreen ? '🗕' : '⛶';
        fullscreenToggle.title = isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen';
        const content_element = document.getElementById("container");
        content_element.setAttribute('class', isFullscreen ? 'container content-wide' : 'container content-narrow');
    });

    // Load Config and Services
    try {
        config = await fetchConfig(serverUrl);
        serverUrl = `http://${config.server.host}:${config.server.port}`;
    } catch (error) {
        addToHistory(`Error: Failed to load config - ${error.message}`, 'error');
    }

    try {
        const services = await fetchServices(serverUrl);
        if (!services.length) {
            addToHistory('Error: No services available', 'error');
        }
        services.forEach(service => {
            const option = document.createElement('option');
            option.value = service;
            option.textContent = service.replace(/-/g, ' ').toUpperCase();
            serviceSelect.appendChild(option);
        });
    } catch (error) {
        addToHistory(`Error: Failed to load services - ${error.message}`, 'error');
    }

    // Service Selection Handler
    serviceSelect.addEventListener('change', () => {
        dynamicSelectors.innerHTML = '';
        const service = serviceSelect.value;
        const serviceConfig = config.services?.[service]?.parameters || [];

        serviceConfig.forEach(param => {
            const container = document.createElement('div');
            const label = document.createElement('label');
            label.textContent = param.label;
            label.htmlFor = param.name;

            if (param.type === 'select') {
                const select = document.createElement('select');
                select.id = param.name;
                select.className = 'dynamic-selector';
                param.options.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt.value;
                    option.textContent = opt.label;
                    select.appendChild(option);
                });
                container.appendChild(label);
                container.appendChild(select);
            } else if (param.type === 'text') {
                const input = document.createElement('input');
                input.type = 'text';
                input.id = param.name;
                input.className = 'dynamic-selector';
                input.placeholder = param.placeholder || '';
                container.appendChild(label);
                container.appendChild(input);
            } else if (param.type === 'textbox') {
                const textarea = document.createElement('textarea');
                textarea.id = param.name;
                textarea.className = 'dynamic-selector';
                textarea.placeholder = param.placeholder || '';
                textarea.rows = param.rows || 4;
                container.appendChild(label);
                container.appendChild(textarea);
            } else if (param.type === 'slider') {
                const sliderContainer = document.createElement('div');
                sliderContainer.className = 'slider-container';
                const slider = document.createElement('input');
                slider.type = 'range';
                slider.id = param.name;
                slider.className = 'dynamic-selector';
                slider.min = param.min;
                slider.max = param.max;
                slider.step = param.step;
                slider.value = param.value;
                const valueDisplay = document.createElement('span');
                valueDisplay.className = 'slider-value';
                valueDisplay.textContent = slider.value;
                slider.addEventListener('input', () => {
                    valueDisplay.textContent = slider.value;
                });
                sliderContainer.appendChild(label);
                sliderContainer.appendChild(slider);
                sliderContainer.appendChild(valueDisplay);
                container.appendChild(sliderContainer);
            }

            dynamicSelectors.appendChild(container);
        });
    });

    // Submit Handler
    submitBtn.addEventListener('click', async () => {
        const service = serviceSelect.value;
        const queryText = queryInput.value.trim();

        if (!service) {
            alert('Please select a service');
            return;
        }

        if (!queryText) {
            alert('Please enter a query');
            return;
        }

        addToHistory(`Request: ${service} - ${queryText}`, 'request');

        const payload = {
            service: service,
            query: { text: queryText },
            stream: config.services?.[service]?.streamable || false
        };

        const serviceConfig = config.services?.[service]?.parameters || [];
        serviceConfig.forEach(param => {
            const element = document.getElementById(param.name);
            if (element) {
                payload.query[param.name] = param.type === 'slider' ? parseFloat(element.value) : element.value;
            }
        });

        console.log(`Sending payload: ${JSON.stringify(payload)}`);

        try {
            const response = await queryService(serverUrl, payload);

            if (payload.stream) {
                console.log(`Initiating streaming for ${service}`);
                const reader = response.body.getReader();
                let responseEntry = null;

                const readStream = async () => {
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) {
                            console.log('Stream ended');
                            break;
                        }

                        const chunk = new TextDecoder().decode(value);
                        console.log(`Received chunk: ${chunk}`);
                        const lines = chunk.split("\\n\\n");
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    console.log(`Parsed SSE event: ${JSON.stringify(data)}`);
                                    if (data.result) {
                                        if (!responseEntry) {
                                            responseEntry = createResponseEntry(data);
                                            historyDiv.insertBefore(responseEntry, historyDiv.firstChild);
                                        } else if (data.type !== 'audio') {
                                            responseEntry.querySelector('.response-text').textContent = `Response: ${data.result}`;
                                        }
                                        historyDiv.scrollTop = 0;
                                        console.log(`Displayed: ${data.result}`);
                                    } else if (data.error) {
                                        addToHistory(`Error: ${data.error}`, 'error');
                                        break;
                                    }
                                } catch (e) {
                                    console.log(`Error parsing SSE event: ${e.message}`);
                                    addToHistory(`Error: Failed to parse stream data - ${e.message}`, 'error');
                                }
                            }
                        }
                    }
                };

                readStream().catch(error => {
                    console.log(`Stream error: ${error.message}`);
                    addToHistory(`Error: Streaming failed - ${error.message}`, 'error');
                });
            } else {
                const data = await response.json();
                const entry = createResponseEntry(data);
                historyDiv.insertBefore(entry, historyDiv.firstChild);
            }
        } catch (error) {
            console.log(`Request error: ${error.message}`);
            addToHistory(`Error: ${error.message}`, 'error');
        }

        // Conditionally clear form based on service-specific or global config
        const shouldClearForm = config.services?.[service]?.clear_form_after_query !== undefined
            ? config.services[service].clear_form_after_query
            : config.ui?.clear_form_after_query !== undefined
            ? config.ui.clear_form_after_query
            : true; // Default to true if not specified
        if (shouldClearForm) {
            queryInput.value = '';
            dynamicSelectors.innerHTML = '';
        }
    });

    function createResponseEntry(data) {
        const text = data.result || JSON.stringify(data);
        const entry = document.createElement('div');
        entry.className = 'history-entry response';
        switch (data.type || "text") {
            case 'image':
                const img = document.createElement('img');
                img.className = 'response-image';
                img.src = data.result;
                entry.appendChild(img);
                break;
            case 'audio':
                const audio = document.createElement('audio');
                audio.className = 'response-audio';
                audio.controls = true;
                audio.autoplay = true;
                audio.src = data.result;
                entry.appendChild(audio);
                break;
            default:
                const textSpan = document.createElement('span');
                textSpan.className = 'response-text';
                textSpan.textContent = `Response: ${text}`;
                const playBtn = document.createElement('button');
                playBtn.className = 'play-btn';
                playBtn.textContent = '▶';
                playBtn.title = 'Play response';
                playBtn.addEventListener('click', () => {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'en-US';
                    window.speechSynthesis.speak(utterance);
                });
                entry.appendChild(textSpan);
                entry.appendChild(playBtn);
                break;
        }

        return entry;
    }

    function addToHistory(message, type) {
        const entry = document.createElement('div');
        entry.className = `history-entry ${type}`;
        entry.textContent = message;
        historyDiv.insertBefore(entry, historyDiv.firstChild);
        historyDiv.scrollTop = 0;
    }
});
"""

def write_file(filepath, content):
    logger.info(f"Generating {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def build_ui():
    write_file(os.path.join(UI_DIR, "index.html"), INDEX_HTML)
    write_file(os.path.join(UI_DIR, "styles.css"), STYLES_CSS)
    write_file(os.path.join(UI_DIR, "api.js"), API_JS)
    write_file(os.path.join(UI_DIR, "script.js"), SCRIPT_JS)
   

if __name__ == "__main__":
    build_ui()