/* ==========================================================================
   AutomataX — Modern Linear / Vercel Studio Research Workstation (app.js)
   Clean Obsidian Minimalist Interactive Frontend Logic
   ========================================================================== */

let currentLanguages = [];
let currentPresets = [];
let currentDataset = [];
let currentLearnedDFA = null;
let currentAlgorithm = "edsm";
let currentSteps = [];
let currentReplayIndex = 0;
let isReplayPlaying = false;
let replayTimer = null;
let currentMode = "canvas";

// Cytoscape instances
let cyLearned = null;
let cyReference = null;

// Chart.js instances
let chartLearningCurve = null;
let chartNoiseStudy = null;
let chartActiveStudy = null;

// Evidence filtering
let currentEvidenceFilter = "all";
let currentEvidenceSearch = "";

// ---------------------------------------------------------------------------
// Cytoscape Visual Theme (Refined Modern Studio)
// ---------------------------------------------------------------------------

const CY_STUDIO_STYLE = [
  {
    selector: 'node',
    style: {
      'content': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#111827',
      'color': '#f8fafc',
      'font-size': '12px',
      'font-family': 'JetBrains Mono, monospace',
      'font-weight': '600',
      'width': 42,
      'height': 42,
      'border-width': 2,
      'border-color': '#334155',
      'border-style': 'solid',
      'transition-property': 'background-color, border-color, width, height, border-width',
      'transition-duration': '0.15s',
    }
  },
  {
    selector: 'node.start',
    style: {
      'border-color': '#38bdf8',
      'border-width': 2.5,
      'background-color': '#0c2842',
      'color': '#ffffff',
    }
  },
  {
    selector: 'node.accept',
    style: {
      'border-color': '#10b981',
      'border-width': 6,
      'border-style': 'double', // Formal theoretical DFA double ring
      'background-color': '#064e3b',
      'color': '#a7f3d0',
    }
  },
  {
    selector: 'node.start.accept',
    style: {
      'border-color': '#10b981',
      'border-width': 6,
      'border-style': 'double',
      'background-color': '#073642',
      'color': '#ffffff',
    }
  },
  {
    selector: 'node.highlighted',
    style: {
      'background-color': '#38bdf8',
      'border-color': '#ffffff',
      'border-width': 4,
      'color': '#030712',
      'width': 50,
      'height': 50,
    }
  },
  {
    selector: 'node.selected-inspect',
    style: {
      'border-color': '#f59e0b',
      'border-width': 3.5,
    }
  },
  {
    selector: 'edge',
    style: {
      'content': 'data(label)',
      'font-size': '11px',
      'font-family': 'JetBrains Mono, monospace',
      'font-weight': '600',
      'color': '#94a3b8',
      'text-background-color': '#090d16',
      'text-background-opacity': 0.9,
      'text-background-padding': '3px',
      'text-border-width': 1,
      'text-border-color': '#1e293b',
      'text-border-style': 'solid',
      'curve-style': 'bezier',
      'control-point-step-size': 40,
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#475569',
      'line-color': '#334155',
      'width': 1.8,
      'arrow-scale': 1.1,
      'transition-property': 'line-color, target-arrow-color, width, color',
      'transition-duration': '0.15s',
    }
  },
  {
    selector: 'edge.highlighted',
    style: {
      'line-color': '#38bdf8',
      'target-arrow-color': '#38bdf8',
      'width': 3.5,
      'color': '#38bdf8',
      'text-border-color': '#38bdf8',
    }
  }
];

function initCy(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return null;
  const cy = cytoscape({
    container: container,
    elements: [],
    style: CY_STUDIO_STYLE,
    layout: { name: 'circle' },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
    wheelSensitivity: 0.25,
  });

  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    cy.elements().removeClass('selected-inspect');
    node.addClass('selected-inspect');
    showStateInspector(node);
  });

  return cy;
}

function renderElements(cy, elements, layoutName = 'cose') {
  if (!cy) return;
  cy.elements().remove();
  cy.add(elements);
  applyGraphLayout(cy, layoutName);
  setTimeout(() => {
    cy.resize();
    cy.fit(40);
  }, 100);
}

function applyGraphLayout(cy, layoutName) {
  if (!cy) return;
  let layoutConfig = { name: layoutName, fit: true, padding: 40 };

  if (layoutName === 'cose') {
    layoutConfig = {
      name: 'cose',
      animate: false,
      fit: true,
      padding: 40,
      nodeRepulsion: 7500,
      idealEdgeLength: 70,
      edgeElasticity: 100,
      gravity: 0.25,
      numIter: 1000,
    };
  } else if (layoutName === 'concentric') {
    layoutConfig = {
      name: 'concentric',
      fit: true,
      padding: 40,
      concentric: function(node) {
        return node.data('is_start') ? 10 : (node.data('is_accept') ? 5 : 1);
      },
      levelWidth: () => 1,
    };
  } else if (layoutName === 'breadthfirst') {
    layoutConfig = {
      name: 'breadthfirst',
      fit: true,
      padding: 40,
      directed: true,
      roots: cy.nodes('[?is_start]'),
    };
  }

  const layout = cy.layout(layoutConfig);
  layout.run();
}

