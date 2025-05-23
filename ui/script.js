document.addEventListener('DOMContentLoaded', async () => {
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
                        const lines = chunk.split('\n\n');
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
