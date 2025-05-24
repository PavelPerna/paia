// ui/script.js
import { fetchServices, fetchConfig, queryService } from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
    const serviceSelect = document.getElementById('service-select');
    const dynamicSelectors = document.getElementById('dynamic-selectors');
    const queryInput = document.getElementById('query-input');
    const fileUpload = document.getElementById('file-upload');
    const micBtn = document.getElementById('mic-btn');
    const submitBtn = document.getElementById('submit-btn');
    const historyDiv = document.getElementById('history');
    let config = {};
    let serverUrl = 'http://localhost:8000';
    let recognition = null;
    let isRecording = false;

    // Initialize Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            queryInput.value = transcript;
        };
        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
            micBtn.textContent = 'Voice';
        };
        recognition.onerror = (event) => {
            console.error(`Speech recognition error: ${event.error}`);
            addToHistory(`Error: Speech recognition failed - ${event.error}`, 'error');
            isRecording = false;
            micBtn.classList.remove('recording');
            micBtn.textContent = 'Voice';
        };
    } else {
        micBtn.disabled = true;
        micBtn.title = 'Speech recognition not supported';
    }

    // File Upload Handler
    fileUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file && file.type === 'text/plain') {
            const reader = new FileReader();
            reader.onload = (e) => {
                queryInput.value = e.target.result;
                addToHistory(`File uploaded: ${file.name}`, 'request');
            };
            reader.onerror = () => {
                addToHistory('Error: Failed to read file', 'error');
            };
            reader.readAsText(file);
        } else {
            addToHistory('Error: Please upload a .txt file', 'error');
        }
        fileUpload.value = ''; // Reset input
    });

    // Microphone Button Handler
    micBtn.addEventListener('click', () => {
        if (!recognition) return;
        if (isRecording) {
            recognition.stop();
        } else {
            queryInput.value = '';
            recognition.start();
            isRecording = true;
            micBtn.classList.add('recording');
            micBtn.textContent = 'Stop';
        }
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
                                            responseEntry = createResponseEntry(data.result);
                                            historyDiv.insertBefore(responseEntry, historyDiv.firstChild);
                                        } else {
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
                const entry = createResponseEntry(data.result || JSON.stringify(data));
                historyDiv.insertBefore(entry, historyDiv.firstChild);
            }
        } catch (error) {
            console.log(`Request error: ${error.message}`);
            addToHistory(`Error: ${error.message}`, 'error');
        }

        queryInput.value = '';
    });

    function createResponseEntry(text) {
        const entry = document.createElement('div');
        entry.className = 'history-entry response';
        const textSpan = document.createElement('span');
        textSpan.className = 'response-text';
        textSpan.textContent = `Response: ${text}`;
        const playBtn = document.createElement('button');
        playBtn.className = 'play-btn';
        playBtn.textContent = 'Play';
        playBtn.title = 'Play response';
        playBtn.addEventListener('click', () => {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US';
            window.speechSynthesis.speak(utterance);
        });
        entry.appendChild(textSpan);
        entry.appendChild(playBtn);
        return entry;
    }

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
