// ui/api.js
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