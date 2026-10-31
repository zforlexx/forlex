/* ============================================================
   FORLEX · interacciones del sitio
   ============================================================ */
(function () {
    'use strict';

    const doc = document;
    const reduceMotionMQ = window.matchMedia('(prefers-reduced-motion: reduce)');
    let reduceMotion = reduceMotionMQ.matches;
    if (reduceMotion) doc.documentElement.classList.add('reduce-motion');

    const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

    const onMotionChange = function (e) {
        reduceMotion = e.matches;
        doc.documentElement.classList.toggle('reduce-motion', reduceMotion);
    };
    if (reduceMotionMQ.addEventListener) reduceMotionMQ.addEventListener('change', onMotionChange);
    else if (reduceMotionMQ.addListener) reduceMotionMQ.addListener(onMotionChange);

    const $  = function (sel, ctx) { return (ctx || doc).querySelector(sel); };
    const $$ = function (sel, ctx) { return Array.prototype.slice.call((ctx || doc).querySelectorAll(sel)); };

    /* =========================================================
       1. SONIDO — Web Audio sintetizado (sin archivos externos)
       ========================================================= */
    const Sound = {
        ctx: null,
        master: null,
        enabled: false,
        ready: false,

        init() {
            if (this.ready) return;
            const AC = window.AudioContext || window.webkitAudioContext;
            if (!AC) return;
            try { this.ctx = new AC(); } catch (e) { return; }
            this.master = this.ctx.createGain();
            this.master.gain.value = 0.28;
            this.master.connect(this.ctx.destination);
            this.ready = true;
        },

        unlock() {
            this.init();
            if (this.ctx && this.ctx.state === 'suspended') this.ctx.resume();
        },

        tone(freq, dur, type, gain, delay, sweepTo) {
            if (!this.enabled || !this.ready || !this.ctx) return;
            const t0 = this.ctx.currentTime + (delay || 0);
            const osc = this.ctx.createOscillator();
            const g = this.ctx.createGain();
            osc.type = type || 'sine';
            osc.frequency.setValueAtTime(freq, t0);
            if (sweepTo) osc.frequency.exponentialRampToValueAtTime(sweepTo, t0 + dur);
            g.gain.setValueAtTime(0.0001, t0);
            g.gain.exponentialRampToValueAtTime(gain || 0.1, t0 + 0.014);
            g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
            osc.connect(g); g.connect(this.master);
            osc.start(t0); osc.stop(t0 + dur + 0.03);
        },

        noise(dur, gain, freq) {
            if (!this.enabled || !this.ready || !this.ctx) return;
            const t0 = this.ctx.currentTime;
            const len = Math.max(1, Math.floor(this.ctx.sampleRate * dur));
            const buf = this.ctx.createBuffer(1, len, this.ctx.sampleRate);
            const d = buf.getChannelData(0);
            for (let i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / len);
            const src = this.ctx.createBufferSource(); src.buffer = buf;
            const lp = this.ctx.createBiquadFilter();
            lp.type = 'lowpass';
            lp.frequency.setValueAtTime(freq || 1400, t0);
            const g = this.ctx.createGain();
            g.gain.setValueAtTime(gain || 0.06, t0);
            g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
            src.connect(lp); lp.connect(g); g.connect(this.master);
            src.start(t0); src.stop(t0 + dur);
        },

        play(name) {
            if (!this.enabled || !this.ready) return;
            switch (name) {
                case 'hover': this.tone(920, 0.05, 'sine', 0.02); break;
                case 'click': this.tone(520, 0.07, 'triangle', 0.055); this.tone(1040, 0.09, 'sine', 0.03, 0.03); break;
                case 'toggle':
                    this.tone(560, 0.09, 'sine', 0.05);
                    this.tone(880, 0.13, 'sine', 0.045, 0.06);
                    this.tone(1320, 0.16, 'sine', 0.028, 0.12);
                    break;
                case 'open': this.tone(420, 0.5, 'sine', 0.045, 0, 1250); this.tone(210, 0.6, 'triangle', 0.035); break;
                case 'close': this.tone(860, 0.34, 'sine', 0.04, 0, 220); break;
                case 'success':
                    [[880, 0.11, 0], [1320, 0.13, 0.08], [1760, 0.22, 0.16]].forEach(function (n) {
                        Sound.tone(n[0], n[1], 'sine', 0.05, n[2]);
                    });
                    break;
                case 'whoosh': this.noise(0.32, 0.04, 1200); break;
            }
        }
    };

    const soundToggle = $('#soundToggle');

    function setSound(on, silent) {
        Sound.unlock();
        Sound.enabled = on;
        if (soundToggle) {
            soundToggle.classList.toggle('on', on);
            soundToggle.classList.remove('hint');
            soundToggle.setAttribute('aria-pressed', String(on));
            soundToggle.innerHTML = on
                ? '<i class="fas fa-volume-up"></i>'
                : '<i class="fas fa-volume-mute"></i>';
            soundToggle.title = on ? 'Silenciar sonidos de interfaz' : 'Activar sonidos de interfaz';
            soundToggle.setAttribute('aria-label', soundToggle.title);
        }
        try { localStorage.setItem('forlex:sound', on ? '1' : '0'); } catch (e) {}
        if (on && !silent) Sound.play('toggle');
    }

    if (soundToggle) {
        soundToggle.addEventListener('click', function (e) {
            e.stopPropagation();
            setSound(!Sound.enabled);
        });
    }

    let savedSound = null;
    try { savedSound = localStorage.getItem('forlex:sound'); } catch (e) {}
    if (savedSound === '0') setSound(false, true);
    else if (savedSound === '1') setSound(true, true);
    else if (soundToggle) soundToggle.title = 'Activar sonidos de interfaz';

    ['pointerdown', 'keydown', 'touchstart'].forEach(function (ev) {
        window.addEventListener(ev, function once() {
            Sound.unlock();
            ['pointerdown', 'keydown', 'touchstart'].forEach(function (e2) {
                window.removeEventListener(e2, once);
            });
        }, { passive: true });
    });

    /* =========================================================
       2. PROGRESO + NAVBAR + SCROLL TOP
       ========================================================= */
    const topbar   = $('#topbar');
    const progress = $('#progressBar');
    const toTop    = $('#toTop');
    let ticking = false;

    function onScroll() {
        const y   = window.scrollY || doc.documentElement.scrollTop;
        const max = doc.documentElement.scrollHeight - window.innerHeight;
        if (progress) progress.style.width = (max > 0 ? (y / max) * 100 : 0) + '%';
        if (topbar) topbar.classList.toggle('show', y > 180);
        if (toTop) toTop.classList.toggle('show', y > 700);
        ticking = false;
    }

    window.addEventListener('scroll', function () {
        if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
    }, { passive: true });

    onScroll();

    if (toTop) {
        toTop.addEventListener('click', function () {
            Sound.play('click');
            window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
        });
    }

    /* =========================================================
       3. REVEAL + STAGGER
       ========================================================= */
    $$('[data-stagger]').forEach(function (group) {
        Array.prototype.forEach.call(group.children, function (child, i) {
            if (!child.classList.contains('reveal')) child.classList.add('reveal');
            child.style.transitionDelay = Math.min(i * 65, 520) + 'ms';
        });
    });

    const revealEls = $$('.reveal');

    if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                const el = entry.target;
                if (entry.isIntersecting) {
                    el.classList.add('visible');
                    setTimeout(function () { el.style.willChange = 'auto'; }, 1000);
                } else if (entry.boundingClientRect.top > 0) {
                    el.classList.remove('visible');
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });
        revealEls.forEach(function (el) { io.observe(el); });
    } else {
        revealEls.forEach(function (el) { el.classList.add('visible'); });
    }

    /* =========================================================
       4. SCROLL SPY
       ========================================================= */
    const navLinkEls = $$('.nav-link');
    const sectionEls = navLinkEls
        .map(function (a) { return doc.querySelector(a.getAttribute('href')); })
        .filter(Boolean);

    if ('IntersectionObserver' in window && sectionEls.length) {
        const spy = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) return;
                navLinkEls.forEach(function (a) {
                    a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id);
                });
            });
        }, { rootMargin: '-45% 0px -50% 0px', threshold: 0 });
        sectionEls.forEach(function (s) { spy.observe(s); });
    }

    /* =========================================================
       5. CONTADORES
       ========================================================= */
    function animateCount(el) {
        if (el.dataset.done === '1') return;
        const target = parseFloat(el.getAttribute('data-count')) || 0;
        const suffix = el.getAttribute('data-suffix') || '';
        el.dataset.done = '1';
        if (reduceMotion) { el.textContent = target + suffix; return; }
        const dur = 1500;
        const start = performance.now();
        function step(now) {
            const p = Math.min((now - start) / dur, 1);
            const eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased) + suffix;
            if (p < 1) requestAnimationFrame(step);
            else el.textContent = target + suffix;
        }
        requestAnimationFrame(step);
    }

    if ('IntersectionObserver' in window) {
        const cio = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) { animateCount(e.target); cio.unobserve(e.target); }
            });
        }, { threshold: 0.5 });
        $$('[data-count]').forEach(function (el) { cio.observe(el); });
    } else {
        $$('[data-count]').forEach(animateCount);
    }

    /* =========================================================
       6. TYPEWRITER
       ========================================================= */
    const typedText = $('#typedText');
    const roles = [
        'Creador de Forlex Optimizer',
        'CEO de PracPvP',
        'Plugin Dev · Folia / Paper / Purpur',
        'Desarrollador de Bots de Discord',
        'Disponible para trabajos de Minecraft ($)'
    ];

    if (typedText) {
        if (reduceMotion) {
            typedText.textContent = roles[0];
        } else {
            let ri = 0, ci = 0, deleting = false;
            (function type() {
                const word = roles[ri];
                typedText.textContent = word.slice(0, ci);
                let delay = deleting ? 32 : 58;
                if (!deleting && ci === word.length) { deleting = true; delay = 1900; }
                else if (deleting && ci === 0) { deleting = false; ri = (ri + 1) % roles.length; delay = 320; }
                else { ci += deleting ? -1 : 1; }
                setTimeout(type, delay);
            })();
        }
    }

    /* =========================================================
       7. GLOW SIGUE AL PUNTERO
       ========================================================= */
    if (finePointer && !reduceMotion) {
        $$('.section, .exp-card, .feature, .dl-card').forEach(function (el) {
            el.addEventListener('pointermove', function (e) {
                const r = el.getBoundingClientRect();
                el.style.setProperty('--mx', (e.clientX - r.left) + 'px');
                el.style.setProperty('--my', (e.clientY - r.top) + 'px');
            });
        });
    }

    /* =========================================================
       8. CURSOR AURA + PARALAJE DEL MOCKUP + ANILLO DE SALUD
       ========================================================= */
    const aura = $('#cursorAura');
    if (aura && finePointer && !reduceMotion) {
        let ax = window.innerWidth / 2, ay = window.innerHeight / 2, cx = ax, cy = ay;
        window.addEventListener('pointermove', function (e) {
            ax = e.clientX; ay = e.clientY;
            aura.style.opacity = '1';
        }, { passive: true });
        (function loopAura() {
            cx += (ax - cx) * 0.12;
            cy += (ay - cy) * 0.12;
            aura.style.transform = 'translate3d(' + cx + 'px,' + cy + 'px,0)';
            requestAnimationFrame(loopAura);
        })();
    }

    const mockupFrame = $('.mockup-frame');
    if (mockupFrame && finePointer && !reduceMotion) {
        window.addEventListener('pointermove', function (e) {
            const x = (e.clientX / window.innerWidth - 0.5);
            const y = (e.clientY / window.innerHeight - 0.5);
            mockupFrame.style.setProperty('--ry', (-3 + x * 6).toFixed(2) + 'deg');
            mockupFrame.style.setProperty('--rx', (2 - y * 5).toFixed(2) + 'deg');
        }, { passive: true });
    }

    const healthRing = $('#healthRing');
    if (healthRing) {
        if (reduceMotion || !('IntersectionObserver' in window)) {
            healthRing.classList.add('visible');
        } else {
            const rio = new IntersectionObserver(function (entries) {
                entries.forEach(function (en) {
                    if (en.isIntersecting) { healthRing.classList.add('visible'); rio.unobserve(en.target); }
                });
            }, { threshold: 0.4 });
            rio.observe(healthRing);
        }
    }

    /* =========================================================
       9. PARTÍCULAS
       ========================================================= */
    const canvas = $('#particles');
    if (canvas && !reduceMotion) {
        const ctx2d = canvas.getContext('2d');
        let dpr = Math.min(window.devicePixelRatio || 1, 2);
        let w = 0, h = 0, parts = [];
        const mouse = { x: -9999, y: -9999 };

        function resize() {
            w = canvas.width  = Math.floor(window.innerWidth  * dpr);
            h = canvas.height = Math.floor(window.innerHeight * dpr);
            canvas.style.width = window.innerWidth + 'px';
            canvas.style.height = window.innerHeight + 'px';
            const base = Math.round((window.innerWidth * window.innerHeight) / 28000);
            const count = Math.max(20, Math.min(base, 80));
            parts = [];
            for (let i = 0; i < count; i++) {
                parts.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    vx: (Math.random() - 0.5) * 0.26 * dpr,
                    vy: (Math.random() - 0.5) * 0.26 * dpr,
                    r: (Math.random() * 1.6 + 0.6) * dpr,
                    hue: Math.random() > 0.45 ? 162 : 188
                });
            }
        }

        window.addEventListener('resize', function () {
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            resize();
        });

        if (finePointer) {
            window.addEventListener('pointermove', function (e) {
                mouse.x = e.clientX * dpr; mouse.y = e.clientY * dpr;
            }, { passive: true });
        }

        function draw() {
            ctx2d.clearRect(0, 0, w, h);
            for (let i = 0; i < parts.length; i++) {
                const p = parts[i];
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
                if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;

                const dx = p.x - mouse.x, dy = p.y - mouse.y;
                const d2 = dx * dx + dy * dy;
                if (d2 < 18000 * dpr) {
                    const f = (1 - d2 / (18000 * dpr)) * 0.5;
                    p.x += dx * f * 0.05; p.y += dy * f * 0.05;
                }

                ctx2d.beginPath();
                ctx2d.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx2d.fillStyle = 'hsla(' + p.hue + ', 85%, 62%, 0.5)';
                ctx2d.fill();
            }

            for (let i = 0; i < parts.length; i++) {
                for (let j = i + 1; j < parts.length; j++) {
                    const a = parts[i], b = parts[j];
                    const dx = a.x - b.x, dy = a.y - b.y;
                    const d2 = dx * dx + dy * dy;
                    const lim = 13000 * dpr;
                    if (d2 < lim) {
                        ctx2d.beginPath();
                        ctx2d.strokeStyle = 'rgba(16,185,129,' + (0.13 * (1 - d2 / lim)) + ')';
                        ctx2d.lineWidth = dpr * 0.7;
                        ctx2d.moveTo(a.x, a.y); ctx2d.lineTo(b.x, b.y);
                        ctx2d.stroke();
                    }
                }
            }
            requestAnimationFrame(draw);
        }

        resize();
        requestAnimationFrame(draw);
    }

    /* =========================================================
       10. RIPPLE + SONIDOS DE INTERACCIÓN
       ========================================================= */
    function addRipple(el, e) {
        if (reduceMotion) return;
        const r = el.getBoundingClientRect();
        const size = Math.max(r.width, r.height);
        const span = doc.createElement('span');
        span.className = 'ripple';
        span.style.width = span.style.height = size + 'px';
        span.style.left = (e.clientX - r.left - size / 2) + 'px';
        span.style.top  = (e.clientY - r.top  - size / 2) + 'px';
        el.appendChild(span);
        setTimeout(function () { span.remove(); }, 780);
    }

    if (finePointer) {
        $$('a, button, [role="button"], .bot-feature, .exp-card, .stat, .feature, .gal-tab').forEach(function (el) {
            let last = 0;
            el.addEventListener('pointerenter', function () {
                const now = performance.now();
                if (now - last < 70) return;
                last = now;
                Sound.play('hover');
            });
        });
    }

    $$('a[data-sound], button[data-sound], [role="button"][data-sound]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            Sound.play('click');
            addRipple(el, e);
        });
    });

    /* =========================================================
       11. TOAST + COPIAR + CONFETTI
       ========================================================= */
    const toast = $('#toast');
    const toastText = $('#toastText');
    let toastTimer = null;

    function showToast(msg, icon) {
        if (!toast || !toastText) return;
        toastText.textContent = msg;
        const ic = toast.querySelector('i');
        if (ic) ic.className = icon || 'fas fa-check';
        toast.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 2300);
    }

    function confetti(x, y) {
        if (reduceMotion) return;
        const supportsWAAPI = typeof Element !== 'undefined' && Element.prototype.animate;
        const colors = ['#10b981', '#34d399', '#06b6d4', '#22d3ee', '#8b5cf6', '#ffffff'];
        for (let i = 0; i < 24; i++) {
            const p = doc.createElement('div');
            p.className = 'confetti-piece';
            p.style.left = x + 'px';
            p.style.top = y + 'px';
            p.style.background = colors[i % colors.length];
            p.style.transform = 'translate(-50%,-50%)';
            doc.body.appendChild(p);

            const ang = Math.random() * Math.PI * 2;
            const dist = 60 + Math.random() * 160;
            const dx = Math.cos(ang) * dist;
            const dy = Math.sin(ang) * dist - 40;

            if (supportsWAAPI) {
                p.animate([
                    { transform: 'translate(-50%,-50%) rotate(0deg)', opacity: 1 },
                    { transform: 'translate(calc(-50% + ' + dx + 'px), calc(-50% + ' + dy + 'px)) rotate(' + (Math.random() * 720 - 360) + 'deg)', opacity: 0 }
                ], {
                    duration: 850 + Math.random() * 500,
                    easing: 'cubic-bezier(0.16,1,0.3,1)'
                }).onfinish = function () { p.remove(); };
            } else {
                p.style.transition = 'transform 1s cubic-bezier(0.16,1,0.3,1), opacity 1s ease';
                requestAnimationFrame(function () {
                    p.style.transform = 'translate(calc(-50% + ' + dx + 'px), calc(-50% + ' + dy + 'px)) rotate(' + (Math.random() * 720 - 360) + 'deg)';
                    p.style.opacity = '0';
                });
                setTimeout(function () { p.remove(); }, 1200);
            }
        }
    }

    function copyText(text, el) {
        function done() {
            Sound.play('success');
            showToast('Copiado: ' + text, 'fas fa-clipboard-check');
            if (el) {
                const r = el.getBoundingClientRect();
                confetti(r.left + r.width / 2, r.top + r.height / 2);
                if (el.classList.contains('copy-btn') || el.classList.contains('copy-mini')) {
                    el.classList.add('done');
                    el.innerHTML = '<i class="fas fa-check"></i>';
                    setTimeout(function () {
                        el.classList.remove('done');
                        el.innerHTML = '<i class="fas fa-copy"></i>';
                    }, 1600);
                }
            }
        }

        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(done).catch(fallback);
        } else { fallback(); }

        function fallback() {
            try {
                const ta = doc.createElement('textarea');
                ta.value = text;
                ta.setAttribute('readonly', '');
                ta.style.position = 'fixed';
                ta.style.opacity = '0';
                doc.body.appendChild(ta);
                ta.select();
                doc.execCommand('copy');
                ta.remove();
                done();
            } catch (e) {
                showToast('No se pudo copiar', 'fas fa-triangle-exclamation');
            }
        }
    }

    $$('[data-copy]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            if (e.target.closest && e.target.closest('.copy-btn') && e.target.closest('.copy-btn') !== el) return;
            copyText(el.getAttribute('data-copy'), el);
        });
        el.addEventListener('keydown', function (e) {
            if ((e.key === 'Enter' || e.key === ' ') && el.getAttribute('role') === 'button') {
                e.preventDefault();
                copyText(el.getAttribute('data-copy'), el);
            }
        });
    });

    /* =========================================================
       12. LIGHTBOX
       ========================================================= */
    const modal     = $('#imageModal');
    const modalImg  = $('#modalImage');
    const modalCap  = $('#modalCap');
    const modalPrev = $('#modalPrev');
    const modalNext = $('#modalNext');
    const closeBtn  = $('#closeModal');
    let lastFocus = null;
    let lightboxList = null;   // [{src, cap}] cuando se abre desde la galería
    let lightboxIndex = 0;

    function renderLightbox() {
        if (!lightboxList) return;
        const item = lightboxList[lightboxIndex];
        if (!item || !modalImg) return;
        modalImg.src = item.src;
        modalImg.alt = item.cap || 'Captura de Forlex Optimizer';
        if (modalCap) modalCap.textContent = item.cap || '';
        const multi = lightboxList.length > 1;
        if (modalPrev) modalPrev.style.display = multi ? 'grid' : 'none';
        if (modalNext) modalNext.style.display = multi ? 'grid' : 'none';
    }

    function openLightbox(src, caption, list, index) {
        if (!modal || !modalImg) return;
        lastFocus = doc.activeElement;
        if (list && list.length) {
            lightboxList = list;
            lightboxIndex = index >= 0 ? index : 0;
            renderLightbox();
        } else {
            lightboxList = null;
            modalImg.src = src;
            modalImg.alt = caption || 'Captura de Forlex Optimizer';
            if (modalCap) modalCap.textContent = caption || '';
            if (modalPrev) modalPrev.style.display = 'none';
            if (modalNext) modalNext.style.display = 'none';
        }
        modal.classList.add('show');
        doc.body.style.overflow = 'hidden';
        Sound.play('open');
        if (closeBtn) closeBtn.focus();
    }

    function closeLightbox() {
        if (!modal || !modal.classList.contains('show')) return;
        modal.classList.remove('show');
        doc.body.style.overflow = '';
        Sound.play('close');
        if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function stepLightbox(dir) {
        if (!lightboxList || lightboxList.length < 2) return;
        lightboxIndex = (lightboxIndex + dir + lightboxList.length) % lightboxList.length;
        renderLightbox();
        syncGalleryFromLightbox();
        Sound.play('click');
    }

    if (modal) {
        modal.addEventListener('click', function (e) {
            if (e.target === modal) closeLightbox();
        });
    }
    if (modalImg) modalImg.addEventListener('click', closeLightbox);
    if (closeBtn) closeBtn.addEventListener('click', closeLightbox);
    if (modalPrev) modalPrev.addEventListener('click', function (e) { e.stopPropagation(); stepLightbox(-1); });
    if (modalNext) modalNext.addEventListener('click', function (e) { e.stopPropagation(); stepLightbox(1); });

    doc.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeLightbox();
        if (!modal || !modal.classList.contains('show')) return;
        if (e.key === 'ArrowLeft') stepLightbox(-1);
        if (e.key === 'ArrowRight') stepLightbox(1);
    });

    /* Avatar: se abre en el lightbox */
    const avatar = $('#avatar');
    if (avatar) {
        avatar.addEventListener('click', function () {
            Sound.play('click');
            openLightbox(avatar.getAttribute('data-full'), 'Forlex', null, 0);
        });
        avatar.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openLightbox(avatar.getAttribute('data-full'), 'Forlex', null, 0);
            }
        });
    }

    /* Capturas sueltas con data-lightbox */
    $$('[data-lightbox]').forEach(function (el) {
        el.addEventListener('click', function () {
            Sound.play('click');
            openLightbox(el.getAttribute('data-lightbox'), el.getAttribute('data-caption') || '');
        });
    });

    /* =========================================================
       13. GALERÍA DEL OPTIMIZADOR
       ========================================================= */
    const galleryTabs  = $$('.gal-tab');
    const galleryImg   = $('#galleryImg');
    const galleryStage = $('#galleryStage');
    const galleryCap   = $('#galleryCap');
    const galleryThumbs = $('#galleryThumbs');
    const galPrev = $('#galPrev');
    const galNext = $('#galNext');
    let galleryIndex = 0;
    let galleryTimer = null;

    const galleryItems = galleryTabs.map(function (tab) {
        return {
            src: tab.getAttribute('data-src'),
            cap: tab.getAttribute('data-cap') || '',
            tab: tab
        };
    });

    function syncGalleryFromLightbox() {
        if (!lightboxList || lightboxList.length < 2) return;
        const item = lightboxList[lightboxIndex];
        const idx = galleryItems.findIndex(function (g) { return g.src === item.src; });
        if (idx >= 0) selectGallery(idx, true);
    }

    function selectGallery(idx, silent) {
        if (!galleryItems.length) return;
        galleryIndex = (idx + galleryItems.length) % galleryItems.length;
        const item = galleryItems[galleryIndex];

        if (galleryStage) galleryStage.classList.add('is-swapping');
        clearTimeout(galleryTimer);
        galleryTimer = setTimeout(function () {
            if (galleryImg) {
                galleryImg.src = item.src;
                galleryImg.alt = item.cap;
            }
            if (galleryCap) galleryCap.textContent = item.cap;
            if (galleryStage) galleryStage.classList.remove('is-swapping');
        }, reduceMotion ? 0 : 180);

        galleryItems.forEach(function (g, i) {
            if (g.tab) {
                g.tab.classList.toggle('active', i === galleryIndex);
                g.tab.setAttribute('aria-selected', String(i === galleryIndex));
            }
        });

        if (galleryThumbs) {
            Array.prototype.forEach.call(galleryThumbs.children, function (th, i) {
                th.classList.toggle('active', i === galleryIndex);
            });
            const active = galleryThumbs.children[galleryIndex];
            if (active && active.scrollIntoView && !silent) {
                active.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'nearest', inline: 'center' });
            }
        }
        if (!silent) Sound.play('click');
    }

    if (galleryTabs.length) {
        galleryTabs.forEach(function (tab, i) {
            tab.addEventListener('click', function () {
                if (i === galleryIndex) {
                    openLightbox(galleryItems[i].src, galleryItems[i].cap, galleryItems, i);
                    return;
                }
                selectGallery(i);
            });
        });

        if (galleryThumbs) {
            galleryItems.forEach(function (item, i) {
                const th = doc.createElement('button');
                th.type = 'button';
                th.className = 'gal-thumb' + (i === 0 ? ' active' : '');
                th.setAttribute('aria-label', 'Ver captura: ' + item.cap);
                const im = doc.createElement('img');
                im.src = item.src;
                im.alt = '';
                im.loading = 'lazy';
                im.decoding = 'async';
                th.appendChild(im);
                th.addEventListener('click', function () {
                    if (i === galleryIndex) openLightbox(galleryItems[i].src, galleryItems[i].cap, galleryItems, i);
                    else selectGallery(i);
                });
                galleryThumbs.appendChild(th);
            });
        }

        if (galPrev) galPrev.addEventListener('click', function () { selectGallery(galleryIndex - 1); });
        if (galNext) galNext.addEventListener('click', function () { selectGallery(galleryIndex + 1); });

        if (galleryImg) {
            galleryImg.addEventListener('click', function () {
                openLightbox(galleryItems[galleryIndex].src, galleryItems[galleryIndex].cap, galleryItems, galleryIndex);
            });
        }
        if (galleryStage) {
            galleryStage.querySelectorAll('img').forEach(function (im) {
                im.addEventListener('click', function (e) {
                    e.stopPropagation();
                    openLightbox(galleryItems[galleryIndex].src, galleryItems[galleryIndex].cap, galleryItems, galleryIndex);
                });
            });
        }

        let touchX = null;
        if (galleryStage) {
            galleryStage.addEventListener('touchstart', function (e) {
                touchX = e.changedTouches[0].clientX;
            }, { passive: true });
            galleryStage.addEventListener('touchend', function (e) {
                if (touchX === null) return;
                const dx = e.changedTouches[0].clientX - touchX;
                if (Math.abs(dx) > 55) selectGallery(galleryIndex + (dx < 0 ? 1 : -1));
                touchX = null;
            }, { passive: true });
        }
    }

    /* =========================================================
       14. FAQ (acordeón)
       ========================================================= */
    $$('.faq-item').forEach(function (item) {
        const btn = item.querySelector('.faq-q');
        if (!btn) return;
        btn.addEventListener('click', function () {
            const isOpen = item.classList.contains('open');
            $$('.faq-item').forEach(function (other) {
                other.classList.remove('open');
                const b = other.querySelector('.faq-q');
                if (b) b.setAttribute('aria-expanded', 'false');
            });
            if (!isOpen) {
                item.classList.add('open');
                btn.setAttribute('aria-expanded', 'true');
                Sound.play('click');
            }
        });
    });

    /* =========================================================
       15. MARQUEE DE CATEGORÍAS (duplicado para bucle continuo)
       ========================================================= */
    const catTrack = $('#catTrack');
    if (catTrack && !reduceMotion) {
        catTrack.innerHTML += catTrack.innerHTML;
    }

    /* =========================================================
       16. NAVEGACIÓN INTERNA SUAVE
       ========================================================= */
    $$('a[href^="#"]').forEach(function (a) {
        a.addEventListener('click', function (e) {
            const href = a.getAttribute('href');
            if (!href || href === '#') return;
            const target = doc.querySelector(href);
            if (!target) return;
            e.preventDefault();
            Sound.play('click');
            const top = target.getBoundingClientRect().top + window.scrollY - 82;
            window.scrollTo({ top: top, behavior: reduceMotion ? 'auto' : 'smooth' });
            history.replaceState(null, '', href);
        });
    });

    /* =========================================================
       17. DETALLES FINALES
       ========================================================= */
    const yearEl = $('#year');
    if (yearEl) yearEl.textContent = new Date().getFullYear();

    window.addEventListener('load', function () {
        setTimeout(onScroll, 120);
    });

    if (savedSound === null && soundToggle) {
        setTimeout(function () {
            if (!soundToggle.classList.contains('on')) soundToggle.classList.remove('hint');
        }, 12000);
    }
})();
