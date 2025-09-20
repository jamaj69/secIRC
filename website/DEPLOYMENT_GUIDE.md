# secIRC Website Deployment Guide

## 🚀 Deploying to Your Hosting Server

### **Server Requirements**
- ✅ **Web Server**: Apache, Nginx, or any HTTP server
- ✅ **SSL Certificate**: HTTPS enabled
- ✅ **Domain**: www.secirc.org configured
- ✅ **File Upload**: FTP, SFTP, or web panel access

### **Files to Upload**
Upload these files to your web server's document root (usually `public_html/` or `www/`):

```
website/
├── index.html          # Main website page
├── styles.css          # CSS styles
├── script.js           # JavaScript functionality
├── favicon.svg         # Website favicon
├── robots.txt          # Search engine instructions
├── sitemap.xml         # Website sitemap
└── favicon.ico         # Fallback favicon
```

### **Upload Methods**

#### **Method 1: FTP/SFTP**
```bash
# Using FTP client (FileZilla, WinSCP, etc.)
# Upload all files from website/ folder to your server's document root
```

#### **Method 2: Command Line (if you have SSH access)**
```bash
# Copy files to server
scp -r website/* user@your-server.com:/var/www/html/

# Or using rsync
rsync -avz website/ user@your-server.com:/var/www/html/
```

#### **Method 3: Web Panel**
- Use your hosting provider's file manager
- Upload all files from the `website/` folder
- Place them in the document root directory

### **Server Configuration**

#### **Apache (.htaccess)**
Create a `.htaccess` file in your document root:

```apache
# Enable HTTPS redirect
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Redirect secirc.org to www.secirc.org
RewriteCond %{HTTP_HOST} ^secirc\.org$ [NC]
RewriteRule ^(.*)$ https://www.secirc.org/$1 [L,R=301]

# Enable compression
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>

# Cache static files
<IfModule mod_expires.c>
    ExpiresActive on
    ExpiresByType text/css "access plus 1 year"
    ExpiresByType application/javascript "access plus 1 year"
    ExpiresByType image/png "access plus 1 year"
    ExpiresByType image/svg+xml "access plus 1 year"
</IfModule>

# Security headers
<IfModule mod_headers.c>
    Header always set X-Content-Type-Options nosniff
    Header always set X-Frame-Options DENY
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
</IfModule>
```

#### **Nginx Configuration**
Add to your Nginx server block:

```nginx
server {
    listen 80;
    server_name secirc.org www.secirc.org;
    return 301 https://www.secirc.org$request_uri;
}

server {
    listen 443 ssl http2;
    server_name secirc.org www.secirc.org;
    
    # Redirect secirc.org to www.secirc.org
    if ($host = secirc.org) {
        return 301 https://www.secirc.org$request_uri;
    }
    
    root /var/www/html;
    index index.html;
    
    # SSL configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
    
    # Compression
    gzip on;
    gzip_types text/plain text/css application/javascript application/json;
    
    # Cache static files
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### **DNS Configuration**

Ensure your DNS records are set up correctly:

```
Type: A
Name: www.secirc.org
Value: [Your Server IP Address]

Type: CNAME
Name: secirc.org
Value: www.secirc.org
```

### **Testing Checklist**

After deployment, test these:

- [ ] **HTTPS**: https://www.secirc.org loads correctly
- [ ] **Redirect**: http://secirc.org redirects to https://www.secirc.org
- [ ] **Mobile**: Website works on mobile devices
- [ ] **Speed**: Page loads quickly
- [ ] **Links**: All internal and external links work
- [ ] **SSL**: SSL certificate is valid and trusted
- [ ] **SEO**: Meta tags and sitemap are accessible

### **Performance Optimization**

#### **Enable Compression**
- Gzip compression for text files
- Image optimization
- Minify CSS/JS (optional)

#### **Caching**
- Browser caching for static assets
- CDN integration (optional)

#### **Monitoring**
- Set up uptime monitoring
- Monitor page load speeds
- Track visitor analytics (optional)

### **Security Considerations**

#### **SSL/TLS**
- Use TLS 1.2 or higher
- Enable HSTS (HTTP Strict Transport Security)
- Regular certificate renewal

#### **Headers**
- Security headers configured
- Content Security Policy
- X-Frame-Options protection

#### **Updates**
- Keep server software updated
- Monitor for security vulnerabilities
- Regular backups

### **Troubleshooting**

#### **Common Issues**
1. **404 Errors**: Check file paths and server configuration
2. **SSL Issues**: Verify certificate installation
3. **Slow Loading**: Enable compression and caching
4. **Mobile Issues**: Test responsive design

#### **Support**
- Check server error logs
- Test with different browsers
- Use online tools (GTmetrix, PageSpeed Insights)

### **Maintenance**

#### **Regular Tasks**
- Monitor website uptime
- Check SSL certificate expiration
- Update content as needed
- Review analytics and performance

#### **Backups**
- Regular file backups
- Database backups (if applicable)
- Configuration backups

---

**Your secIRC website is now ready for deployment to your hosting server!** 🚀