function showStateInspector(node) {
  document.getElementById('inspector-node-empty').classList.add('hidden');
  const card = document.getElementById('inspector-node-card');
  card.classList.remove('hidden');

  const id = node.data('id');
  const isStart = node.data('is_start');
  const isAccept = node.data('is_accept');

  document.getElementById('inspect-state-id').textContent = id;
  const typeBadge = document.getElementById('inspect-state-type');
  if (isStart && isAccept) {
    typeBadge.textContent = 'Start & Accept';
    typeBadge.style.color = 'var(--accent-emerald)';
  } else if (isAccept) {
    typeBadge.textContent = 'Accepting';
    typeBadge.style.color = 'var(--accent-emerald)';
  } else if (isStart) {
    typeBadge.textContent = 'Start';
    typeBadge.style.color = 'var(--accent-cyan)';
  } else {
    typeBadge.textContent = 'Normal';
    typeBadge.style.color = 'var(--text-dim)';
  }

  const outEdges = node.outgoers('edge');
  const list = document.getElementById('inspect-transitions-list');
  list.innerHTML = '';
  if (outEdges.length === 0) {
    list.innerHTML = '<span style="color: var(--text-muted); font-size: 11px; font-style: italic;">No outgoing transitions.</span>';
  } else {
    outEdges.forEach(e => {
      const row = document.createElement('div');
      row.style.display = 'flex';
      row.style.justifyContent = 'space-between';
      row.style.fontSize = '11px';
      row.style.padding = '3px 6px';
      row.style.background = 'rgba(255,255,255,0.03)';
      row.style.borderRadius = '4px';
      row.innerHTML = `
        <span style="color: var(--text-dim)">on <strong style="color: var(--accent-cyan);">'${e.data('label')}'</strong></span>
        <span style="color: #fff; font-weight: 600;">➜ ${e.data('target')}</span>
      `;
      list.appendChild(row);
    });
  }
}

// ---------------------------------------------------------------------------
// App Bootstrapping
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
  cyLearned = initCy('cy-container');
  cyReference = initCy('cy-reference-container');

  setupWorkstationLayout();
  setupEventListeners();

  window.addEventListener('resize', () => {
    if (cyLearned) cyLearned.resize().fit(40);
    if (cyReference) cyReference.resize().fit(40);
  });

  await loadCatalogAndPresets();
  await generateData();
  await runInference();
});

// ---------------------------------------------------------------------------
// Workstation Layout & Mode Switching
// ---------------------------------------------------------------------------

function setupWorkstationLayout() {
  const btnLeft = document.getElementById('btn-toggle-left-panel');
  const leftPanel = document.getElementById('left-panel');
  btnLeft.addEventListener('click', () => {
    leftPanel.classList.toggle('collapsed');
    setTimeout(() => { if (cyLearned) cyLearned.resize().fit(40); }, 220);
  });

  const btnRight = document.getElementById('btn-toggle-right-panel');
  const rightPanel = document.getElementById('right-panel');
  btnRight.addEventListener('click', () => {
    rightPanel.classList.toggle('collapsed');
    setTimeout(() => { if (cyLearned) cyLearned.resize().fit(40); }, 220);
  });

  const modeTabs = document.querySelectorAll('.mode-tab');
  const simDock = document.getElementById('sim-floating-dock');
  const replayDock = document.getElementById('replay-floating-dock');
  const diffOverlay = document.getElementById('view-diff-overlay');
  const analyticsOverlay = document.getElementById('view-analytics-overlay');

  modeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      modeTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentMode = tab.getAttribute('data-mode');

      simDock.classList.add('hidden');
      replayDock.classList.add('hidden');
      diffOverlay.classList.add('hidden');
      analyticsOverlay.classList.add('hidden');

      if (currentMode === 'canvas') {
        if (cyLearned) cyLearned.resize().fit(40);
      } else if (currentMode === 'simulate') {
        simDock.classList.remove('hidden');
        if (cyLearned) cyLearned.resize().fit(40);
      } else if (currentMode === 'replay') {
        replayDock.classList.remove('hidden');
        if (cyLearned) cyLearned.resize().fit(40);
      } else if (currentMode === 'compare') {
        diffOverlay.classList.remove('hidden');
        setTimeout(() => { if (cyReference) cyReference.resize().fit(40); }, 80);
      } else if (currentMode === 'analytics') {
        analyticsOverlay.classList.remove('hidden');
      }
    });
  });

  document.getElementById('btn-close-diff-view').addEventListener('click', () => {
    document.querySelector('.mode-tab[data-mode="canvas"]').click();
  });
  document.getElementById('btn-close-analytics-view').addEventListener('click', () => {
    document.querySelector('.mode-tab[data-mode="canvas"]').click();
  });
}

// ---------------------------------------------------------------------------
// Catalog & Presets Loading
// ---------------------------------------------------------------------------

