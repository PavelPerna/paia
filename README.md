# AI Microservice Application

This is a multi-threaded Python application providing AI microservices (e.g., text generation, translation) via a web UI. It uses a REST API (`localhost:8000`) and a separate UI server (`localhost:8080`), with configuration managed by a singleton (`PAIAConfig`) and logging via `PAIALogger` to `app.log`.

## Features

- **Services**: Text generation (`Novaciano/NSFW-AMEBA-3.2-1B`), translation (`Helsinki-NLP/opus-mt`), text analysis, sentiment analysis, text summarization.
- **UI**: Web interface with `select`, `text`, `textbox`, and `slider` inputs, streaming responses for text generation.
- **Multi-threading**: Main server uses `ThreadingTCPServer`; UI server runs in a separate thread.
- **Configuration**: Managed via `config.json` with singleton access (`PAIAConfig`).
- **Logging**: Detailed logs with thread names in `app.log` and console (`PAIALogger`).

## Project Structure

```
project_directory/
├── app.log                # Log file
├── config.json            # Configuration
├── README.md              # This file
├── server.py              # Main server (localhost:8000)
├── build_ui.py            # Generates UI files
├── ui/                    # UI files
│   ├── index.html
│   ├── styles.css
│   ├── script.js
│   ├── image/             # For generated images (if applicable)
├── ai/
│   ├── __init__.py
│   ├── config.py          # PAIAConfig singleton
│   ├── logger.py          # PAIALogger singleton
│   ├── singleton.py       # PAIASingleton base class
│   ├── microservice/
│   │   ├── __init__.py
│   │   ├── base_service.py
│   │   ├── text_analyzer.py
│   │   ├── sentiment_analyzer.py
│   │   ├── text_summarizer.py
│   │   ├── text_generator.py  # TextGenerationService
│   │   ├── translate.py       # TranslateService
```

## Prerequisites

- Python 3.8+
- Dependencies:
  ```bash
  pip install transformers torch
  ```

## Setup

1. **Clone the Repository**:

   ```bash
   git clone <repository-url>
   cd project_directory
   ```
2. **Install Dependencies**:

   ```bash
   pip install transformers torch
   ```
3. **Verify `config.json`**:

   - Ensure `config.json` is in the project root (same directory as `server.py`).
   - Example `config.json`:
     ```json
     {
       "server": {
         "host": "localhost",
         "port": 8000
       },
       "ui": {
         "directory": "ui"
       },
       "services": {
         "translate": {
           "enabled": true,
           "streamable": false,
           "parameters": [
             {
               "name": "source_language",
               "type": "select",
               "label": "Source Language",
               "options": [
                 {"value": "cs", "label": "Czech"},
                 {"value": "en", "label": "English"},
                 {"value": "fr", "label": "French"},
                 {"value": "de", "label": "German"}
               ]
             },
             {
               "name": "target_language",
               "type": "select",
               "label": "Target Language",
               "options": [
                 {"value": "cs", "label": "Czech"},
                 {"value": "en", "label": "English"},
                 {"value": "fr", "label": "French"},
                 {"value": "de", "label": "German"}
               ]
             }
           ]
         },
         "text-generator": {
           "enabled": true,
           "streamable": true,
           "parameters": [
             {
               "name": "prefix",
               "type": "textbox",
               "label": "Prefix",
               "placeholder": "Enter prefix (e.g., Once upon a time)",
               "rows": 2
             },
             {
               "name": "context",
               "type": "textbox",
               "label": "Context",
               "placeholder": "Enter context (optional)",
               "rows": 2
             },
             {
               "name": "max_length",
               "type": "slider",
               "label": "Max Length",
               "min": 10,
               "max": 200,
               "step": 5,
               "value": 50
             }
           ]
         },
         "text-analyzer": {
           "enabled": true,
           "streamable": false,
           "parameters": []
         },
         "sentiment-analyzer": {
           "enabled": true,
           "streamable": false,
           "parameters": []
         },
         "text-summarizer": {
           "enabled": true,
           "streamable": false,
           "parameters": []
         }
       }
     }
     ```
   - Verify permissions:
     ```bash
     ls -l config.json
     chmod +r config.json
     ```
4. **Generate UI**:

   ```bash
   python build_ui.py
   ```

   - Creates `ui/index.html`, `ui/styles.css`, `ui/script.js`, `ui/image/`.
   - Check `app.log` for:
     ```
     2025-05-24 00:33:00,000 [MainThread] INFO: Loaded config, UI directory: ui
     2025-05-24 00:33:00,001 [MainThread] INFO: Generating ui/index.html
     ```

## Running the Application

