import os
from pathlib import Path
from paia import PAIAConfig, PAIALogger

# Initialize logger and config via global singletons
logger = PAIALogger().getLogger()
config = PAIAConfig().getConfig()
UI_DIR = PAIAConfig().ui_dir
TEMPLATE_DIR = os.path.join(PAIAConfig().root_dir, "ui", "template")

def write_file(filepath, content):
    logger.info(f"Generating {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def read_template_file(template_path):
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.debug(f"Successfully read template: {template_path}")
        return content
    except FileNotFoundError:
        logger.error(f"Template file not found: {template_path}")
        raise
    except PermissionError:
        logger.error(f"Permission denied for template file: {template_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading template file {template_path}: {str(e)}")
        raise

def build_ui():
    # Ensure output directories exist
    os.makedirs(UI_DIR, exist_ok=True)
    os.makedirs(os.path.join(UI_DIR, "image"), exist_ok=True)

    # List of template files to process
    template_files = {
        "index.html": os.path.join(TEMPLATE_DIR, "index.html"),
        "styles.css": os.path.join(TEMPLATE_DIR, "styles.css"),
        "api.js": os.path.join(TEMPLATE_DIR, "api.js"),
        "script.js": os.path.join(TEMPLATE_DIR, "script.js")
    }

    # Check if template directory exists
    if not os.path.exists(TEMPLATE_DIR):
        logger.error(f"Template directory not found: {TEMPLATE_DIR}")
        raise FileNotFoundError(f"Template directory {TEMPLATE_DIR} does not exist")

    # Copy each template file to the output directory
    for output_filename, template_path in template_files.items():
        content = read_template_file(template_path)
        output_path = os.path.join(UI_DIR, output_filename)
        write_file(output_path, content)

if __name__ == "__main__":
    try:
        build_ui()
        logger.info("UI files generated successfully")
    except Exception as e:
        logger.error(f"Failed to build UI: {str(e)}")
        raise