(function () {
  const DATA = window.UTS_DATA;
  const SVGS = window.UTS_SVGS || {};

  const stage = document.getElementById('stage');
  const topnav = document.getElementById('topnav');
  const btnHome = document.getElementById('btn-home');
  const crumbSep = document.getElementById('crumb-sep');
  const crumbCurrent = document.getElementById('crumb-current');
  const portal = document.getElementById('zoom-portal');

  const lightbox = document.getElementById('lightbox');
  const lbTitle = document.getElementById('lightbox-title');
  const lbBody = document.getElementById('lightbox-body');
  const lbPct = document.getElementById('lb-pct');
  let lbZoom = 100;
  let lbBaseWidth = 0;

  let currentView = 'generale';
  let timelineFilter = 'tutte';
  let timelineNewestFirst = true;
  let animating = false;
  let flowEnabled = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (!flowEnabled) document.body.classList.add('no-flow');

  function syncFlowButtons() {
    document.body.classList.toggle('no-flow', !flowEnabled);
    document.querySelectorAll('.btn-flow').forEach((btn) => {
      btn.classList.toggle('active', flowEnabled);
      btn.setAttribute('aria-pressed', String(flowEnabled));
      const lbl = btn.querySelector('.flow-lbl');
      if (lbl) lbl.textContent = flowEnabled ? 'Flusso' : 'Flusso off';
    });
  }

  // --- Flusso animato sulle frecce D2 (dash su tratteggiate, impulso luminoso su continue) ---
  function enhanceSvgFlow(svgEl, diagramId) {
    if (!svgEl || diagramId === 'database') return;
    const SVG_NS = 'http://www.w3.org/2000/svg';
    const paths = svgEl.querySelectorAll('path.connection[marker-end], path.connection[marker-start]');
    let pulseIdx = 0;

    paths.forEach((p) => {
      if (p.closest('.invisibile')) return;
      const inlineStyle = p.getAttribute('style') || '';
      if (/opacity\s*:\s*0(?:\D|$)/.test(inlineStyle)) return;

      const hasEnd = Boolean(p.getAttribute('marker-end'));
      const hasStart = Boolean(p.getAttribute('marker-start'));
      const reverse = hasStart && !hasEnd;
      const isDashed = /stroke-dasharray/i.test(inlineStyle) || p.hasAttribute('stroke-dasharray');

      if (isDashed) {
        p.classList.add('uts-dash-anim');
        if (reverse) p.classList.add('rev');
        return;
      }

      // Freccia continua: clona un impulso luminoso che scorre lungo il percorso a 90°
      let len = 0;
      try {
        len = p.getTotalLength();
      } catch {
        len = 0;
      }
      if (!Number.isFinite(len) || len < 16) return;

      const pulseLen = Math.min(26, Math.max(10, Math.round(len * 0.16)));
      const gapLen = Math.max(len + 48, 180);
      const cycle = pulseLen + gapLen;
      const dur = Math.min(4.6, Math.max(1.7, len / 120)).toFixed(2);
      const delay = -((pulseIdx * 0.45) % Number(dur)).toFixed(2);
      pulseIdx += 1;

      const strokeColor = p.getAttribute('stroke') || '#38BDF8';
      const pulse = document.createElementNS(SVG_NS, 'path');
      pulse.setAttribute('d', p.getAttribute('d') || '');
      pulse.setAttribute('class', reverse ? 'uts-flow-pulse rev' : 'uts-flow-pulse');
      pulse.setAttribute('stroke', strokeColor);
      pulse.setAttribute('stroke-width', '3.2');
      pulse.setAttribute('stroke-dasharray', `${pulseLen} ${gapLen}`);
      const mask = p.getAttribute('mask');
      if (mask) pulse.setAttribute('mask', mask);

      pulse.style.color = strokeColor;
      pulse.style.setProperty('--flow-start', `${pulseLen}`);
      pulse.style.setProperty('--flow-end', `${-(cycle - pulseLen)}`);
      pulse.style.setProperty('--flow-dur', `${dur}s`);
      pulse.style.setProperty('--flow-delay', `${delay}s`);

      p.parentNode.insertBefore(pulse, p.nextSibling);
    });
  }

  // --- Drag-to-pan nei contenitori diagramma (lascia intatti i clic sui nodi <a>) ---
  function setupDragPan(viewportEl) {
    if (!viewportEl) return;
    let pointerDown = false;
    let dragging = false;
    let startX = 0;
    let startY = 0;
    let startScrollL = 0;
    let startScrollT = 0;

    const refreshPannable = () => {
      const canScroll =
        viewportEl.scrollWidth > viewportEl.clientWidth + 4 ||
        viewportEl.scrollHeight > viewportEl.clientHeight + 4;
      viewportEl.classList.toggle('pannable', canScroll);
    };

    viewportEl.addEventListener('pointerdown', (ev) => {
      if (ev.button !== 0) return;
      refreshPannable();
      if (!viewportEl.classList.contains('pannable')) return;
      pointerDown = true;
      dragging = false;
      startX = ev.clientX;
      startY = ev.clientY;
      startScrollL = viewportEl.scrollLeft;
      startScrollT = viewportEl.scrollTop;
    });

    viewportEl.addEventListener('pointermove', (ev) => {
      if (!pointerDown) return;
      const dx = ev.clientX - startX;
      const dy = ev.clientY - startY;
      if (!dragging && Math.hypot(dx, dy) > 5) {
        dragging = true;
        viewportEl.classList.add('panning');
        try {
          viewportEl.setPointerCapture(ev.pointerId);
        } catch {
          // ignora se pointerId non catturabile
        }
      }
      if (dragging) {
        viewportEl.scrollLeft = startScrollL - dx;
        viewportEl.scrollTop = startScrollT - dy;
      }
    });

    const endPan = (ev) => {
      if (!pointerDown) return;
      pointerDown = false;
      viewportEl.classList.remove('panning');
      if (dragging) {
        try {
          if (viewportEl.hasPointerCapture(ev.pointerId)) {
            viewportEl.releasePointerCapture(ev.pointerId);
          }
        } catch {
          // ignora
        }
        const suppress = (clickEv) => {
          clickEv.preventDefault();
          clickEv.stopPropagation();
        };
        viewportEl.addEventListener('click', suppress, { capture: true, once: true });
        setTimeout(() => viewportEl.removeEventListener('click', suppress, { capture: true }), 80);
      }
      dragging = false;
    };

    viewportEl.addEventListener('pointerup', endPan);
    viewportEl.addEventListener('pointercancel', endPan);

    return refreshPannable;
  }

  function extractAccent(anchor) {
    const shape = anchor.querySelector('.shape rect, .shape path, .shape ellipse, rect, path');
    const stroke = shape?.getAttribute('stroke');
    if (stroke && /^#[0-9a-f]{3,8}$/i.test(stroke)) return stroke;
    return '#38bdf8';
  }

  // --- Colorazione sintassi leggera (offline, zero dipendenze) ---
  function escapeHtml(str) {
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function highlightCode(raw, lang) {
    let html = escapeHtml(raw);
    const placeholders = [];
    const stash = (cls, text) => {
      const idx = placeholders.length;
      placeholders.push(`<span class="${cls}">${text}</span>`);
      return `\u0000${idx}\u0000`;
    };

    // Commenti
    if (lang === 'sql') {
      html = html.replace(/(--[^\n]*)/g, (_, m) => stash('tok-com', m));
    } else if (lang === 'python' || lang === 'yaml') {
      html = html.replace(/(#[^\n]*)/g, (_, m) => stash('tok-com', m));
    } else {
      html = html.replace(/(\/\/[^\n]*)/g, (_, m) => stash('tok-com', m));
    }

    // Stringhe
    html = html.replace(/('[^'\n]*'|"[^"\n]*"|`[^`\n]*`)/g, (_, m) => stash('tok-str', m));

    // Parole chiave
    const kwMap = {
      sql: /\b(CREATE|TABLE|PRIMARY|KEY|NOT|NULL|UNIQUE|REFERENCES|CHECK|IN|DEFAULT|GENERATED|BY|AS|IDENTITY|SELECT|FROM|WITH|FORMAT|HEADER|match)\b/g,
      js: /\b(export|function|return|const|let|async|await|if|try|catch|throw|new|import|from)\b/g,
      jsx: /\b(export|default|function|return|const|let|if|import|from)\b/g,
      python: /\b(def|return|if|raise|import|from|as|not|in)\b/g,
      yaml: /\b(name|if|run|uses|with|on|jobs|steps)\b(?=:)/g,
      json: /\b(true|false|null)\b/g
    };
    const kwRe = kwMap[lang];
    if (kwRe) {
      html = html.replace(kwRe, (m) => `<span class="tok-kw">${m}</span>`);
    }

    // Numeri
    html = html.replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="tok-num">$1</span>');

    return html.replace(/\u0000(\d+)\u0000/g, (_, idx) => placeholders[Number(idx)]);
  }

  // --- Navigazione superiore ---
  function renderTopnav() {
    topnav.innerHTML = DATA.navOrder
      .map(
        (item) =>
          `<button type="button" class="nav-pill ${item.id === currentView ? 'active' : ''}" data-view="${item.id}">${item.label}</button>`
      )
      .join('');

    topnav.querySelectorAll('.nav-pill').forEach((btn) => {
      btn.addEventListener('click', () => navigateTo(btn.dataset.view, btn.getBoundingClientRect()));
    });

    if (currentView === 'generale') {
      crumbSep.hidden = true;
      crumbCurrent.hidden = true;
    } else {
      const info = DATA.navOrder.find((n) => n.id === currentView);
      crumbSep.hidden = false;
      crumbCurrent.hidden = false;
      crumbCurrent.textContent = info ? info.label : currentView;
    }
  }

  // --- Animazione "esplosione" (Opzione A) dal riquadro cliccato ---
  function navigateTo(targetId, sourceRect = null, pushHash = true, accentColor = null) {
    if (!DATA.views[targetId] || targetId === currentView || animating) return;
    animating = true;

    const goingBack = targetId === 'generale';

    if (sourceRect && !goingBack && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const targetInfo = DATA.navOrder.find((n) => n.id === targetId);
      portal.textContent = targetInfo ? targetInfo.label : '';
      portal.style.setProperty('--portal-accent', accentColor || '#38bdf8');
      portal.hidden = false;
      portal.style.transition = 'none';
      portal.style.top = `${sourceRect.top}px`;
      portal.style.left = `${sourceRect.left}px`;
      portal.style.width = `${Math.max(40, sourceRect.width)}px`;
      portal.style.height = `${Math.max(30, sourceRect.height)}px`;
      portal.style.opacity = '0.95';
      portal.getBoundingClientRect(); // forza reflow

      const stageRect = stage.getBoundingClientRect();
      const targetW = Math.min(window.innerWidth - 32, Math.max(stageRect.width, 640));
      const targetLeft = (window.innerWidth - targetW) / 2;

      portal.style.transition = '';
      stage.classList.add('exiting-in');
      requestAnimationFrame(() => {
        portal.style.top = '72px';
        portal.style.left = `${targetLeft}px`;
        portal.style.width = `${targetW}px`;
        portal.style.height = `${Math.min(window.innerHeight - 100, 620)}px`;
        portal.style.opacity = '0';
      });

      setTimeout(() => {
        portal.hidden = true;
        finishSwitch(targetId, goingBack, pushHash);
      }, 280);
    } else {
      stage.classList.add(goingBack ? 'exiting-out' : 'exiting-in');
      setTimeout(() => {
        finishSwitch(targetId, goingBack, pushHash);
      }, 170);
    }
  }

  function finishSwitch(targetId, goingBack, pushHash) {
    currentView = targetId;
    if (pushHash) {
      const nextHash = targetId === 'generale' ? '#generale' : `#${targetId}`;
      if (window.location.hash !== nextHash) {
        history.pushState(null, '', nextHash);
      }
    }
    renderTopnav();
    renderStage(goingBack ? 'entering-out' : 'entering-in');
    window.scrollTo({ top: 0, behavior: 'instant' });
    setTimeout(() => {
      stage.classList.remove('entering-in', 'entering-out');
      animating = false;
    }, 350);
  }

  // --- Inserimento SVG inline con centratura e click intercettati ---
  function mountDiagram(container, diagramSpec) {
    const svgMarkup = SVGS[diagramSpec.id];
    if (!svgMarkup) {
      container.innerHTML = `<p class="section-hint">Diagramma "${diagramSpec.id}" non compilato. Lancia <code>./compila.sh</code>.</p>`;
      return;
    }

    const card = document.createElement('div');
    card.className = 'diagram-card';
    const supportsFlow = diagramSpec.id !== 'database';
    card.innerHTML = `
      <div class="diagram-bar">
        <span class="diagram-caption">
          <span>${diagramSpec.caption}</span>
          ${diagramSpec.hint ? `<span class="hint-chip">${diagramSpec.hint}</span>` : ''}
        </span>
        <div class="zoom-controls">
          ${
            supportsFlow
              ? `<button type="button" class="btn-flow ${flowEnabled ? 'active' : ''}" data-z="flow" aria-pressed="${flowEnabled}" title="Attiva o ferma il flusso animato sulle frecce"><span class="flow-dot" aria-hidden="true"></span><span class="flow-lbl">${flowEnabled ? 'Flusso' : 'Flusso off'}</span></button>`
              : ''
          }
          <button type="button" data-z="out" title="Rimpicciolisci">−</button>
          <span class="zoom-pct">Adatta</span>
          <button type="button" data-z="in" title="Ingrandisci">+</button>
          <button type="button" data-z="fit" title="Adatta alla pagina">Adatta</button>
          <button type="button" data-z="full" title="Apri a schermo intero">Espandi</button>
        </div>
      </div>
      <div class="diagram-viewport">
        <div class="diagram-inner"></div>
      </div>
    `;

    const viewport = card.querySelector('.diagram-viewport');
    const inner = card.querySelector('.diagram-inner');
    inner.innerHTML = svgMarkup;

    const svgEl = inner.querySelector(':scope > svg');
    let naturalWidth = 1000;
    if (svgEl) {
      const vb = svgEl.getAttribute('viewBox');
      if (vb) {
        const parts = vb.trim().split(/\s+/).map(Number);
        if (parts.length === 4 && parts[2] > 0) naturalWidth = parts[2];
      }
      svgEl.removeAttribute('width');
      svgEl.removeAttribute('height');
      svgEl.style.width = '100%';
      svgEl.style.maxWidth = `${Math.min(naturalWidth, 1160)}px`;
      svgEl.style.height = 'auto';

      // Rende i link interni (#backend, #database...) animati e apre quelli esterni in nuova scheda
      svgEl.querySelectorAll('a').forEach((anchor) => {
        const href = anchor.getAttribute('href') || anchor.getAttribute('xlink:href') || '';
        if (href.startsWith('#')) {
          const targetId = href.slice(1);
          anchor.addEventListener('click', (ev) => {
            ev.preventDefault();
            navigateTo(targetId, anchor.getBoundingClientRect(), true, extractAccent(anchor));
          });
        } else if (href.startsWith('http')) {
          anchor.setAttribute('target', '_blank');
          anchor.setAttribute('rel', 'noopener');
        }
      });

      enhanceSvgFlow(svgEl, diagramSpec.id);
    }

    const refreshPan = setupDragPan(viewport);

    // Controlli zoom locali al solo diagramma (il testo della pagina non si rimpicciolisce mai!)
    let zoomPct = null; // null = adatta
    const pctEl = card.querySelector('.zoom-pct');
    const applyZoom = () => {
      if (!svgEl) return;
      if (zoomPct === null) {
        svgEl.style.width = '100%';
        svgEl.style.maxWidth = `${Math.min(naturalWidth, 1160)}px`;
        pctEl.textContent = 'Adatta';
      } else {
        const px = Math.round((naturalWidth * zoomPct) / 100);
        svgEl.style.maxWidth = 'none';
        svgEl.style.width = `${px}px`;
        pctEl.textContent = `${zoomPct}%`;
      }
      requestAnimationFrame(() => refreshPan?.());
    };

    const flowBtn = card.querySelector('[data-z="flow"]');
    if (flowBtn) {
      flowBtn.addEventListener('click', () => {
        flowEnabled = !flowEnabled;
        syncFlowButtons();
      });
    }

    card.querySelector('[data-z="in"]').addEventListener('click', () => {
      zoomPct = zoomPct === null ? 100 : Math.min(200, zoomPct + 20);
      applyZoom();
    });
    card.querySelector('[data-z="out"]').addEventListener('click', () => {
      zoomPct = zoomPct === null ? 70 : Math.max(40, zoomPct - 20);
      applyZoom();
    });
    card.querySelector('[data-z="fit"]').addEventListener('click', () => {
      zoomPct = null;
      applyZoom();
    });
    card.querySelector('[data-z="full"]').addEventListener('click', () => {
      openLightbox(diagramSpec.caption, svgMarkup, naturalWidth, diagramSpec.id);
    });

    viewport.addEventListener(
      'wheel',
      (ev) => {
        if (!ev.ctrlKey) return;
        ev.preventDefault();
        if (ev.deltaY < 0) {
          zoomPct = zoomPct === null ? 100 : Math.min(200, zoomPct + 15);
        } else {
          zoomPct = zoomPct === null ? 75 : Math.max(40, zoomPct - 15);
        }
        applyZoom();
      },
      { passive: false }
    );

    container.appendChild(card);
    requestAnimationFrame(() => refreshPan?.());
  }

  // --- Lightbox a schermo intero ---
  const refreshLbPan = setupDragPan(lbBody);

  function openLightbox(title, svgMarkup, naturalWidth, diagramId = '') {
    lbTitle.textContent = title;
    lbBody.innerHTML = svgMarkup;
    lbBaseWidth = naturalWidth || 1200;
    lbZoom = null;

    const svgEl = lbBody.querySelector(':scope > svg');
    if (svgEl) {
      svgEl.removeAttribute('width');
      svgEl.removeAttribute('height');
      svgEl.style.width = '100%';
      svgEl.style.maxWidth = `${Math.min(lbBaseWidth, window.innerWidth - 72)}px`;
      svgEl.querySelectorAll('a').forEach((anchor) => {
        const href = anchor.getAttribute('href') || anchor.getAttribute('xlink:href') || '';
        if (href.startsWith('#')) {
          const targetId = href.slice(1);
          anchor.addEventListener('click', (ev) => {
            ev.preventDefault();
            closeLightbox();
            navigateTo(targetId, null, true, extractAccent(anchor));
          });
        } else if (href.startsWith('http')) {
          anchor.setAttribute('target', '_blank');
          anchor.setAttribute('rel', 'noopener');
        }
      });
      enhanceSvgFlow(svgEl, diagramId);
    }
    lbPct.textContent = 'Adatta';
    lightbox.hidden = false;
    requestAnimationFrame(() => refreshLbPan?.());
  }

  function applyLightboxZoom() {
    const svgEl = lbBody.querySelector(':scope > svg');
    if (!svgEl) return;
    if (lbZoom === null) {
      svgEl.style.width = '100%';
      svgEl.style.maxWidth = `${Math.min(lbBaseWidth, window.innerWidth - 72)}px`;
      lbPct.textContent = 'Adatta';
    } else {
      svgEl.style.maxWidth = 'none';
      svgEl.style.width = `${Math.round((lbBaseWidth * lbZoom) / 100)}px`;
      lbPct.textContent = `${lbZoom}%`;
    }
    requestAnimationFrame(() => refreshLbPan?.());
  }

  lbBody.addEventListener(
    'wheel',
    (ev) => {
      if (!ev.ctrlKey) return;
      ev.preventDefault();
      if (ev.deltaY < 0) {
        lbZoom = lbZoom === null ? 100 : Math.min(220, lbZoom + 15);
      } else {
        lbZoom = lbZoom === null ? 75 : Math.max(40, lbZoom - 15);
      }
      applyLightboxZoom();
    },
    { passive: false }
  );

  function closeLightbox() {
    lightbox.hidden = true;
    lbBody.innerHTML = '';
  }

  document.getElementById('lb-in').addEventListener('click', () => {
    lbZoom = lbZoom === null ? 100 : Math.min(220, lbZoom + 20);
    applyLightboxZoom();
  });
  document.getElementById('lb-out').addEventListener('click', () => {
    lbZoom = lbZoom === null ? 75 : Math.max(40, lbZoom - 20);
    applyLightboxZoom();
  });
  document.getElementById('lb-fit').addEventListener('click', () => {
    lbZoom = null;
    applyLightboxZoom();
  });
  document.getElementById('lb-close').addEventListener('click', closeLightbox);

  // --- Timeline verticale Storico GitHub ---
  function renderTimeline(view) {
    const wrap = document.createElement('section');
    wrap.className = 'section';

    const items = [...view.timeline];
    const filtered = items
      .filter((it) => {
        if (timelineFilter === 'tutte') return true;
        if (timelineFilter === 'review') return Boolean(it.hasReview);
        return it.category === timelineFilter;
      })
      .sort((a, b) => (timelineNewestFirst ? b.order - a.order : a.order - b.order));

    const counts = {
      tutte: items.length,
      unita: items.filter((i) => i.category === 'unita').length,
      aperta: items.filter((i) => i.category === 'aperta').length,
      chiusa: items.filter((i) => i.category === 'chiusa').length,
      review: items.filter((i) => i.hasReview).length
    };

    const filters = [
      ['tutte', `Tutte (${counts.tutte})`],
      ['unita', `Unite su main (${counts.unita})`],
      ['aperta', `Aperte (${counts.aperta})`],
      ['chiusa', `Chiuse (${counts.chiusa})`],
      ['review', `Con approvazioni (${counts.review})`]
    ];

    wrap.innerHTML = `
      <div class="timeline-controls">
        <div class="filter-pills">
          ${filters
            .map(
              ([k, lbl]) =>
                `<button type="button" class="filter-pill ${timelineFilter === k ? 'active' : ''}" data-f="${k}">${lbl}</button>`
            )
            .join('')}
        </div>
        <button type="button" class="filter-pill" id="btn-sort">
          Ordine: ${timelineNewestFirst ? 'Più recenti prima ↓' : 'Cronologico ↑'}
        </button>
      </div>
      <div class="timeline">
        ${filtered
          .map(
            (it) => `
          <article class="tl-item">
            <span class="tl-dot ${it.status}" aria-hidden="true"></span>
            <div class="tl-card">
              <div class="tl-top">
                <span class="tl-date">${it.date}</span>
                <span class="tl-pr">${it.pr}</span>
                <span class="badge ${it.status}">${it.statusLabel}</span>
                <span class="tl-author">di ${it.author}</span>
              </div>
              <h3 class="tl-title">${it.title}</h3>
              <p class="tl-desc">${it.desc}</p>
              ${
                Array.isArray(it.files) && it.files.length
                  ? `<details class="tl-details">
                      <summary>File toccati (${it.files.length})</summary>
                      <ul class="tl-files">
                        ${it.files.map((f) => `<li><code>${escapeHtml(f)}</code></li>`).join('')}
                      </ul>
                    </details>`
                  : ''
              }
              ${
                Array.isArray(it.commits) && it.commits.length
                  ? `<details class="tl-details">
                      <summary>Commit (${it.commits.length})</summary>
                      <ul class="tl-commits">
                        ${it.commits
                          .map(
                            (c) =>
                              `<li><a class="tl-commit-hash" href="https://github.com/lufo-336/under-the-sun/commit/${encodeURIComponent(c.hash)}" target="_blank" rel="noopener"><code>${escapeHtml(c.hash)}</code></a> · <span class="tl-commit-date">${escapeHtml(c.date)}</span> · <span class="tl-commit-who">${escapeHtml(c.who)}</span> · ${escapeHtml(c.what)}</li>`
                          )
                          .join('')}
                      </ul>
                    </details>`
                  : ''
              }
              ${it.review ? `<div class="tl-review-box">${it.review}</div>` : ''}
              <div class="tl-links">
                ${it.links
                  .map(
                    (l) =>
                      `<a class="btn-link ${l.secondary ? 'secondary' : ''}" href="${l.href}" target="_blank" rel="noopener">${l.label}</a>`
                  )
                  .join('')}
              </div>
            </div>
          </article>
        `
          )
          .join('')}
      </div>
    `;

    wrap.querySelectorAll('[data-f]').forEach((btn) => {
      btn.addEventListener('click', () => {
        timelineFilter = btn.dataset.f;
        renderStage();
      });
    });

    wrap.querySelector('#btn-sort').addEventListener('click', () => {
      timelineNewestFirst = !timelineNewestFirst;
      renderStage();
    });

    return wrap;
  }

  // --- Rendering principale della vista corrente ---
  function renderStage(animClass = '') {
    const view = DATA.views[currentView];
    stage.className = `stage ${animClass}`.trim();
    stage.innerHTML = '';

    // Intestazione pagina
    const head = document.createElement('section');
    head.className = 'page-head';

    if (currentView !== 'generale') {
      const backRow = document.createElement('div');
      backRow.className = 'back-row';
      backRow.innerHTML = `<button type="button" class="btn-back" id="btn-back-main">← Vista generale</button><div class="action-links"></div>`;
      backRow.querySelector('#btn-back-main').addEventListener('click', () => navigateTo('generale'));

      const linksBox = backRow.querySelector('.action-links');
      (view.links || []).forEach((lnk) => {
        if (lnk.internal) {
          const b = document.createElement('button');
          b.type = 'button';
          b.className = `btn-link ${lnk.secondary ? 'secondary' : ''}`;
          b.textContent = lnk.label;
          b.addEventListener('click', () => navigateTo(lnk.internal, b.getBoundingClientRect()));
          linksBox.appendChild(b);
        } else {
          const a = document.createElement('a');
          a.className = `btn-link ${lnk.secondary ? 'secondary' : ''}`;
          a.href = lnk.href;
          a.target = '_blank';
          a.rel = 'noopener';
          a.textContent = lnk.label;
          linksBox.appendChild(a);
        }
      });
      head.appendChild(backRow);
    }

    const h1 = document.createElement('h1');
    h1.textContent = view.title;
    head.appendChild(h1);

    const sub = document.createElement('p');
    sub.className = 'subtitle';
    sub.innerHTML = view.subtitle;
    head.appendChild(sub);

    if (view.badges && view.badges.length) {
      const strip = document.createElement('div');
      strip.className = 'meta-strip';
      strip.innerHTML = view.badges
        .map((b) => `<span class="badge ${b.cls}"><span class="dot"></span>${b.text}</span>`)
        .join('');
      head.appendChild(strip);
    }

    stage.appendChild(head);

    // Timeline verticale (per Storico GitHub)
    if (view.isTimeline) {
      stage.appendChild(renderTimeline(view));
      return;
    }

    // Diagrammi D2
    (view.diagrams || []).forEach((diag) => {
      const sec = document.createElement('section');
      sec.className = 'section';
      mountDiagram(sec, diag);
      stage.appendChild(sec);
    });

    // Calendario (solo vista generale)
    if (view.showCalendar) {
      const calSec = document.createElement('section');
      calSec.className = 'section';
      calSec.innerHTML = `
        <div class="section-head">
          <h2 class="section-title">Dove siamo nel calendario</h2>
          <span class="section-hint">Ogni SAL: organizzazione · chi ha fatto cosa · prossimi passi · scelte sull'architettura</span>
        </div>
        <div class="cal-grid"></div>
      `;
      const grid = calSec.querySelector('.cal-grid');
      DATA.calendario.forEach((c) => {
        const el = document.createElement('div');
        el.className = `cal-item ${c.stato} ${c.link ? 'clickable' : ''}`;
        el.innerHTML = `<span class="cal-date">${c.date}</span><span class="cal-title">${c.title}</span><span class="cal-desc">${c.desc}</span>`;
        if (c.link) {
          el.addEventListener('click', () => navigateTo(c.link, el.getBoundingClientRect()));
        }
        grid.appendChild(el);
      });
      stage.appendChild(calSec);
    }

    // Già fatto in quest'area
    if (view.fatto && Array.isArray(view.fatto.items) && view.fatto.items.length) {
      const fSec = document.createElement('section');
      fSec.className = 'section';
      fSec.innerHTML = `
        <div class="section-head">
          <h2 class="section-title">${view.fatto.title || 'Già fatto in quest\'area'}</h2>
        </div>
        <ul class="fatto-list">
          ${view.fatto.items
            .map(
              (it) => `
            <li class="fatto-row">
              <span class="fatto-dot ${it.stato || 'fatto'}" aria-hidden="true"></span>
              <span class="fatto-date">${it.date}</span>
              <span class="fatto-who">${it.who}</span>
              <span class="fatto-what">${it.what}</span>
              ${
                it.ref && it.href
                  ? `<a class="fatto-ref" href="${it.href}" target="_blank" rel="noopener">${it.ref} ↗</a>`
                  : it.ref
                    ? `<span class="fatto-ref muted">${it.ref}</span>`
                    : ''
              }
            </li>
          `
            )
            .join('')}
        </ul>
      `;
      stage.appendChild(fSec);
    }

    // Tabella (endpoint / configurazioni / CI jobs)
    if (view.table) {
      const tSec = document.createElement('section');
      tSec.className = 'section';
      tSec.innerHTML = `
        <div class="section-head"><h2 class="section-title">${view.table.title}</h2></div>
        <div class="table-wrap">
          <table>
            <thead><tr>${view.table.headers.map((h) => `<th>${h}</th>`).join('')}</tr></thead>
            <tbody>${view.table.rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join('')}</tr>`).join('')}</tbody>
          </table>
        </div>
      `;
      stage.appendChild(tSec);
    }

    // Scelte architetturali
    if (view.choices && view.choices.length) {
      const cSec = document.createElement('section');
      cSec.className = 'section';
      cSec.innerHTML = `
        <div class="section-head">
          <h2 class="section-title">${view.choicesTitle || 'Scelte architetturali e perché'}</h2>
        </div>
        <div class="cards-grid">
          ${view.choices
            .map(
              (c) => `
            <article class="card">
              <h3>${c.title}</h3>
              <p>${c.body}</p>
              ${c.why ? `<p><strong>Perché:</strong> ${c.why}</p>` : ''}
            </article>
          `
            )
            .join('')}
        </div>
      `;
      stage.appendChild(cSec);
    }

    // Codice reale
    if (view.codeBlocks && view.codeBlocks.length) {
      const kSec = document.createElement('section');
      kSec.className = 'section';
      kSec.innerHTML = `
        <div class="section-head">
          <h2 class="section-title">Sguardo al codice reale</h2>
          <span class="section-hint">Estratti verificati dal repository</span>
        </div>
        <div class="code-list"></div>
      `;
      const list = kSec.querySelector('.code-list');
      view.codeBlocks.forEach((blk) => {
        const card = document.createElement('div');
        card.className = 'code-card';
        card.innerHTML = `
          <div class="code-head">
            <span class="code-file">${blk.file}</span>
            <span class="code-actions">
              <span class="lang-pill">${blk.lang}</span>
              <button type="button" class="btn-copy">Copia</button>
            </span>
          </div>
          <div class="code-body">
            <pre><code>${highlightCode(blk.code, blk.lang)}</code></pre>
            <div class="code-note"><p>${blk.note}</p></div>
          </div>
        `;
        const copyBtn = card.querySelector('.btn-copy');
        copyBtn.addEventListener('click', () => {
          navigator.clipboard?.writeText(blk.code).then(() => {
            copyBtn.textContent = 'Copiato ✓';
            setTimeout(() => (copyBtn.textContent = 'Copia'), 1400);
          });
        });
        list.appendChild(card);
      });
      stage.appendChild(kSec);
    }
  }

  // --- Eventi globali ---
  btnHome.addEventListener('click', () => navigateTo('generale'));

  window.addEventListener('keydown', (ev) => {
    if (ev.key === 'Escape') {
      if (!lightbox.hidden) {
        closeLightbox();
      } else if (currentView !== 'generale') {
        navigateTo('generale');
      }
    }
  });

  window.addEventListener('popstate', () => {
    const id = (window.location.hash || '#generale').slice(1);
    if (DATA.views[id] && id !== currentView) {
      navigateTo(id, null, false);
    }
  });

  // Avvio
  const initialId = (window.location.hash || '#generale').slice(1);
  currentView = DATA.views[initialId] ? initialId : 'generale';
  renderTopnav();
  renderStage();
})();
