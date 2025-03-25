#!/usr/bin/env python3
"""
QMLaude - A Claude-powered QML Generator
Entry point script
"""
import sys
import os

# Add the claude package to path if needed
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

from claude.main import main

if __name__ == "__main__":
    sys.exit(main())