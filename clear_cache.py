"""
Clear Streamlit cache to force fresh data load
Run this if you want to clear all cached data
"""
import streamlit as st
import shutil
from pathlib import Path

# Clear Streamlit cache directory
cache_dir = Path(".streamlit/cache")
if cache_dir.exists():
    shutil.rmtree(cache_dir)
    print("✓ Streamlit cache cleared")
else:
    print("ℹ No cache directory found")

print("\nCache cleared! Restart your Streamlit app to see fresh data.")
