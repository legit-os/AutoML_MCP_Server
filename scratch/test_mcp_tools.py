import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from dist_automl.mcp_server import read_file, run_file
import yaml

def test_read_file():
    print("Testing read_file tool...")
    # This assumes a project is initialized and has a config.yaml
    # We can try to read a known path if available, or just check if it fails gracefully
    result = read_file("nonexistent.file")
    print(f"Read nonexistent: {result}")
    
    # Try reading the config info to see what's available
    from dist_automl.mcp_server import get_current_project_info
    info = get_current_project_info()
    print(f"Project info: {info}")
    
    # If there's a file in config, try reading it
    config_data = yaml.safe_load(info['config'])
    if 'utils' in config_data and 'files' in config_data['utils'] and config_data['utils']['files']:
        first_util = list(config_data['utils']['files'].keys())[0]
        read_path = f"utils.{first_util}"
        print(f"Attempting to read: {read_path}")
        content = read_file(read_path)
        print(f"Content length: {len(content) if isinstance(content, str) else 'N/A'}")
    else:
        print("No utils files found in config to test reading.")

if __name__ == "__main__":
    test_read_file()
