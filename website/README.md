# secIRC Website

This is the official website for secIRC - Anonymous Censorship-Resistant Messaging System.

## 🌐 Website URL
**https://www.secirc.org**

## 📁 Files Structure
```
website/
├── index.html          # Main website page
├── styles.css          # CSS styles
├── script.js           # JavaScript functionality
├── favicon.ico         # Website favicon
├── favicon.svg         # SVG favicon
├── robots.txt          # Search engine crawler instructions
├── sitemap.xml         # Website sitemap
└── README.md           # This file
```

## 🚀 Deployment Instructions

### Option 1: Static Hosting (Recommended)
1. Upload all files to your web server
2. Point your domain `www.secirc.org` to the server
3. Ensure HTTPS is enabled
4. Test the website functionality

### Option 2: GitHub Pages
1. Create a new repository named `secirc-website`
2. Upload all files to the repository
3. Enable GitHub Pages in repository settings
4. Set custom domain to `www.secirc.org`

### Option 3: Netlify/Vercel
1. Connect your GitHub repository
2. Set build command to empty (static site)
3. Set publish directory to `website/`
4. Add custom domain `www.secirc.org`

## 🔧 Configuration

### Domain Setup
- **Primary Domain**: `www.secirc.org`
- **Redirect**: `secirc.org` → `www.secirc.org`
- **SSL Certificate**: Required (Let's Encrypt recommended)

### DNS Configuration
```
Type: A
Name: www.secirc.org
Value: [Your Server IP]

Type: CNAME
Name: secirc.org
Value: www.secirc.org
```

## 📱 Features

### Responsive Design
- Mobile-first approach
- Works on all devices
- Touch-friendly interface

### Performance
- Optimized images and assets
- Minified CSS and JavaScript
- Fast loading times

### SEO Optimized
- Meta tags and descriptions
- Structured data
- Sitemap and robots.txt
- Open Graph tags

### Security
- HTTPS required
- Security headers
- No external dependencies
- Privacy-focused

## 🎨 Design Features

### Modern UI
- Clean and professional design
- Smooth animations
- Interactive elements
- Dark/light theme support

### Sections
1. **Hero Section** - Main introduction
2. **Features** - Key benefits and features
3. **How It Works** - Step-by-step process
4. **Download** - Platform downloads
5. **Documentation** - Links to docs
6. **GitHub** - Open source information
7. **Footer** - Links and legal info

## 🔗 Links

### External Links
- **GitHub Repository**: https://github.com/jamaj69/secIRC
- **Documentation**: Links to GitHub docs
- **Downloads**: Links to GitHub releases

### Internal Navigation
- Smooth scrolling between sections
- Mobile-friendly navigation
- Breadcrumb navigation

## 📊 Analytics (Optional)

To add analytics, include the tracking code in `index.html`:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🔒 Security Considerations

### Headers to Add
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
```

### Privacy
- No tracking by default
- No external analytics
- No cookies
- GDPR compliant

## 🚀 Launch Checklist

- [ ] Upload all files to server
- [ ] Configure domain and DNS
- [ ] Enable HTTPS/SSL
- [ ] Test all links and functionality
- [ ] Verify mobile responsiveness
- [ ] Check page load speed
- [ ] Test in different browsers
- [ ] Submit to search engines
- [ ] Set up monitoring
- [ ] Create backup

## 📞 Support

For website issues or updates, contact:
- **GitHub Issues**: https://github.com/jamaj69/secIRC/issues
- **Email**: [Your contact email]

## 📄 License

This website is part of the secIRC project and is licensed under the MIT License.
