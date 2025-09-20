#!/bin/bash

# secIRC Website Deployment Script
# This script helps deploy the website to your hosting server

set -e

echo "🚀 secIRC Website Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "index.html" ]; then
    print_status "ERROR" "Please run this script from the website directory"
    exit 1
fi

print_status "INFO" "Website files found:"
ls -la *.html *.css *.js *.svg *.txt *.xml 2>/dev/null || true

echo ""
print_status "INFO" "Deployment Options:"
echo "1. Create deployment package (ZIP file)"
echo "2. Show FTP/SFTP upload commands"
echo "3. Show server configuration examples"
echo "4. Exit"
echo ""

read -p "Choose an option (1-4): " choice

case $choice in
    1)
        print_status "INFO" "Creating deployment package..."
        
        # Create deployment package
        PACKAGE_NAME="secirc-website-$(date +%Y%m%d-%H%M%S).zip"
        
        # Create temporary directory
        TEMP_DIR=$(mktemp -d)
        cp *.html *.css *.js *.svg *.txt *.xml "$TEMP_DIR/" 2>/dev/null || true
        
        # Create ZIP package
        cd "$TEMP_DIR"
        zip -r "$PACKAGE_NAME" . > /dev/null
        mv "$PACKAGE_NAME" "$OLDPWD/"
        cd "$OLDPWD"
        
        # Clean up
        rm -rf "$TEMP_DIR"
        
        print_status "SUCCESS" "Deployment package created: $PACKAGE_NAME"
        print_status "INFO" "Upload this file to your server and extract it in the document root"
        ;;
        
    2)
        print_status "INFO" "FTP/SFTP Upload Commands:"
        echo ""
        echo "FTP Upload:"
        echo "  ftp your-server.com"
        echo "  cd /var/www/html"
        echo "  put index.html"
        echo "  put styles.css"
        echo "  put script.js"
        echo "  put favicon.svg"
        echo "  put robots.txt"
        echo "  put sitemap.xml"
        echo ""
        echo "SFTP Upload:"
        echo "  sftp user@your-server.com"
        echo "  cd /var/www/html"
        echo "  put index.html"
        echo "  put styles.css"
        echo "  put script.js"
        echo "  put favicon.svg"
        echo "  put robots.txt"
        echo "  put sitemap.xml"
        echo ""
        echo "SCP Upload (all files at once):"
        echo "  scp *.html *.css *.js *.svg *.txt *.xml user@your-server.com:/var/www/html/"
        echo ""
        echo "Rsync Upload:"
        echo "  rsync -avz . user@your-server.com:/var/www/html/"
        ;;
        
    3)
        print_status "INFO" "Server Configuration Examples:"
        echo ""
        echo "Apache .htaccess file:"
        echo "  Create .htaccess in document root with:"
        echo "  - HTTPS redirect"
        echo "  - www.secirc.org redirect"
        echo "  - Compression"
        echo "  - Security headers"
        echo ""
        echo "Nginx configuration:"
        echo "  - SSL server block"
        echo "  - Domain redirects"
        echo "  - Security headers"
        echo "  - Compression"
        echo ""
        echo "See DEPLOYMENT_GUIDE.md for complete configuration examples"
        ;;
        
    4)
        print_status "INFO" "Exiting..."
        exit 0
        ;;
        
    *)
        print_status "ERROR" "Invalid option. Please choose 1-4."
        exit 1
        ;;
esac

echo ""
print_status "INFO" "Next Steps:"
echo "1. Upload files to your server's document root"
echo "2. Configure server (Apache/Nginx)"
echo "3. Test the website at https://www.secirc.org"
echo "4. Check SSL certificate"
echo "5. Test mobile responsiveness"
echo ""
print_status "SUCCESS" "Deployment preparation complete!"
