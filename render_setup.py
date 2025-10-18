import sys
import re
from packaging.version import Version, InvalidVersion

def parse_version(version_str: str) -> Version:
    # Clean Render's AWS version string
    cleaned = re.sub(r'-\d+-aws$', '', version_str)
    try:
        return Version(cleaned)
    except InvalidVersion:
        return Version("3.11.7")  # Force Render's Python version

# Monkey-patch packaging module
import pip._vendor.packaging.version
pip._vendor.packaging.version.parse = parse_version

# Patch sys.version
if 'aws' in sys.version.lower():
    sys.version = sys.version.replace('aws', '')
    sys.version_info = sys.version_info[:3]  # Strip extra version components
