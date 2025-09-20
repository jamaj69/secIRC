// secIRC Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                targetSection.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Add scroll effect to header
    const header = document.querySelector('.header');
    let lastScrollY = window.scrollY;

    window.addEventListener('scroll', () => {
        const currentScrollY = window.scrollY;
        
        if (currentScrollY > 100) {
            header.style.background = 'rgba(255, 255, 255, 0.95)';
            header.style.backdropFilter = 'blur(10px)';
        } else {
            header.style.background = 'var(--light-bg)';
            header.style.backdropFilter = 'none';
        }
        
        lastScrollY = currentScrollY;
    });

    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Observe download cards
    const downloadCards = document.querySelectorAll('.download-card');
    downloadCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Observe documentation cards
    const docCards = document.querySelectorAll('.doc-card');
    docCards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });

    // Network diagram animation
    const networkDiagram = document.querySelector('.network-diagram');
    if (networkDiagram) {
        const nodes = networkDiagram.querySelectorAll('.node');
        const connections = networkDiagram.querySelectorAll('.connection');
        
        // Animate nodes
        nodes.forEach((node, index) => {
            node.style.opacity = '0';
            node.style.transform = 'scale(0.8)';
            node.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                node.style.opacity = '1';
                node.style.transform = 'scale(1)';
            }, index * 200);
        });
        
        // Animate connections
        connections.forEach((connection, index) => {
            connection.style.opacity = '0';
            connection.style.transform = 'scaleX(0)';
            connection.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            
            setTimeout(() => {
                connection.style.opacity = '1';
                connection.style.transform = 'scaleX(1)';
            }, 1000 + index * 200);
        });
    }

    // GitHub stats animation
    const statNumbers = document.querySelectorAll('.stat-number');
    const statsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = entry.target;
                const finalValue = target.textContent;
                const isNumber = !isNaN(parseInt(finalValue));
                
                if (isNumber) {
                    const startValue = 0;
                    const duration = 2000;
                    const increment = parseInt(finalValue) / (duration / 16);
                    let currentValue = startValue;
                    
                    const timer = setInterval(() => {
                        currentValue += increment;
                        if (currentValue >= parseInt(finalValue)) {
                            currentValue = parseInt(finalValue);
                            clearInterval(timer);
                        }
                        target.textContent = Math.floor(currentValue);
                    }, 16);
                }
                
                statsObserver.unobserve(target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(stat => {
        statsObserver.observe(stat);
    });

    // Mobile menu toggle (if needed)
    const createMobileMenu = () => {
        const nav = document.querySelector('.nav-container');
        const navMenu = document.querySelector('.nav-menu');
        
        if (window.innerWidth <= 768) {
            // Create mobile menu button
            const mobileMenuBtn = document.createElement('button');
            mobileMenuBtn.className = 'mobile-menu-btn';
            mobileMenuBtn.innerHTML = '☰';
            mobileMenuBtn.style.cssText = `
                background: none;
                border: none;
                font-size: 1.5rem;
                color: var(--light-text);
                cursor: pointer;
                display: block;
            `;
            
            nav.appendChild(mobileMenuBtn);
            
            // Toggle mobile menu
            mobileMenuBtn.addEventListener('click', () => {
                navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
            });
            
            // Hide menu on link click
            navMenu.addEventListener('click', () => {
                navMenu.style.display = 'none';
            });
        }
    };

    // Initialize mobile menu
    createMobileMenu();
    
    // Recreate mobile menu on resize
    window.addEventListener('resize', createMobileMenu);

    // Add loading animation
    const addLoadingAnimation = () => {
        const style = document.createElement('style');
        style.textContent = `
            .loading {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: var(--light-bg);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999;
                transition: opacity 0.5s ease;
            }
            
            .loading.hidden {
                opacity: 0;
                pointer-events: none;
            }
            
            .spinner {
                width: 50px;
                height: 50px;
                border: 3px solid var(--border-color);
                border-top: 3px solid var(--primary-color);
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
        
        // Remove loading screen after page load
        window.addEventListener('load', () => {
            const loading = document.querySelector('.loading');
            if (loading) {
                loading.classList.add('hidden');
                setTimeout(() => {
                    loading.remove();
                }, 500);
            }
        });
    };

    // Add loading screen
    addLoadingAnimation();

    // Add typing animation to hero title
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        const text = heroTitle.textContent;
        heroTitle.textContent = '';
        heroTitle.style.borderRight = '2px solid var(--accent-color)';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                heroTitle.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 100);
            } else {
                setTimeout(() => {
                    heroTitle.style.borderRight = 'none';
                }, 1000);
            }
        };
        
        setTimeout(typeWriter, 500);
    }

    // Add parallax effect to hero section
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const rate = scrolled * -0.5;
            hero.style.transform = `translateY(${rate}px)`;
        });
    }

    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });

    // Add click animation to cards
    const cards = document.querySelectorAll('.feature-card, .download-card, .doc-card');
    cards.forEach(card => {
        card.addEventListener('click', function() {
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });

    // Console message
    console.log(`
    🔐 secIRC - Anonymous Censorship-Resistant Messaging
    🌐 Website: https://www.secirc.org
    📱 GitHub: https://github.com/jamaj69/secIRC
    🚀 Built with privacy and security in mind
    `);
});
