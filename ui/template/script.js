// ui/script.js
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
                        const lines = chunk.split("\n\n");
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
                                            responseEntry.querySelector('.markdown-content').innerHTML = marked.parse(data.result);
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
            if (length(dynamicSelectors) > 0){
                dynamicSelectors.forEach( 
                    selector =>{
                        selector.value = '';
                    }
                )
            }
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
                const textDiv = document.createElement('div');
                textDiv.className = 'markdown-content';
                textDiv.innerHTML = marked.parse(text); // Parse Markdown to HTML
                const playBtn = document.createElement('button');
                playBtn.className = 'play-btn';
                playBtn.textContent = '▶';
                playBtn.title = 'Play response';
                playBtn.addEventListener('click', () => {
                    const utterance = new SpeechSynthesisUtterance(text);
                    utterance.lang = 'en-US';
                    window.speechSynthesis.speak(utterance);
                });
                entry.appendChild(textDiv);
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