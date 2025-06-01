import os
import sys
from pathlib import Path

def export_project_to_file(root_dir, output_file):
    """
    Export all Python files in a project directory to a single file with formatted structure.
    """
    root_path = Path(root_dir).resolve()
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for dirpath, _, filenames in os.walk(root_path):
            # Filter for Python files only
            py_files = [f for f in filenames if f.endswith('.py')]
            if not py_files:
                continue
                
            # Get relative path and format as specified
            rel_path = Path(dirpath).relative_to(root_path)
            path_parts = rel_path.parts
            
            for py_file in py_files:
                file_path = Path(dirpath) / py_file
                # Write formatted path
                formatted_path = f"# [{'/'.join(path_parts)}]/{py_file}" if path_parts != ('.',) else f"# {py_file}"
                outfile.write(f"{formatted_path}\n")
                
                # Write file contents
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        outfile.write(f"{content}\n\n")
                except Exception as e:
                    outfile.write(f"# Error reading {file_path}: {str(e)}\n\n")

if __name__ == "__main__":
    if len(sys.argv) >= 2: 
        project_dir = sys.argv[1] 
    else: 
        project_dir = "."

    if len(sys.argv) >= 3: 
        output_file = sys.argv[2] 
    else: 
        output_file = "paia.txt"

    
    if not os.path.isdir(project_dir):
        print(f"Error: {project_dir} is not a valid directory")
        sys.exit(1)
        
    export_project_to_file(project_dir, output_file)
    print(f"Project exported to {output_file}")