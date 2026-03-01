#!/bin/bash

# MCP Server for 212 Trading - Setup Script
# This script automates the installation and initial configuration

set -e  # Exit on any error

echo "🚀 Setting up MCP Server for 212 Trading..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Check if Python 3.14+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.14"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python3"
        else
            print_error "Python 3.14+ is required, but found $PYTHON_VERSION"
            exit 1
        fi
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.14"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then
            print_success "Python $PYTHON_VERSION found"
            PYTHON_CMD="python"
        else
            print_error "Python 3.14+ is required, but found $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python is not installed. Please install Python 3.14+ and try again."
        exit 1
    fi
}

# Check if uv is installed, if not suggest installation
check_uv() {
    print_status "Checking for uv package manager..."
    
    if command -v uv &> /dev/null; then
        print_success "uv found"
        USE_UV=true
    else
        print_warning "uv not found. You can install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        print_status "Falling back to pip..."
        USE_UV=false
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    if [ "$USE_UV" = true ]; then
        print_status "Using uv to install dependencies..."
        uv sync
        print_success "Dependencies installed with uv"
    else
        print_status "Using pip to install dependencies..."
        $PYTHON_CMD -m pip install --upgrade pip
        $PYTHON_CMD -m pip install -e .
        print_success "Dependencies installed with pip"
    fi
}

# Create environment template
create_env_template() {
    print_status "Creating environment template..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_success "Created .env file from template"
            print_warning "Please edit .env file with your 212 Trading API credentials"
        else
            print_error ".env.template not found. Please create it manually."
        fi
    else
        print_warning ".env file already exists, skipping creation"
    fi
}

# Test the installation
test_installation() {
    print_status "Testing installation..."
    
    # Check if main.py exists and is executable
    if [ -f "main.py" ]; then
        print_success "main.py found"
    else
        print_error "main.py not found"
        exit 1
    fi
    
    # Try to import the required modules
    if $PYTHON_CMD -c "import mcp, httpx, dotenv" 2>/dev/null; then
        print_success "All required modules can be imported"
    else
        print_error "Some required modules cannot be imported. Please check your installation."
        exit 1
    fi
}

# Display next steps
show_next_steps() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit the .env file with your 212 Trading API credentials:"
    echo "   - 212_API_KEY_ID=your_api_key_id"
    echo "   - 212_API_KEY_SECRET=your_api_secret"
    echo "   - 212_API_BASE_LIVE_URL=https://live.trading212.com/api/v0"
    echo ""
    echo "2. Configure Claude Desktop:"
    echo "   - Open Claude Desktop"
    echo "   - Go to Settings > Developer"
    echo "   - Add this MCP server configuration:"
    echo ""
    echo "   {"
    echo "     \"mcpServers\": {"
    echo "       \"212-trading\": {"
    echo "         \"command\": \"$PYTHON_CMD\","
    echo "         \"args\": [\"$(pwd)/main.py\"],"
    echo "         \"env\": {"
    echo "           \"212_API_KEY_ID\": \"your_api_key_id\","
    echo "           \"212_API_KEY_SECRET\": \"your_api_secret\","
    echo "           \"212_API_BASE_LIVE_URL\": \"https://live.trading212.com/api/v0\""
    echo "         }"
    echo "       }"
    echo "     }"
    echo "   }"
    echo ""
    echo "3. Restart Claude Desktop"
    echo ""
    echo "4. Test the connection by asking Claude: 'Show me my account balance'"
    echo ""
    print_warning "Remember to keep your API credentials secure!"
}

# Main execution
main() {
    echo "=========================================="
    echo "  MCP Server for 212 Trading Setup"
    echo "=========================================="
    echo ""
    
    check_python
    check_uv
    install_dependencies
    create_env_template
    test_installation
    show_next_steps
}

# Run main function
main "$@"