1. **Start the Server**:

   ```bash
   python server.py
   ```

   - Main server runs on `http://localhost:8000`.
   - UI server runs on `http://localhost:8080` in a separate thread.
   - Check `app.log` for:
     ```
     2025-05-24 00:33:01,000 [MainThread] INFO: Loaded config: host=localhost, port=8000, ui_dir=ui
     2025-05-24 00:33:01,001 [MainThread] INFO: Loaded service: text-generator
     2025-05-24 00:33:01,002 [MainThread] INFO: Loaded service: translate
     2025-05-24 00:33:01,003 [MainThread] INFO: Starting UI server in separate thread
     2025-05-24 00:33:01,004 [Thread-1] INFO: UI server running at http://localhost:8080
     2025-05-24 00:33:01,005 [MainThread] INFO: Main server running at http://localhost:8000
     ```
2. **Access the UI**:

   - Open `http://localhost:8080` in a browser.
   - Select a service (e.g., TEXT GENERATOR, TRANSLATE) from the dropdown.
   - Input query and parameters (e.g., sliders, textboxes).
3. **Test Text Generation**:

   - Select “Text Generator”.
   - Enter “Hello world” in query, “Story:” in “Prefix”, leave “Context” empty, set “Max Length” to 50.
   - Click “Submit”.
   - Expect streaming responses in history (e.g., “Response: Story: Hello world, how are you”).
   - Check `app.log`:
     ```
     2025-05-24 00:33:02,000 [Thread-2] DEBUG: Received POST: {"service":"text-generator","query":{"text":"Hello world","prefix":"Story:","context":"","max_length":50},"stream":true}
     2025-05-24 00:33:02,001 [Thread-2] INFO: Processing text-generator, stream=true
     2025-05-24 00:33:02,002 [Thread-2] DEBUG: Generated text: Story: Hello world, how
     ```
4. **Test Translation**:

   - Select “Translate”, choose “Czech” to “English”, enter “Ahoj”.
   - Click “Submit”.
   - Expect: “Request: translate - Ahoj” (blue), “Response: Hello” (green).
   - Check `app.log`:
     ```
     2025-05-24 00:33:03,000 [Thread-3] DEBUG: Received POST: {"service":"translate","query":{"text":"Ahoj","source_language":"cs","target_language":"en"},"stream":false}
     2025-05-24 00:33:03,001 [Thread-3] INFO: Translation result: Hello
     ```

## Debugging

### Config/Services Not Loading

- **Symptoms**: Dropdown empty, “No services available” in UI history.
- **Check `app.log`**:
  - Look for:
    ```
    ERROR: config.json not found at /path/to/project/config.json
    ERROR: No services in SERVICE_REGISTRY
    ```
  - Fix:
    - Ensure `config.json` is in project root:
      ```bash
      ls -l config.json
      ```
    - Verify permissions:
      ```bash
      chmod +r config.json
      ```
    - Test endpoints:
      ```bash
      curl http://localhost:8000/config
      curl http://localhost:8000/services
      ```
- **Browser Console**:
  - Check for:
    ```
    Config fetch error: ...
    Services fetched: []
    ```
  - Ensure `http://localhost:8000` is running.

### Streaming Not Visible

- **Symptoms**: Text generation responses don’t appear or are delayed.
- **Check `app.log`**:
  - Verify:
    ```
    DEBUG: Generated text: Story: Hello world, how
    INFO: EOS token reached
    ```
  - If missing, check for:
    ```
    ERROR: Error in text generation: ...
    ```
- **Browser Console**:
  - Look for:
    ```
    Parsed SSE event: {"result":"Story: Hello world, how"}
    ```
  - If absent, ensure `streamable: true` in `config.json` for `text-generator`.
- **Fix**:
  - Reduce `time.sleep(0.2)` in `text_generator.py` to `0.1` for faster UI updates.
  - Check Network tab for SSE responses.

### General Issues

- **Logs**: Review `app.log` for `DEBUG`, `INFO`, `ERROR` entries with thread names.
- **File Access**:
  - Verify `ui/` is writable:
    ```bash
    chmod -R u+w ui/
    ```
- **CWD**:
  - Run commands from project root:
    ```bash
    cd /path/to/project
    pwd
    python server.py
    ```

## Contributing

- Add new services in `ai/microservice/` by extending `AIMicroService`.
- Update `config.json` with service parameters (`select`, `text`, `textbox`, `slider`).
- Submit pull requests with clear descriptions.

## License

MIT License. See `LICENSE` for details.

---

### Notes

- **Config Path**: Assumes `config.json` is in the project root, loaded via `PAIAConfig` with `__file__`-based path.
- **Logging**: Guides users to `app.log` for debugging, with thread names for multi-threading clarity.
- **Streaming**: Highlights `streamable: true` for `text-generator` and UI’s SSE handling.
- **Debugging**: Provides specific commands and log checks for common issues.

Please confirm if this `README.md` meets your needs or if you want additions (e.g., specific service details, API endpoints, or screenshots). If you’re still seeing “config.json not found”, share:

- **app.log**: Full contents, especially `Attempting to load config`.
- **CWD**: Output of `pwd` when running `server.py`.
- **File Check**: Output of `ls -l config.json`.
- **UI**: Dropdown contents, streaming behavior.

I can refine the README or assist with further debugging!