async function loadCatalogAndPresets() {
  try {
    const [langRes, presetRes] = await Promise.all([
      fetch('/api/languages').then(r => r.json()),
      fetch('/api/presets').then(r => r.json()),
    ]);

    currentLanguages = langRes.languages || [];
    currentPresets = presetRes.presets || [];

    const langSelect = document.getElementById('select-target-lang');
    if (currentLanguages.length > 0) {
      langSelect.innerHTML = '';
      currentLanguages.forEach(l => {
        const opt = document.createElement('option');
        opt.value = l.id;
        opt.textContent = `${l.name} (${l.expected_min_dfa_states} states)`;
        langSelect.appendChild(opt);
      });
    }

    renderDossierCards();
    updateLanguageMeta();
  } catch (err) {
    console.error("Failed to load catalog/presets:", err);
  }
}

function updateLanguageMeta() {
  const langSelect = document.getElementById('select-target-lang');
  const selectedId = langSelect ? langSelect.value : 'ends_with_ab';
  const lang = currentLanguages.find(l => l.id === selectedId);
  if (!lang) return;

  document.getElementById('target-desc').textContent = lang.description;
  document.getElementById('target-alphabet-badge').textContent = `Σ = {${lang.alphabet.join(', ')}}`;
  document.getElementById('inspect-alphabet').textContent = `{${lang.alphabet.join(', ')}}`;
}

