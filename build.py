# build_ui.py
import os
import json

try:
    with open("config.json", "r") as f:
        config = json.load(f)
    UI_DIR = config["ui"]["directory"]
except FileNotFoundError:
    print("Error: config.json not found, using default UI directory 'ui'")
    UI_DIR = "ui"
except (KeyError, json.JSONDecodeError) as e:
    print(f"Error: Invalid config.json, using default UI directory 'ui': {str(e)}")
    UI_DIR = "ui"

os.makedirs(UI_DIR, exist_ok=True)
os.makedirs(os.path.join(UI_DIR, "image"), exist_ok=True)  # Ensure image directory

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Microservice UI</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <h1>AI Microservice Query</h1>
        <div id="history" class="history"></div>
        <div class="input-section">
            <select id="service-select">
                <option value="" disabled selected>Select a service</option>
            </select>
            <div id="dynamic-selectors" class="dynamic-selectors"></div>
            <input type="text" id="query-input" placeholder="Enter your query">
            <button id="submit-btn">Submit</button>
        </div>
    </div>
    <script src="script.js"></script>
</body>
</html>
"""

STYLES_CSS = """body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f4f4f4;
}

.container {
    max-width: 800px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
}

h1 {
    text-align: center;
    color: #333;
}

.history {
    min-height: 200px;
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 10px;
    margin-bottom: 20px;
    background-color: #fafafa;
}

.history-entry {
    margin-bottom: 10px;
    padding: 10px;
    border-radius: 4px;
}

.history-entry.request {
    background-color: #e6f3ff;
}

.history-entry.response {
    background-color: #e6ffe6;
}

.history-entry.error {
    background-color: #ffe6e6;
}

.history-entry img {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin-top: 5px;
}

.input-section {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
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
    border: 1px solid #ccc;
    border-radius: 4px;
}

.dynamic-selectors label {
    font-size: 14px;
    margin-right: 5px;
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
}

#service-select, #query-input {
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
}

#query-input {
    flex: 1;
}

#submit-btn {
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}

#submit-btn:hover {
    background-color: #0056b3;
}
"""

SCRIPT_JS = """document.addEventListener('DOMContentLoaded', async () => {
    const serviceSelect = document.getElementById('service-select');
    const dynamicSelectors = document.getElementById('dynamic-selectors');
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('submit-btn');
    const historyDiv = document.getElementById('history');
    let config = {};
    let serverUrl = 'http://localhost:8000';

    async function fetchWithRetry(url, options, retries = 3, delay = 1000) {
        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(url, options);
                if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                return response;
            } catch (error) {
                console.error(`Fetch attempt ${i+1} failed for ${url}: ${error.message}`);
                if (i === retries - 1) {
                    addToHistory(`Error: ${error.message} for ${url}`, 'error');
                    throw error;
                }
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }

    try {
        const configResponse = await fetchWithRetry('http://localhost:8000/config', { method: 'GET' });
        config = await configResponse.json();
        serverUrl = `http://${config.server.host}:${config.server.port}`;
        console.log(`Server URL: ${serverUrl}`);
    } catch (error) {
        console.error(`Config fetch error: ${error.message}`);
        addToHistory(`Error: Failed to load config - ${error.message}`, 'error');
    }

    try {
        const response = await fetchWithRetry(`${serverUrl}/services`, { method: 'GET' });
        const data = await response.json();
        console.log(`Services fetched: ${data.services}`);
        if (!data.services.length) {
            addToHistory('Error: No services available', 'error');
        }
        data.services.forEach(service => {
            const option = document.createElement('option');
            option.value = service;
            option.textContent = service.replace(/-/g, ' ').toUpperCase();
            serviceSelect.appendChild(option);
        });
    } catch (error) {
        console.error(`Services fetch error: ${error.message}`);
        addToHistory(`Error: Failed to load services - ${error.message}`, 'error');
    }

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
            const response = await fetch(serverUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

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
                        const lines = chunk.split('\\n\\n');
                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    console.log(`Parsed SSE event: ${JSON.stringify(data)}`);
                                    if (data.result) {
                                        if (!responseEntry) {
                                            responseEntry = document.createElement('div');
                                            responseEntry.className = 'history-entry response';
                                            historyDiv.insertBefore(responseEntry, historyDiv.firstChild);
                                        }
                                        if (data.type === 'image') {
                                            const img = document.createElement('img');
                                            img.src = data.result;
                                            img.alt = 'Generated image';
                                            responseEntry.innerHTML = '';
                                            responseEntry.appendChild(img);
                                        } else {
                                            responseEntry.textContent = `Response: ${data.result}`;
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
                if (data.type === 'image') {
                    const entry = document.createElement('div');
                    entry.className = 'history-entry response';
                    const img = document.createElement('img');
                    img.src = data.result;
                    img.alt = 'Generated image';
                    entry.appendChild(img);
                    historyDiv.insertBefore(entry, historyDiv.firstChild);
                } else {
                    addToHistory(`Response: ${data.result || JSON.stringify(data)}`, 'response');
                }
            }
        } catch (error) {
            console.log(`Request error: ${error.message}`);
            addToHistory(`Error: ${error.message}`, 'error');
        }

        queryInput.value = '';
    });

    function addToHistory(message, type) {
        const entry = document.createElement('div');
        entry.className = `history-entry ${type}`;
        entry.textContent = message;
        historyDiv.insertBefore(entry, historyDiv.firstChild);
        while (historyDiv.children.length > 50) {
            historyDiv.removeChild(historyDiv.lastChild);
        }
        historyDiv.scrollTop = 0;
    }
});
"""

def write_file(filepath, content):
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Generated {filepath}")

def build_ui():
    write_file(os.path.join(UI_DIR, "index.html"), INDEX_HTML)
    write_file(os.path.join(UI_DIR, "styles.css"), STYLES_CSS)
    write_file(os.path.join(UI_DIR, "script.js"), SCRIPT_JS)

if __name__ == "__main__":
    build_ui()