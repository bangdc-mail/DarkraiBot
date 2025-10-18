#!/bin/bash

# Discord Bot Setup Script
# This script helps with initial setup and common operations

set -e

echo "🤖 Discord Bot Setup Script"
echo "=============================="

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

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_success "Docker and Docker Compose are installed"
}

# Setup environment file
setup_env() {
    if [ ! -f .env ]; then
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file and add your bot token and owner ID"
        print_status "You can edit it with: nano .env"
    else
        print_status ".env file already exists"
    fi
}

# Create data directory
setup_data() {
    if [ ! -d data ]; then
        print_status "Creating data directory..."
        mkdir -p data
        touch data/.gitkeep
    fi
    print_success "Data directory is ready"
}

# Build and start the bot
start_bot() {
    print_status "Building and starting the Discord bot..."
    docker compose up -d --build

    # Wait a moment for containers to start
    sleep 3

    # Check if containers are running
    if docker compose ps | grep -q "Up"; then
        print_success "Bot is starting up!"
        print_status "You can check logs with: docker compose logs -f discord-bot"
    else
        print_error "Failed to start the bot. Check logs with: docker compose logs"
    fi
}

# Stop the bot
stop_bot() {
    print_status "Stopping the Discord bot..."
    docker compose down
    print_success "Bot stopped"
}

# Show logs
show_logs() {
    print_status "Showing bot logs (Ctrl+C to exit)..."
    docker compose logs -f discord-bot
}

# Restart the bot
restart_bot() {
    print_status "Restarting the Discord bot..."
    docker compose restart discord-bot
    print_success "Bot restarted"
}

# Update the bot
update_bot() {
    print_status "Updating the Discord bot..."
    docker compose down
    docker compose build --no-cache
    docker compose up -d
    print_success "Bot updated and restarted"
}

# Show status
show_status() {
    print_status "Bot Status:"
    docker compose ps

    echo
    print_status "Resource Usage:"
    docker stats --no-stream discord-bot discord-bot-redis 2>/dev/null || echo "Containers not running"
}

# Backup data
backup_data() {
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    print_status "Creating backup in $BACKUP_DIR..."

    mkdir -p "$BACKUP_DIR"
    cp -r data/ "$BACKUP_DIR/"
    cp .env "$BACKUP_DIR/" 2>/dev/null || true

    print_success "Backup created in $BACKUP_DIR"
}

# Main menu
show_menu() {
    echo
    echo "Available commands:"
    echo "  setup     - Initial setup (create .env, data directory)"
    echo "  start     - Start the bot"
    echo "  stop      - Stop the bot"
    echo "  restart   - Restart the bot"
    echo "  logs      - Show bot logs"
    echo "  status    - Show bot status"
    echo "  update    - Update and restart the bot"
    echo "  backup    - Backup bot data"
    echo "  help      - Show this menu"
    echo
}

# Handle command line arguments
case "${1:-help}" in
    "setup")
        check_docker
        setup_env
        setup_data
        print_success "Setup complete! Edit .env file and run './setup.sh start'"
        ;;
    "start")
        check_docker
        setup_data
        start_bot
        ;;
    "stop")
        stop_bot
        ;;
    "restart")
        restart_bot
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "update")
        update_bot
        ;;
    "backup")
        backup_data
        ;;
    "help"|*)
        show_menu
        ;;
esac