#!/bin/bash

# GenAI Job Assistant - Setup Script
# This script handles initial installation and configuration

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    print_header "GenAI Job Assistant - Setup"
    
    # Step 1: Check Python version
    print_info "Checking Python version..."
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
    
    # Step 2: Create virtual environment
    print_info "Creating virtual environment..."
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Step 3: Activate virtual environment
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
    
    # Step 4: Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    print_success "pip upgraded"
    
    # Step 5: Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
    
    # Step 6: Check Ollama installation
    print_info "Checking Ollama installation..."
    if ! command_exists ollama; then
        print_warning "Ollama is not installed"
        print_info "Please install Ollama from: https://ollama.ai/download"
        print_info "After installation, run: ollama pull llama3"
    else
        print_success "Ollama found"
        
        # Check if Ollama is running
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            print_success "Ollama service is running"
            
            # Check if llama3 model is available
            if ollama list | grep -q "llama3"; then
                print_success "llama3 model is available"
            else
                print_warning "llama3 model not found"
                print_info "Downloading llama3 model (this may take a while)..."
                ollama pull llama3
                print_success "llama3 model downloaded"
            fi
        else
            print_warning "Ollama service is not running"
            print_info "Start Ollama with: ollama serve"
        fi
    fi
    
    # Step 7: Check Chrome/Chromium
    print_info "Checking Chrome/Chromium installation..."
    if command_exists google-chrome || command_exists chromium-browser || command_exists chromium; then
        print_success "Chrome/Chromium found"
    else
        print_warning "Chrome/Chromium not found"
        print_info "Please install Chrome or Chromium for web scraping functionality"
    fi
    
    # Step 8: Initialize application
    print_info "Initializing application..."
    python3 scripts/init_app.py
    
    if [ $? -eq 0 ]; then
        print_success "Application initialized successfully"
    else
        print_error "Application initialization failed"
        exit 1
    fi
    
    # Step 9: Display next steps
    print_header "Setup Complete!"
    
    echo "Next steps:"
    echo ""
    echo "1. Configure your preferences:"
    echo "   - Edit config/config.yaml with your job search criteria"
    echo "   - Update user profile information"
    echo "   - Configure notification settings"
    echo ""
    echo "2. (Optional) Set up notifications:"
    echo "   - For email: Add SMTP credentials to config/config.yaml"
    echo "   - For WhatsApp: Add Twilio credentials to config/config.yaml"
    echo ""
    echo "3. Start the application:"
    echo "   - Interactive UI: streamlit run app.py"
    echo "   - Background scheduler: python scripts/run_scheduler.py"
    echo ""
    echo "4. (Optional) Set up automated backups:"
    echo "   - Run: python scripts/backup_db.py"
    echo "   - Add to cron for daily backups"
    echo ""
    
    print_success "Setup completed successfully!"
}

# Run main function
main
