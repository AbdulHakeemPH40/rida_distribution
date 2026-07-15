/* ============================================================
   RiDA Landing Page — Main JavaScript
   Version: 1.0 | Date: 2026-07-11
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  // ─── INIT ───
  initNavbar();
  initThemeToggle();
  initLanguageToggle();
  initFrameworkTimeline();
  initMobileMenu();
  initSmoothScroll();

  // Wait for GSAP to load, then init animations
  if (typeof gsap !== 'undefined') {
    initGSAPAnimations();
  } else {
    window.addEventListener('load', () => {
      if (typeof gsap !== 'undefined') {
        initGSAPAnimations();
      } else {
        // Fallback: show all elements if GSAP fails
        showAllRevealElements();
      }
    });
  }
});

// ─── 1. NAVBAR ───
function initNavbar() {
  const navbar = document.getElementById('navbar');
  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;

    if (currentScroll > 80) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    lastScroll = currentScroll;
  });

  // Active link highlight
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.navbar-links a');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(link => {
          link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
        });
      }
    });
  }, { threshold: 0.3, rootMargin: '-80px 0px -50% 0px' });

  sections.forEach(section => observer.observe(section));
}

// ─── 2. DARK MODE TOGGLE ───
function initThemeToggle() {
  const toggle = document.getElementById('themeToggle');
  const html = document.documentElement;
  const sunIcon = toggle.querySelector('.icon-sun');
  const moonIcon = toggle.querySelector('.icon-moon');

  // Check saved preference or system preference
  const savedTheme = localStorage.getItem('rida-theme');
  const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme === 'dark' || (!savedTheme && systemDark)) {
    html.setAttribute('data-theme', 'dark');
    sunIcon.style.display = 'none';
    moonIcon.style.display = 'block';
  }

  toggle.addEventListener('click', () => {
    const isDark = html.getAttribute('data-theme') === 'dark';

    if (isDark) {
      html.removeAttribute('data-theme');
      localStorage.setItem('rida-theme', 'light');
      sunIcon.style.display = 'block';
      moonIcon.style.display = 'none';
    } else {
      html.setAttribute('data-theme', 'dark');
      localStorage.setItem('rida-theme', 'dark');
      sunIcon.style.display = 'none';
      moonIcon.style.display = 'block';
    }
  });
}

// ─── 3. LANGUAGE TOGGLE ───
function initLanguageToggle() {
  const toggle = document.getElementById('langToggle');
  const html = document.documentElement;
  let isArabic = false;

  // Check saved preference
  const savedLang = localStorage.getItem('rida-lang');
  if (savedLang === 'ar') {
    isArabic = true;
    applyLanguage(true);
  }

  toggle.addEventListener('click', () => {
    isArabic = !isArabic;
    applyLanguage(isArabic);
    localStorage.setItem('rida-lang', isArabic ? 'ar' : 'en');
  });

  function applyLanguage(arabic) {
    if (arabic) {
      html.setAttribute('dir', 'rtl');
      html.setAttribute('lang', 'ar');
      toggle.textContent = 'AR | EN';
    } else {
      html.setAttribute('dir', 'ltr');
      html.setAttribute('lang', 'en');
      toggle.textContent = 'EN | AR';
    }

    // Switch both navbar and footer brand artwork with the page language.
    document.querySelectorAll('.navbar-logo, .footer-logo').forEach(logo => {
      const englishLogo = logo.getAttribute('data-logo-en') || 'assets/logos/logo_english.png';
      const arabicLogo = logo.getAttribute('data-logo-ar') || 'assets/logos/logo_2_arabic.png';
      logo.setAttribute('src', arabic ? arabicLogo : englishLogo);
      logo.alt = arabic ? 'شعار ريدا' : 'RiDA Logo';
    });

    // Update all text elements with data-en / data-ar
    document.querySelectorAll('[data-en][data-ar]').forEach(el => {
      const text = arabic ? el.getAttribute('data-ar') : el.getAttribute('data-en');
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = text;
      } else {
        el.textContent = text;
      }
    });
  }
}

// ─── 4. MOBILE MENU ───
function initMobileMenu() {
  const hamburger = document.getElementById('hamburger');
  const drawer = document.getElementById('mobileDrawer');
  const overlay = document.getElementById('overlay');
  const drawerLinks = drawer.querySelectorAll('a');

  function openMenu() {
    hamburger.classList.add('active');
    drawer.classList.add('open');
    overlay.classList.add('active');
    overlay.style.display = 'block';
    document.body.style.overflow = 'hidden';
  }

  function closeMenu() {
    hamburger.classList.remove('active');
    drawer.classList.remove('open');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
    setTimeout(() => { overlay.style.display = 'none'; }, 300);
  }

  hamburger.addEventListener('click', () => {
    if (drawer.classList.contains('open')) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  overlay.addEventListener('click', closeMenu);

  drawerLinks.forEach(link => {
    link.addEventListener('click', closeMenu);
  });
}

// ─── 5. SMOOTH SCROLL ───
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      e.preventDefault();
      const target = document.querySelector(anchor.getAttribute('href'));
      if (target) {
        const offset = 80; // navbar height
        const top = target.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
}

// ─── 6. FRAMEWORK TIMELINE ───
function initFrameworkTimeline() {
  const nodes = document.querySelectorAll('.timeline-node');
  const detail = document.getElementById('frameworkDetail');
  const progress = document.getElementById('timelineProgress');

  const steps = [
    {
      number: '01',
      titleEn: 'Global Sourcing',
      titleAr: 'التوريد العالمي',
      textEn: 'We source premium FMCG products from our five key markets — the Philippines, India, Thailand, Vietnam, and Africa. Every product is vetted for quality, compliance, and market demand.',
      textAr: 'نورد منتجات استهلاكية متميزة من أسواقنا الخمسة الرئيسية — الفلبين والهند وتايلاند وفيتنام وأفريقيا. كل منتج يتم فحصه للجودة والامتثال ومتطلبات السوق.'
    },
    {
      number: '02',
      titleEn: 'Compliance & Registration',
      titleAr: 'الامتثال والتسجيل',
      textEn: 'Our regulatory team handles all UAE municipality approvals, product registration, labeling requirements, and documentation — ensuring every item is market-ready.',
      textAr: 'يتولى فريقنا التنظيمي جميع موافقات البلديات الإماراتية، تسجيل المنتجات، متطلبات العلامات، والوثائق — مما يضمن جاهزية كل منتج للسوق.'
    },
    {
      number: '03',
      titleEn: 'Warehousing & Inventory',
      titleAr: 'التخزين والمخزون',
      textEn: 'Strategically located warehouses with climate-controlled zones, FIFO inventory management, and real-time stock tracking across the UAE.',
      textAr: 'مستودعات ذات مواقع استراتيجية مع مناطق متحكّم بالمناخ، إدارة مخزون FIFO، وتتبع المخزون في الوقت الحقيقي عبر الإمارات.'
    },
    {
      number: '04',
      titleEn: 'Distribution & Delivery',
      titleAr: 'التوزيع والتسليم',
      textEn: 'A dedicated fleet covering all 7 Emirates with cold chain capability, same-day dispatch, and route-optimized delivery to retailers, HORECA, and wholesale points.',
      textAr: 'أسطول مخصص يغطي جميع الإمارات السبع مع قدرة سلسلة التبريد، إرسال في نفس اليوم، وتسليم محسّن المسار لتجار التجزئة والفنادق والجملة.'
    },
    {
      number: '05',
      titleEn: 'Retail Activation',
      titleAr: 'تفعيل المبيعات',
      textEn: 'We go beyond delivery — with in-store merchandising, promotional campaigns, planogram support, and brand activation to drive sell-through.',
      textAr: 'نتجاوز التسليم — مع تجارة داخل المتاجر، حملات ترويجية، دعم خطط العرض، وتفعيل العلامة التجارية لزيادة المبيعات.'
    }
  ];

  nodes.forEach((node, index) => {
    node.addEventListener('click', () => {
      setActiveStep(index);
    });
  });

  function setActiveStep(index) {
    const isArabic = document.documentElement.getAttribute('lang') === 'ar';

    // Update active node
    nodes.forEach(n => n.classList.remove('active'));
    nodes[index].classList.add('active');

    // Update progress
    if (progress) {
      const percent = (index / (steps.length - 1)) * 100;
      progress.style.width = percent + '%';
    }

    // Update detail card
    if (detail) {
      const step = steps[index];
      const titleEl = detail.querySelector('.framework-detail-title span:last-child');
      const numberEl = detail.querySelector('.framework-detail-number');
      const textEl = detail.querySelector('.framework-detail-text');

      if (numberEl) numberEl.textContent = step.number;
      if (titleEl) titleEl.textContent = isArabic ? step.titleAr : step.titleEn;
      if (textEl) textEl.textContent = isArabic ? step.textAr : step.textEn;

      // Animate detail card
      if (typeof gsap !== 'undefined') {
        gsap.fromTo(detail, { opacity: 0, y: 20 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' });
      }
    }
  }
}

// ─── 7. GSAP ANIMATIONS ───
function initGSAPAnimations() {
  gsap.registerPlugin(ScrollTrigger);

  // Mobile browsers resize the viewport when the address bar hides/shows
  // mid-scroll. Without this, ScrollTrigger treats that as a real resize
  // and recalculates every trigger's start/end position while the user
  // is actively scrolling — the #1 cause of stutter/jump on phones.
  ScrollTrigger.config({ ignoreMobileResize: true });

  // Hero animations
  animateHero();

  // Section reveals
  animateRevealElements();

  // Stat counters
  animateCounters();

  // Parallax effects
  animateParallax();

  // Timeline scroll progress
  animateTimelineScroll();
}

function animateHero() {
  const tl = gsap.timeline({ delay: 0.3 });

  tl.to('.hero-label', {
    opacity: 1,
    y: 0,
    duration: 0.6,
    ease: 'power2.out'
  })
  .to('.hero-title .word', {
    opacity: 1,
    y: 0,
    duration: 0.6,
    stagger: 0.1,
    ease: 'power3.out'
  }, '-=0.3')
  .to('.hero-subtitle', {
    opacity: 1,
    duration: 0.5,
    ease: 'power2.out'
  }, '-=0.2')
  .to('.hero-tagline', {
    opacity: 1,
    duration: 0.5,
    ease: 'power2.out'
  }, '-=0.2')
  .to('.hero-ctas', {
    opacity: 1,
    duration: 0.5,
    ease: 'power2.out'
  }, '-=0.2');
}

function animateRevealElements() {
  // Reveal from bottom
  // Cards inside .stagger-cards are animated by the stagger tween below —
  // tweening them here too made two tweens fight over the same transform
  // and cards could strand mid-flight (visible as an offset "orphan" card).
  // Apple-style deceleration — long, smooth settle rather than a snappy
  // stop. Paired with a subtle scale so cards feel like they're easing
  // into focus, not just sliding.
  const APPLE_EASE = 'cubic-bezier(.16,1,.3,1)';

  gsap.utils.toArray('.reveal-up').forEach(el => {
    if (el.closest('.stagger-cards')) return;
    gsap.fromTo(el,
      { y: 70, opacity: 0, scale: .97 },
      {
        y: 0,
        opacity: 1,
        scale: 1,
        duration: 1.1,
        ease: APPLE_EASE,
        scrollTrigger: {
          trigger: el,
          start: 'top 90%',
          toggleActions: 'play none none none'
        }
      }
    );
  });

  // Reveal from left
  gsap.utils.toArray('.reveal-left').forEach(el => {
    gsap.fromTo(el,
      { x: -60, opacity: 0, scale: .97 },
      {
        x: 0,
        opacity: 1,
        scale: 1,
        duration: 1.1,
        ease: APPLE_EASE,
        scrollTrigger: {
          trigger: el,
          start: 'top 87%',
          toggleActions: 'play none none none'
        }
      }
    );
  });

  // Reveal from right
  gsap.utils.toArray('.reveal-right').forEach(el => {
    gsap.fromTo(el,
      { x: 60, opacity: 0, scale: .97 },
      {
        x: 0,
        opacity: 1,
        scale: 1,
        duration: 1.1,
        ease: APPLE_EASE,
        scrollTrigger: {
          trigger: el,
          start: 'top 87%',
          toggleActions: 'play none none none'
        }
      }
    );
  });

  // Staggered cards — each card eases in slightly after the last, like
  // Apple's product-grid reveals, instead of popping in together.
  gsap.utils.toArray('.stagger-cards').forEach(container => {
    const cards = container.querySelectorAll('.card, .portfolio-card, .segment-card, .region-card, .stat-card-light, .vision-card, .contact-card');
    if (cards.length > 0) {
      gsap.fromTo(cards,
        { y: 70, opacity: 0, scale: .96 },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          duration: .9,
          stagger: 0.1,
          ease: APPLE_EASE,
          scrollTrigger: {
            trigger: container,
            start: 'top 85%',
            toggleActions: 'play none none none'
          }
        }
      );
    }
  });

  // Advantage items
  gsap.utils.toArray('.advantage-item').forEach((item, i) => {
    gsap.fromTo(item,
      { x: -40, opacity: 0 },
      {
        x: 0,
        opacity: 1,
        duration: 0.7,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: item,
          start: 'top 85%',
          toggleActions: 'play none none none'
        }
      }
    );
  });

  // Section labels & titles
  gsap.utils.toArray('.section-label').forEach(el => {
    gsap.fromTo(el,
      { x: -30, opacity: 0 },
      {
        x: 0,
        opacity: 1,
        duration: 0.5,
        ease: 'power2.out',
        scrollTrigger: {
          trigger: el,
          start: 'top 90%',
          toggleActions: 'play none none none'
        }
      }
    );
  });
}

function animateCounters() {
  const statNumbers = document.querySelectorAll('.stat-number[data-count]');

  statNumbers.forEach(el => {
    const target = parseInt(el.getAttribute('data-count'));
    const suffix = el.getAttribute('data-suffix') || '';
    const prefix = el.getAttribute('data-prefix') || '';

    ScrollTrigger.create({
      trigger: el,
      start: 'top 85%',
      onEnter: () => {
        gsap.to(el, {
          innerText: target,
          duration: 2,
          snap: { innerText: 1 },
          ease: 'power2.out',
          onUpdate: function() {
            el.textContent = prefix + Math.round(parseFloat(el.textContent)) + (suffix ? suffix : '+');
          },
          onComplete: function() {
            el.textContent = prefix + target + (suffix ? suffix : '+');
          }
        });
      },
      once: true
    });
  });
}

function animateParallax() {
  // Hero parallax disabled — content stays fixed inside hero section.
  // The movement + fade on scroll pushed text outside the hero boundary.
}

function animateTimelineScroll() {
  const progress = document.getElementById('timelineProgress');
  if (!progress) return;

  const timeline = document.querySelector('.timeline');
  if (!timeline) return;

  ScrollTrigger.create({
    trigger: timeline,
    start: 'top 80%',
    end: 'bottom 20%',
    onUpdate: (self) => {
      const percent = Math.min(self.progress * 100, 100);
      progress.style.width = percent + '%';

      // Activate nodes based on scroll progress
      const nodes = document.querySelectorAll('.timeline-node');
      const activeIndex = Math.min(Math.floor(self.progress * nodes.length), nodes.length - 1);

      nodes.forEach((node, i) => {
        if (i <= activeIndex) {
          node.classList.add('active');
        } else {
          node.classList.remove('active');
        }
      });
    }
  });
}

// ─── 8. FALLBACK (NO GSAP) ───
function showAllRevealElements() {
  document.querySelectorAll('.reveal-up, .reveal-left, .reveal-right, .reveal-scale').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'none';
  });

  document.querySelectorAll('.hero-label, .hero-title .word, .hero-subtitle, .hero-tagline, .hero-ctas').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'none';
  });
}

// ─── 9. BRAND FILTER ───
function initBrandFilter() {
  const filterBtns = document.querySelectorAll('.brand-filter-btn');
  const brandCards = document.querySelectorAll('.brand-card');
  if (!filterBtns.length || !brandCards.length) return;

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const filter = btn.dataset.filter;

      // Update active state
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      // Filter cards
      brandCards.forEach(card => {
        if (filter === 'all') {
          card.classList.remove('hidden');
        } else {
          const categories = card.dataset.category.split(' ');
          if (categories.includes(filter)) {
            card.classList.remove('hidden');
          } else {
            card.classList.add('hidden');
          }
        }
      });

      // Refresh ScrollTrigger after filter
      if (typeof ScrollTrigger !== 'undefined') {
        ScrollTrigger.refresh();
      }
    });
  });
}

// Init brand filter on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  initBrandFilter();
});