function renderDossierCards() {
  const container = document.getElementById('dossier-cards-grid');
  if (!container) return;
  container.innerHTML = '';

  currentPresets.forEach((p, idx) => {
    const card = document.createElement('div');
    card.className = 'studio-card';

    card.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span class="pill-tag" style="background: rgba(255,255,255,0.08);">${p.case_code || `CASE-${idx+1}`}</span>
        <span style="font-size: 10px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">${p.difficulty || 'Normal'}</span>
      </div>
      <h4 style="font-size: 12.5px; font-weight: 600; color: #fff; margin-top: 4px;">${p.title}</h4>
      <p style="font-size: 11px; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace;">${p.subtitle}</p>
      <p style="font-size: 11px; color: var(--text-dim); line-height: 1.35; margin-top: 4px;">${p.description}</p>
      <div style="padding-top: 8px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
        <span style="font-size: 10.5px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">Algo: <strong style="color: #fff;">${p.algorithm.toUpperCase()}</strong></span>
        <button class="btn-deploy-case btn-studio primary" style="padding: 2px 8px; font-size: 11px;" data-preset-id="${p.id}">
          Load Case
        </button>
      </div>
    `;

    card.querySelector('.btn-deploy-case').addEventListener('click', () => {
      deployCaseFile(p);
    });

    container.appendChild(card);
  });
}

async function deployCaseFile(preset) {
  closeDossierModal();

  if (preset.language) {
    document.getElementById('select-target-lang').value = preset.language;
    updateLanguageMeta();
  }
  if (preset.algorithm) {
    const btn = document.querySelector(`.algo-btn[data-algo="${preset.algorithm}"]`);
    if (btn) btn.click();
  }

  if (preset.examples) {
    renderTrainingExamples(preset.examples);
  } else {
    if (preset.sampling_mode) {
      document.getElementById('select-sampling-mode').value = preset.sampling_mode;
    }
    if (preset.noise_rate !== undefined) {
      document.getElementById('input-noise-rate').value = Math.round(preset.noise_rate * 100);
      document.getElementById('val-noise-rate').textContent = `${Math.round(preset.noise_rate * 100)}%`;
    }
    await generateData();
  }

  await runInference();
}

function openDossierModal() {
  document.getElementById('modal-dossier-vault').classList.remove('hidden');
}

function closeDossierModal() {
  document.getElementById('modal-dossier-vault').classList.add('hidden');
}

// ---------------------------------------------------------------------------
// Event Listeners Setup
// ---------------------------------------------------------------------------

function setupEventListeners() {
  const sampleCount = document.getElementById('input-sample-count');
  sampleCount.addEventListener('input', () => {
    document.getElementById('val-sample-count').textContent = sampleCount.value;
  });

  const maxLength = document.getElementById('input-max-length');
  maxLength.addEventListener('input', () => {
    document.getElementById('val-max-length').textContent = maxLength.value;
  });

  const noiseRate = document.getElementById('input-noise-rate');
  noiseRate.addEventListener('input', () => {
    document.getElementById('val-noise-rate').textContent = `${noiseRate.value}%`;
  });

  document.getElementById('select-target-lang').addEventListener('change', () => {
    updateLanguageMeta();
    generateData();
  });

  document.getElementById('btn-generate-data').addEventListener('click', () => {
    generateData();
  });

  document.querySelectorAll('.algo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.algo-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentAlgorithm = btn.getAttribute('data-algo');

      const explainer = document.getElementById('algo-explainer');
      if (currentAlgorithm === 'edsm') {
        explainer.textContent = "EDSM: Evaluates all candidate merges by global evidence endorsement gain.";
      } else if (currentAlgorithm === 'rpni') {
        explainer.textContent = "RPNI: Merges candidate states in canonical shortlex order with the earliest compatible red state.";
      } else {
        explainer.textContent = "Angluin's L*: Active learner maintaining observation table closedness and consistency via queries.";
      }
    });
  });

  document.getElementById('btn-quick-run').addEventListener('click', () => {
    runInference();
  });

  document.getElementById('btn-open-dossier').addEventListener('click', openDossierModal);
  document.getElementById('btn-close-dossier').addEventListener('click', closeDossierModal);
  document.getElementById('modal-dossier-vault').addEventListener('click', (e) => {
    if (e.target.id === 'modal-dossier-vault') closeDossierModal();
  });

  document.getElementById('select-graph-layout').addEventListener('change', (e) => {
    if (cyLearned) applyGraphLayout(cyLearned, e.target.value);
  });
  document.getElementById('btn-fit-graph').addEventListener('click', () => {
    if (cyLearned) cyLearned.fit(40);
  });
  document.getElementById('btn-zoom-in').addEventListener('click', () => {
    if (cyLearned) cyLearned.zoom(cyLearned.zoom() * 1.25);
  });
  document.getElementById('btn-zoom-out').addEventListener('click', () => {
    if (cyLearned) cyLearned.zoom(cyLearned.zoom() * 0.8);
  });
  document.getElementById('btn-export-png').addEventListener('click', exportGraphPng);
  document.getElementById('btn-export-json').addEventListener('click', exportGraphJson);

  document.getElementById('input-search-evidence').addEventListener('input', (e) => {
    currentEvidenceSearch = e.target.value.toLowerCase();
    filterAndRenderEvidence();
  });

  document.querySelectorAll('.evidence-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.evidence-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentEvidenceFilter = btn.getAttribute('data-filter');
      filterAndRenderEvidence();
    });
  });

  setupPlantClueModal();

  document.getElementById('btn-play-simulate').addEventListener('click', () => {
    animateStringPath();
  });
  document.getElementById('btn-step-simulate').addEventListener('click', () => {
    stepStringPath();
  });
  document.getElementById('btn-reset-simulate').addEventListener('click', () => {
    resetSimulation();
  });

  document.querySelectorAll('.btn-quick-string').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('input-test-string').value = btn.getAttribute('data-str');
      resetSimulation();
      animateStringPath();
    });
  });

  const scrubber = document.getElementById('replay-scrubber');
  scrubber.addEventListener('input', (e) => {
    currentReplayIndex = parseInt(e.target.value, 10);
    renderReplayStep(currentReplayIndex);
  });
  document.getElementById('btn-replay-prev').addEventListener('click', () => {
    if (currentReplayIndex > 0) {
      currentReplayIndex--;
      scrubber.value = currentReplayIndex;
      renderReplayStep(currentReplayIndex);
    }
  });
  document.getElementById('btn-replay-next').addEventListener('click', () => {
    if (currentReplayIndex < currentSteps.length - 1) {
      currentReplayIndex++;
      scrubber.value = currentReplayIndex;
      renderReplayStep(currentReplayIndex);
    }
  });
  document.getElementById('btn-replay-play').addEventListener('click', toggleReplayPlayback);

  document.getElementById('btn-recompare').addEventListener('click', runComparison);
  document.getElementById('btn-run-learning-curve').addEventListener('click', runLearningCurveExperiment);
  document.getElementById('btn-run-noise-study').addEventListener('click', runNoiseStudyExperiment);
  document.getElementById('btn-run-active-study').addEventListener('click', runActiveStudyExperiment);
}

// ---------------------------------------------------------------------------
// Add Custom String Setup
// ---------------------------------------------------------------------------

let newClueLabel = true;

function setupPlantClueModal() {
  const modal = document.getElementById('modal-plant-clue');
  document.getElementById('btn-plant-clue').addEventListener('click', () => {
    modal.classList.remove('hidden');
    document.getElementById('input-new-clue-string').focus();
  });

  document.getElementById('btn-close-plant-clue').addEventListener('click', () => {
    modal.classList.add('hidden');
  });
  modal.addEventListener('click', (e) => {
    if (e.target.id === 'modal-plant-clue') modal.classList.add('hidden');
  });

  const posBtn = document.getElementById('btn-label-pos');
  const negBtn = document.getElementById('btn-label-neg');

  posBtn.addEventListener('click', () => {
    newClueLabel = true;
    posBtn.style.borderColor = 'rgba(16, 185, 129, 0.4)';
    posBtn.style.background = 'rgba(16, 185, 129, 0.1)';
    posBtn.style.color = 'var(--accent-emerald)';
    negBtn.style.borderColor = 'var(--border-subtle)';
    negBtn.style.background = 'rgba(255,255,255,0.04)';
    negBtn.style.color = 'var(--text-muted)';
  });

  negBtn.addEventListener('click', () => {
    newClueLabel = false;
    negBtn.style.borderColor = 'rgba(244, 63, 94, 0.4)';
    negBtn.style.background = 'rgba(244, 63, 94, 0.1)';
    negBtn.style.color = 'var(--accent-rose)';
    posBtn.style.borderColor = 'var(--border-subtle)';
    posBtn.style.background = 'rgba(255,255,255,0.04)';
    posBtn.style.color = 'var(--text-muted)';
  });

  document.getElementById('btn-submit-clue').addEventListener('click', () => {
    const rawStr = document.getElementById('input-new-clue-string').value.trim();
    currentDataset.unshift({ string: rawStr, label: newClueLabel });
    modal.classList.add('hidden');
    document.getElementById('input-new-clue-string').value = '';
    filterAndRenderEvidence();
    runInference();
  });
}

// ---------------------------------------------------------------------------
// Dataset Generation & Evidence Rendering
// ---------------------------------------------------------------------------

async function generateData() {
  const targetSelect = document.getElementById('select-target-lang');
  const target = targetSelect ? targetSelect.value || 'ends_with_ab' : 'ends_with_ab';
  const size = parseInt(document.getElementById('input-sample-count').value, 10);
  const maxLength = parseInt(document.getElementById('input-max-length').value, 10);
  const noiseRate = parseFloat(document.getElementById('input-noise-rate').value) / 100.0;
  const samplingMode = document.getElementById('select-sampling-mode').value;

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: 'language',
        target: target,
        size: size,
        min_length: 0,
        max_length: maxLength,
        positive_ratio: 0.5,
        noise_rate: noiseRate,
        sampling_mode: samplingMode,
        seed: 42,
      }),
    });
    const data = await res.json();
    currentDataset = data.examples || [];
    filterAndRenderEvidence();
  } catch (err) {
    console.error("Failed to generate data:", err);
  }
}

function filterAndRenderEvidence() {
  let filtered = currentDataset;

  if (currentEvidenceFilter === 'pos') {
    filtered = filtered.filter(ex => ex.label);
  } else if (currentEvidenceFilter === 'neg') {
    filtered = filtered.filter(ex => !ex.label);
  }

  if (currentEvidenceSearch) {
    filtered = filtered.filter(ex => ex.string.toLowerCase().includes(currentEvidenceSearch));
  }

  const list = document.getElementById('training-examples-list');
  list.innerHTML = '';

  document.getElementById('train-count').textContent = currentDataset.length;

  if (filtered.length === 0) {
    list.innerHTML = '<div style="color: var(--text-muted); font-style: italic; text-align: center; padding: 12px; font-size: 11px;">No matching strings found.</div>';
    return;
  }

  filtered.forEach((ex) => {
    const row = document.createElement('div');
    row.className = `evidence-row ${ex.label ? 'pos' : 'neg'}`;
    const strDisplay = ex.string === '' ? 'ε (empty)' : ex.string;

    row.innerHTML = `
      <div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-weight: 600; color: ${ex.label ? '#f8fafc' : '#cbd5e1'}; font-family: 'JetBrains Mono', monospace;">${strDisplay}</span>
        <span style="font-size: 10px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;">|${ex.string.length}|</span>
      </div>
      <div style="display: flex; align-items: center; gap: 6px;">
        <span class="pill-tag ${ex.label ? 'pos' : 'neg'}">${ex.label ? '+pos' : '-neg'}</span>
        <button class="btn-probe-evidence" style="background: none; border: none; color: var(--accent-cyan); cursor: pointer; font-size: 11px;" title="Test in Simulator">
          ➜
        </button>
      </div>
    `;

    row.querySelector('.btn-probe-evidence').addEventListener('click', (e) => {
      e.stopPropagation();
      probeEvidenceInSimulator(ex.string);
    });

    row.addEventListener('click', () => {
      probeEvidenceInSimulator(ex.string);
    });

    list.appendChild(row);
  });
}

function probeEvidenceInSimulator(str) {
  const tabSim = document.querySelector('.mode-tab[data-mode="simulate"]');
  if (tabSim) tabSim.click();
  document.getElementById('input-test-string').value = str;
  resetSimulation();
  animateStringPath();
}

function renderTrainingExamples(examples) {
  currentDataset = examples;
  filterAndRenderEvidence();
}

// ---------------------------------------------------------------------------
// Inference Execution
// ---------------------------------------------------------------------------

async function runInference() {
  const langSelect = document.getElementById('select-target-lang');
  const langId = langSelect ? langSelect.value || 'ends_with_ab' : 'ends_with_ab';
  const btn = document.getElementById('btn-quick-run');
  const text = document.getElementById('btn-run-text');

  text.textContent = 'Inferring...';
  btn.disabled = true;

  try {
    const payload = {
      algorithm: currentAlgorithm,
      alphabet: currentLanguages.find(l => l.id === langId)?.alphabet || ['a', 'b'],
      strict: false,
    };
    if (currentAlgorithm === 'lstar') {
      payload.target_language = langId;
    } else {
      payload.examples = currentDataset.map(ex => ({ string: ex.string, label: ex.label }));
    }

    const res = await fetch('/api/learn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    currentLearnedDFA = data.dfa;
    currentSteps = data.steps || [];

    const chosenLayout = document.getElementById('select-graph-layout').value || 'cose';
    renderElements(cyLearned, data.cytoscape || [], chosenLayout);

    const stateCount = data.dfa.states.length;
    let transitionCount = 0;
    for (const s in data.dfa.transitions) {
      transitionCount += Object.keys(data.dfa.transitions[s]).length;
    }

    document.getElementById('badge-states-count').textContent = `${stateCount} states`;
    document.getElementById('inference-meta').textContent = `${transitionCount} transitions | ${data.metadata.merges_accepted || 0} merges`;
    document.getElementById('inspect-total-states').textContent = stateCount;
    document.getElementById('inspect-total-transitions').textContent = transitionCount;
    document.getElementById('inspect-merges').textContent = data.metadata.merges_accepted || 0;

    setupReplayScrubber(currentSteps);
    await runComparison();
  } catch (err) {
    console.error("Inference run error:", err);
  } finally {
    text.textContent = 'Run Inference';
    btn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Export Helpers
// ---------------------------------------------------------------------------

function exportGraphPng() {
  if (!cyLearned) return;
  const pngData = cyLearned.png({ full: true, scale: 2.5, bg: '#060910' });
  const a = document.createElement('a');
  a.href = pngData;
  a.download = `automata_${document.getElementById('select-target-lang').value}_${currentAlgorithm}.png`;
  a.click();
}

function exportGraphJson() {
  if (!currentLearnedDFA) return;
  const jsonStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentLearnedDFA, null, 2));
  const a = document.createElement('a');
  a.href = jsonStr;
  a.download = `dfa_${document.getElementById('select-target-lang').value}.json`;
  a.click();
}

// ---------------------------------------------------------------------------
// Path Traversal Simulator
// ---------------------------------------------------------------------------

let simCurrentStep = 0;
let simPathData = null;

async function fetchSimulationData(str) {
  const res = await fetch('/api/simulate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      dfa: currentLearnedDFA,
      string: str,
    }),
  });
  return await res.json();
}

function resetSimulation() {
  simCurrentStep = 0;
  simPathData = null;
  if (cyLearned) {
    cyLearned.elements().removeClass('highlighted');
  }
  document.getElementById('sim-path-display').innerHTML = 'Ready to simulate. Enter input string above.';
  const badge = document.getElementById('sim-verdict-badge');
  badge.textContent = 'AWAITING INPUT';
  badge.style.background = 'rgba(255,255,255,0.08)';
  badge.style.color = 'var(--text-dim)';
}

async function stepStringPath() {
  const str = document.getElementById('input-test-string').value.trim();
  if (!simPathData) {
    simPathData = await fetchSimulationData(str);
    simCurrentStep = 0;
  }

  const path = simPathData.path;
  if (simCurrentStep >= path.length) return;

  const activeState = path[simCurrentStep];
  if (cyLearned) {
    cyLearned.elements().removeClass('highlighted');
    const node = cyLearned.getElementById(activeState);
    if (node) node.addClass('highlighted');

    if (simCurrentStep > 0) {
      const from = path[simCurrentStep - 1];
      const edge = cyLearned.getElementById(`e_${from}_${activeState}`);
      if (edge) edge.addClass('highlighted');
    }
  }

  renderPathTrace(path, simCurrentStep);
  simCurrentStep++;
  if (simCurrentStep === path.length) {
    showVerdict(simPathData.accepted);
  }
}

async function animateStringPath() {
  const str = document.getElementById('input-test-string').value.trim();
  resetSimulation();
  simPathData = await fetchSimulationData(str);
  const path = simPathData.path;

  for (let i = 0; i < path.length; i++) {
    const activeState = path[i];
    if (cyLearned) {
      cyLearned.elements().removeClass('highlighted');
      const node = cyLearned.getElementById(activeState);
      if (node) node.addClass('highlighted');

      if (i > 0) {
        const from = path[i - 1];
        const edge = cyLearned.getElementById(`e_${from}_${activeState}`);
        if (edge) edge.addClass('highlighted');
      }
    }
    renderPathTrace(path, i);
    await new Promise(r => setTimeout(r, 420));
  }
  showVerdict(simPathData.accepted);
}

function renderPathTrace(path, activeIndex) {
  const display = document.getElementById('sim-path-display');
  display.innerHTML = '';
  path.forEach((state, idx) => {
    const span = document.createElement('span');
    span.style.padding = '2px 6px';
    span.style.borderRadius = '3px';
    span.style.fontFamily = 'JetBrains Mono, monospace';
    span.style.fontSize = '11px';
    if (idx === activeIndex) {
      span.style.background = 'var(--accent-cyan)';
      span.style.color = '#030712';
      span.style.fontWeight = '700';
    } else if (idx < activeIndex) {
      span.style.background = 'rgba(255,255,255,0.08)';
      span.style.color = '#fff';
    } else {
      span.style.color = 'var(--text-muted)';
    }
    span.textContent = state;
    display.appendChild(span);
    if (idx < path.length - 1) {
      const arrow = document.createElement('span');
      arrow.style.color = 'var(--text-muted)';
      arrow.textContent = '➜';
      display.appendChild(arrow);
    }
  });
}

function showVerdict(accepted) {
  const badge = document.getElementById('sim-verdict-badge');
  if (accepted) {
    badge.textContent = 'ACCEPTED (IN-LANGUAGE)';
    badge.style.background = 'var(--accent-emerald-bg)';
    badge.style.color = 'var(--accent-emerald)';
  } else {
    badge.textContent = 'REJECTED (OUT-OF-LANGUAGE)';
    badge.style.background = 'var(--accent-rose-bg)';
    badge.style.color = 'var(--accent-rose)';
  }
}

// ---------------------------------------------------------------------------
// PTA Replay Scrubber
// ---------------------------------------------------------------------------

function setupReplayScrubber(steps) {
  const scrubber = document.getElementById('replay-scrubber');
  scrubber.min = 0;
  scrubber.max = Math.max(0, steps.length - 1);
  scrubber.value = 0;
  currentReplayIndex = 0;
  renderReplayStep(0);
}

function renderReplayStep(index) {
  if (!currentSteps || currentSteps.length === 0) return;
  const step = currentSteps[index];
  if (!step) return;

  document.getElementById('replay-step-counter').textContent = `Step ${index + 1} / ${currentSteps.length}`;
  document.getElementById('replay-step-type').textContent = step.step_type;
  document.getElementById('replay-step-desc').textContent = step.description;

  if (step.cytoscape && cyLearned && currentMode === 'replay') {
    renderElements(cyLearned, step.cytoscape, 'cose');
  }
}

function toggleReplayPlayback() {
  const btn = document.getElementById('btn-replay-play');
  if (isReplayPlaying) {
    clearInterval(replayTimer);
    isReplayPlaying = false;
    btn.textContent = '▶ Play';
  } else {
    isReplayPlaying = true;
    btn.textContent = '⏸ Pause';
    replayTimer = setInterval(() => {
      if (currentReplayIndex < currentSteps.length - 1) {
        currentReplayIndex++;
        document.getElementById('replay-scrubber').value = currentReplayIndex;
        renderReplayStep(currentReplayIndex);
      } else {
        clearInterval(replayTimer);
        isReplayPlaying = false;
        btn.textContent = '▶ Play';
      }
    }, 550);
  }
}

// ---------------------------------------------------------------------------
// Equivalence Polygraph & Diff
// ---------------------------------------------------------------------------

async function runComparison() {
  if (!currentLearnedDFA) return;
  const langSelect = document.getElementById('select-target-lang');
  const langId = langSelect ? langSelect.value || 'ends_with_ab' : 'ends_with_ab';

  try {
    const refRes = await fetch(`/api/reference-dfa/${langId}`);
    const refData = await refRes.json();
    renderElements(cyReference, refData.cytoscape || [], 'circle');
    document.getElementById('ref-name-badge').textContent = `${langId} (${refData.dfa.states.length} states)`;

    const compRes = await fetch('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dfa: currentLearnedDFA,
        reference_language_id: langId,
        test_size: 60,
      }),
    });
    const compData = await compRes.json();
    const metrics = compData.metrics;

    document.getElementById('comp-learned-states').textContent = compData.candidate_states;
    document.getElementById('comp-minimal-states').textContent = compData.reference_states;
    document.getElementById('comp-accuracy').textContent = `${(metrics.accuracy * 100).toFixed(1)}%`;
    document.getElementById('comp-f1').textContent = `${(metrics.f1_score * 100).toFixed(1)}%`;

    document.getElementById('inspect-accuracy-preview').textContent = `${(metrics.accuracy * 100).toFixed(1)}%`;
    document.getElementById('inspect-f1-preview').textContent = `${(metrics.f1_score * 100).toFixed(1)}%`;

    const verdictPill = document.getElementById('compare-verdict-pill');
    const cexEl = document.getElementById('compare-counterexample');
    const previewEquiv = document.getElementById('inspect-equiv-preview');

    if (metrics.is_equivalent) {
      verdictPill.textContent = 'EXACTLY EQUIVALENT (100% MATCH)';
      verdictPill.style.background = 'var(--accent-emerald-bg)';
      verdictPill.style.color = 'var(--accent-emerald)';
      cexEl.textContent = 'No counterexample: machine recognizes the identical regular language!';
      previewEquiv.textContent = 'Yes (100%)';
      previewEquiv.style.color = 'var(--accent-emerald)';
    } else {
      verdictPill.textContent = 'NOT EQUIVALENT';
      verdictPill.style.background = 'var(--accent-rose-bg)';
      verdictPill.style.color = 'var(--accent-rose)';
      cexEl.textContent = `Counterexample: ${metrics.counterexample === '' ? 'ε (empty string)' : metrics.counterexample}`;
      previewEquiv.textContent = 'No';
      previewEquiv.style.color = 'var(--accent-rose)';
    }

    const disagList = document.getElementById('disagreements-list');
    disagList.innerHTML = '';
    const diffs = compData.disagreements || [];
    if (diffs.length === 0) {
      disagList.innerHTML = '<span style="color: var(--accent-emerald); font-style: italic; font-size: 11px;">No disagreements on test sample.</span>';
    } else {
      diffs.forEach(d => {
        const row = document.createElement('div');
        row.style.display = 'flex';
        row.style.justifyContent = 'space-between';
        row.style.padding = '4px 6px';
        row.style.background = 'var(--accent-rose-bg)';
        row.style.borderRadius = '4px';
        row.style.fontSize = '11px';
        const strLabel = d.string === '' ? 'ε' : d.string;
        row.innerHTML = `
          <span style="font-weight: 700; color: #fff;">${strLabel}</span>
          <span style="color: var(--accent-rose); font-size: 10px;">Learned: ${d.candidate_predicted ? '+' : '-'} | True: ${d.true_label ? '+' : '-'}</span>
        `;
        disagList.appendChild(row);
      });
    }
  } catch (err) {
    console.error("Comparison error:", err);
  }
}

// ---------------------------------------------------------------------------
// Benchmark Labs & Charts
// ---------------------------------------------------------------------------

async function runLearningCurveExperiment() {
  const langSelect = document.getElementById('select-target-lang');
  const langId = langSelect ? langSelect.value || 'ends_with_ab' : 'ends_with_ab';
  const btn = document.getElementById('btn-run-learning-curve');
  btn.textContent = 'Running...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/experiments/learning-curve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language_id: langId,
        train_sizes: [10, 25, 50, 80],
        learners: ['edsm', 'rpni'],
        seeds: [0, 1, 2],
      }),
    });
    const data = await res.json();
    const edsmPoints = data.points.filter(p => p.learner === 'edsm');
    const rpniPoints = data.points.filter(p => p.learner === 'rpni');

    const labels = edsmPoints.map(p => p.train_size);
    const edsmAcc = edsmPoints.map(p => p.mean_accuracy * 100);
    const rpniAcc = rpniPoints.map(p => p.mean_accuracy * 100);

    const ctx = document.getElementById('chart-learning-curve').getContext('2d');
    if (chartLearningCurve) chartLearningCurve.destroy();

    chartLearningCurve = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'EDSM Accuracy (%)',
            data: edsmAcc,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            tension: 0.2,
            fill: true,
          },
          {
            label: 'RPNI Accuracy (%)',
            data: rpniAcc,
            borderColor: '#f43f5e',
            backgroundColor: 'rgba(244, 63, 94, 0.1)',
            tension: 0.2,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.06)' }, title: { display: true, text: 'Train Size', color: '#64748b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.06)' }, min: 50, max: 100, title: { display: true, text: 'Accuracy (%)', color: '#64748b' } }
        }
      }
    });
  } catch (err) {
    console.error("Learning curve error:", err);
  } finally {
    btn.textContent = 'Run Scaling Curves';
    btn.disabled = false;
  }
}

async function runNoiseStudyExperiment() {
  const langSelect = document.getElementById('select-target-lang');
  const langId = langSelect ? langSelect.value || 'ends_with_ab' : 'ends_with_ab';
  const btn = document.getElementById('btn-run-noise-study');
  btn.textContent = 'Running...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/experiments/noise-study', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language_id: langId,
        noise_rates: [0.0, 0.05, 0.10, 0.20],
        learners: ['edsm', 'rpni'],
        train_size: 60,
        seeds: [0, 1],
      }),
    });
    const data = await res.json();
    const edsmPts = data.points.filter(p => p.learner === 'edsm');
    const rpniPts = data.points.filter(p => p.learner === 'rpni');

    const labels = edsmPts.map(p => `${Math.round(p.noise_rate * 100)}%`);
    const edsmAcc = edsmPts.map(p => p.mean_accuracy * 100);
    const rpniAcc = rpniPts.map(p => p.mean_accuracy * 100);

    const ctx = document.getElementById('chart-noise-study').getContext('2d');
    if (chartNoiseStudy) chartNoiseStudy.destroy();

    chartNoiseStudy = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'EDSM (Graceful)',
            data: edsmAcc,
            backgroundColor: 'rgba(56, 189, 248, 0.8)',
            borderColor: '#38bdf8',
            borderWidth: 1,
          },
          {
            label: 'RPNI (Collapse)',
            data: rpniAcc,
            backgroundColor: 'rgba(244, 63, 94, 0.8)',
            borderColor: '#f43f5e',
            borderWidth: 1,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.06)' } },
          y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.06)' }, min: 50, max: 100 }
        }
      }
    });
  } catch (err) {
    console.error("Noise study error:", err);
  } finally {
    btn.textContent = 'Run Noise Study';
    btn.disabled = false;
  }
}

async function runActiveStudyExperiment() {
  const langSelect = document.getElementById('select-target-lang');
  const langId = langSelect ? langSelect.value || 'ends_with_ab' : 'ends_with_ab';
  const btn = document.getElementById('btn-run-active-study');
  btn.textContent = 'Running...';
  btn.disabled = true;

  try {
    const res = await fetch('/api/experiments/active-study', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        language_id: langId,
        initial_size: 6,
        batch_size: 6,
        rounds: 4,
        seed: 42,
      }),
    });
    const data = await res.json();
    const labels = data.query_budgets;
    const activeAcc = data.active_accuracies.map(a => a * 100);
    const randomAcc = data.random_accuracies.map(a => a * 100);

    const ctx = document.getElementById('chart-active-study').getContext('2d');
    if (chartActiveStudy) chartActiveStudy.destroy();

    chartActiveStudy = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Active (Uncertainty)',
            data: activeAcc,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            tension: 0.2,
            fill: true,
          },
          {
            label: 'Random Sampling',
            data: randomAcc,
            borderColor: '#64748b',
            backgroundColor: 'rgba(100, 116, 139, 0.1)',
            tension: 0.2,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.06)' }, title: { display: true, text: 'Query Budget', color: '#64748b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.06)' }, min: 50, max: 100 }
        }
      }
    });
  } catch (err) {
    console.error("Active study error:", err);
  } finally {
    btn.textContent = 'Run Active Oracle';
    btn.disabled = false;
  }
}
