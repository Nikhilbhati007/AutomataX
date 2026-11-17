/* ==========================================================================
   AutomataX — Cyber-Detective & Forensic Inference Lab (app.js)
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
let soundEnabled = true;

// Cytoscape instances
let cyLearned = null;
let cySim = null;
let cyReplay = null;
let cyReference = null;
let cyArchitect = null;

// Automata Architect state
let currentArchitectData = null;
let activeArchitectMode = "eps_nfa";
let architectPresets = [];
let currentArchitectSimResult = null;
let currentArchitectStepIndex = 0;

// Chart.js instances
let chartLearningCurve = null;
let chartNoiseStudy = null;
let chartActiveStudy = null;

// Active evidence filters
let currentEvidenceFilter = "all";
let currentEvidenceSearch = "";

// ---------------------------------------------------------------------------
// Web Audio API Synthesizer (Tactical SFX)
// ---------------------------------------------------------------------------
let audioCtx = null;

function getAudioContext() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

function playTone(freq, type = 'sine', duration = 0.08, gainVal = 0.05) {
  if (!soundEnabled) return;
  try {
    const ctx = getAudioContext();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    gain.gain.setValueAtTime(gainVal, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  } catch (e) {
    // Audio context may be restricted by autoplay policy
  }
}

function sfxClick() { playTone(600, 'sine', 0.04, 0.03); }
function sfxStep() { playTone(880, 'triangle', 0.06, 0.05); }
function sfxAccept() {
  if (!soundEnabled) return;
  playTone(523.25, 'sine', 0.12, 0.06);
  setTimeout(() => playTone(659.25, 'sine', 0.12, 0.06), 80);
  setTimeout(() => playTone(783.99, 'sine', 0.22, 0.08), 160);
}
function sfxReject() {
  if (!soundEnabled) return;
  playTone(220, 'sawtooth', 0.18, 0.06);
  setTimeout(() => playTone(180, 'sawtooth', 0.22, 0.06), 90);
}
function sfxDeploy() {
  if (!soundEnabled) return;
  playTone(440, 'triangle', 0.08, 0.05);
  setTimeout(() => playTone(880, 'sine', 0.15, 0.07), 70);
}

// ---------------------------------------------------------------------------
// Cytoscape Visual Theme (Cyber-Detective HUD)
// ---------------------------------------------------------------------------

const CY_STYLE = [
  {
    selector: 'node',
    style: {
      'content': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#0d1527',
      'color': '#f8fafc',
      'font-size': '12px',
      'font-family': 'JetBrains Mono, monospace',
      'font-weight': 'bold',
      'width': 46,
      'height': 46,
      'border-width': 2.5,
      'border-color': '#1e3a5f',
      'border-style': 'solid',
      'shadow-blur': 12,
      'shadow-color': 'rgba(0,0,0,0.6)',
      'shadow-opacity': 0.8,
      'transition-property': 'background-color, border-color, width, height, border-width, shadow-color',
      'transition-duration': '0.2s',
    }
  },
  {
    selector: 'node.start',
    style: {
      'border-color': '#00f0ff',
      'border-width': 3.5,
      'background-color': '#07243b',
      'color': '#ffffff',
      'shadow-blur': 20,
      'shadow-color': 'rgba(0, 240, 255, 0.6)',
    }
  },
  {
    selector: 'node.accept',
    style: {
      'border-color': '#00ff9d',
      'border-width': 7,
      'border-style': 'double', // Double ring formal DFA convention
      'background-color': '#042e20',
      'color': '#a7f3d0',
      'shadow-blur': 22,
      'shadow-color': 'rgba(0, 255, 157, 0.5)',
    }
  },
  {
    selector: 'node.start.accept',
    style: {
      'border-color': '#00ff9d',
      'border-width': 7,
      'border-style': 'double',
      'background-color': '#07323b',
      'color': '#ffffff',
      'shadow-blur': 25,
      'shadow-color': 'rgba(0, 240, 255, 0.7)',
    }
  },
  {
    selector: 'node.highlighted',
    style: {
      'background-color': '#00f0ff',
      'border-color': '#ffffff',
      'border-width': 5,
      'color': '#050811',
      'width': 54,
      'height': 54,
      'shadow-blur': 35,
      'shadow-color': '#00f0ff',
      'shadow-opacity': 1,
    }
  },
  {
    selector: 'node.selected-inspect',
    style: {
      'border-color': '#f59e0b',
      'border-width': 4,
      'shadow-blur': 20,
      'shadow-color': '#f59e0b',
    }
  },
  {
    selector: 'edge',
    style: {
      'content': 'data(label)',
      'font-size': '11px',
      'font-family': 'JetBrains Mono, monospace',
      'font-weight': 'bold',
      'color': '#94a3b8',
      'text-background-color': '#070d1a',
      'text-background-opacity': 0.95,
      'text-background-padding': '4px',
      'text-border-width': 1,
      'text-border-color': '#1e3a5f',
      'text-border-style': 'solid',
      'curve-style': 'bezier',
      'control-point-step-size': 45,
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#475569',
      'line-color': '#334155',
      'width': 2.2,
      'arrow-scale': 1.15,
      'transition-property': 'line-color, target-arrow-color, width, color',
      'transition-duration': '0.15s',
    }
  },
  {
    selector: 'edge.highlighted',
    style: {
      'line-color': '#00f0ff',
      'target-arrow-color': '#00f0ff',
      'width': 4.5,
      'color': '#00f0ff',
      'text-border-color': '#00f0ff',
      'shadow-blur': 15,
      'shadow-color': '#00f0ff',
    }
  },
  {
    selector: 'node.active-set',
    style: {
      'background-color': '#f59e0b',
      'border-color': '#ffffff',
      'border-width': 4.5,
      'color': '#050811',
      'width': 52,
      'height': 52,
      'shadow-blur': 30,
      'shadow-color': 'rgba(245, 158, 11, 0.9)',
      'shadow-opacity': 1,
    }
  },
  {
    selector: 'edge.epsilon-edge',
    style: {
      'line-style': 'dashed',
      'line-dash-pattern': [6, 4],
      'line-color': '#f59e0b',
      'target-arrow-color': '#f59e0b',
      'color': '#fbbf24',
      'font-style': 'italic',
      'font-weight': 'bold',
      'width': 2.5,
    }
  }
];

function initCy(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return null;
  const cy = cytoscape({
    container: container,
    elements: [],
    style: CY_STYLE,
    layout: { name: 'circle' },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
    wheelSensitivity: 0.25,
  });

  // State inspection click listener
  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    cy.elements().removeClass('selected-inspect');
    node.addClass('selected-inspect');
    showStateInspector(node);
    sfxClick();
  });

  return cy;
}

function renderElements(cy, elements, layoutName = 'cose') {
  if (!cy) return;
  cy.elements().remove();
  cy.add(elements);
  applyGraphLayout(cy, layoutName);
}

function applyGraphLayout(cy, layoutName) {
  if (!cy) return;
  let layoutConfig = { name: layoutName, fit: true, padding: 35 };

  if (layoutName === 'cose') {
    layoutConfig = {
      name: 'cose',
      animate: false,
      fit: true,
      padding: 35,
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
      padding: 35,
      concentric: function(node) {
        return node.data('is_start') ? 10 : (node.data('is_accept') ? 5 : 1);
      },
      levelWidth: () => 1,
    };
  } else if (layoutName === 'breadthfirst') {
    layoutConfig = {
      name: 'breadthfirst',
      fit: true,
      padding: 35,
      directed: true,
      roots: cy.nodes('[?is_start]'),
    };
  }

  const layout = cy.layout(layoutConfig);
  layout.run();
}

function showStateInspector(node) {
  const inspector = document.getElementById('state-inspector-card');
  if (!inspector) return;
  inspector.classList.remove('hidden');

  const id = node.data('id');
  const isStart = node.data('is_start');
  const isAccept = node.data('is_accept');

  document.getElementById('inspect-state-id').textContent = `State: ${id} ${isStart ? '[START]' : ''} ${isAccept ? '[ACCEPT]' : ''}`;
  document.getElementById('inspect-state-type').textContent = isAccept ? 'Type: Accept (Final)' : (isStart ? 'Type: Start State' : 'Type: Normal Intermediate');

  // Compute incoming and outgoing edges
  const outEdges = node.outgoers('edge');
  const transitions = [];
  outEdges.forEach(e => {
    transitions.push(`--(${e.data('label')})--> ${e.data('target')}`);
  });
  document.getElementById('inspect-state-transitions').textContent = `Transitions: ${transitions.length ? transitions.join(' | ') : 'None'}`;
}

// ---------------------------------------------------------------------------
// App Bootstrapping
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
  cyLearned = initCy('cy-container');
  cySim = initCy('cy-sim-container');
  cyReplay = initCy('cy-replay-container');
  cyReference = initCy('cy-reference-container');
  cyArchitect = initCy('cy-architect-container');

  setupTabs();
  setupEventListeners();
  await loadCatalogAndPresets();
  await generateData();
  await runInference();
  await initArchitectSector();
});

// ---------------------------------------------------------------------------
// Tactical Tabs Navigation
// ---------------------------------------------------------------------------

function setupTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      sfxClick();
      tabs.forEach(t => {
        t.classList.remove('active', 'bg-cyan-950/70', 'text-cyan-300', 'border', 'border-cyan-600/60');
        t.classList.add('text-slate-400');
      });
      tab.classList.add('active', 'bg-cyan-950/70', 'text-cyan-300', 'border', 'border-cyan-600/60');
      tab.classList.remove('text-slate-400');

      panels.forEach(p => p.classList.add('hidden'));
      const targetId = tab.getAttribute('data-target');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.remove('hidden');
        setTimeout(() => {
          if (targetId === 'tab-investigate' && cyLearned) cyLearned.resize().fit(35);
          if (targetId === 'tab-simulator' && cySim) cySim.resize().fit(35);
          if (targetId === 'tab-replay' && cyReplay) cyReplay.resize().fit(35);
          if (targetId === 'tab-compare' && cyReference) cyReference.resize().fit(35);
          if (targetId === 'tab-architect' && cyArchitect) cyArchitect.resize().fit(35);
        }, 80);
      }
    });
  });
}

// ---------------------------------------------------------------------------
// Catalog & Case Files Loading
// ---------------------------------------------------------------------------

async function loadCatalogAndPresets() {
  try {
    const [langRes, presetRes] = await Promise.all([
      fetch('/api/languages').then(r => r.json()),
      fetch('/api/presets').then(r => r.json()),
    ]);

    currentLanguages = langRes.languages || [];
    currentPresets = presetRes.presets || [];

    // Populate language selector
    const langSelect = document.getElementById('select-target-lang');
    langSelect.innerHTML = '';
    currentLanguages.forEach(l => {
      const opt = document.createElement('option');
      opt.value = l.id;
      opt.textContent = `${l.name} (${l.expected_min_dfa_states} min states)`;
      langSelect.appendChild(opt);
    });

    // Populate Dossier Vault Modal
    renderDossierCards();
    updateLanguageMeta();
  } catch (err) {
    console.error("Failed to load catalog/presets:", err);
  }
}

function updateLanguageMeta() {
  const selectedId = document.getElementById('select-target-lang').value;
  const lang = currentLanguages.find(l => l.id === selectedId);
  if (!lang) return;

  document.getElementById('target-desc').textContent = lang.description;
  document.getElementById('target-alphabet-badge').textContent = `Σ = {${lang.alphabet.join(', ')}}`;
}

function renderDossierCards() {
  const container = document.getElementById('dossier-cards-grid');
  if (!container) return;
  container.innerHTML = '';
  document.getElementById('dossier-count-badge').textContent = currentPresets.length;

  currentPresets.forEach((p, idx) => {
    const card = document.createElement('div');
    card.className = 'dossier-card p-4 flex flex-col justify-between space-y-3';
    
    const clearance = p.clearance || 'CONFIDENTIAL';
    let stampColor = 'border-amber-500 text-amber-400 bg-amber-950/40';
    if (clearance === 'TOP SECRET') stampColor = 'border-rose-500 text-rose-400 bg-rose-950/40';
    if (clearance === 'RESTRICTED') stampColor = 'border-cyan-500 text-cyan-400 bg-cyan-950/40';

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between">
          <span class="stamp-classified ${stampColor}">${clearance}</span>
          <span class="font-mono text-[11px] text-slate-400">${p.case_code || `CASE-00${idx+1}`}</span>
        </div>
        <h4 class="text-sm font-bold text-slate-100 font-display mt-2">${p.title}</h4>
        <p class="text-xs text-cyan-300/90 font-mono mt-0.5">${p.subtitle}</p>
        <p class="text-[11px] text-slate-400 mt-2 leading-relaxed font-sans">${p.description}</p>
        ${p.suspect ? `<div class="mt-2 text-[10px] font-mono text-amber-300/80 bg-amber-950/20 px-2 py-1 rounded border border-amber-900/40">Suspect Signature: ${p.suspect}</div>` : ''}
      </div>
      <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between">
        <span class="text-[10px] font-mono text-slate-500">Difficulty: <span class="text-slate-300 font-bold">${p.difficulty || 'Normal'}</span></span>
        <button class="btn-deploy-case hud-btn hud-btn-amber text-[10px] py-1 px-3" data-preset-id="${p.id}">
          Deploy Investigation
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
  sfxDeploy();
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
  sfxClick();
  document.getElementById('modal-dossier-vault').classList.remove('hidden');
}

function closeDossierModal() {
  document.getElementById('modal-dossier-vault').classList.add('hidden');
}

// ---------------------------------------------------------------------------
// Event Listeners Setup
// ---------------------------------------------------------------------------

function setupEventListeners() {
  // Knobs
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
    sfxClick();
  });

  document.getElementById('btn-generate-data').addEventListener('click', () => {
    sfxClick();
    generateData();
  });

  // Algorithm selectors
  document.querySelectorAll('.algo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      sfxClick();
      document.querySelectorAll('.algo-btn').forEach(b => {
        b.classList.remove('active', 'border-cyan-500/80', 'bg-cyan-500/10', 'text-cyan-300');
        b.classList.add('border-slate-800', 'bg-slate-900', 'text-slate-400');
      });
      btn.classList.add('active', 'border-cyan-500/80', 'bg-cyan-500/10', 'text-cyan-300');
      btn.classList.remove('border-slate-800', 'bg-slate-900', 'text-slate-400');
      currentAlgorithm = btn.getAttribute('data-algo');

      const explainer = document.getElementById('algo-explainer');
      if (currentAlgorithm === 'edsm') {
        explainer.textContent = "EDSM: Evaluates all blue-fringe candidate merges by label endorsement gain; excels under sparse sample data.";
      } else if (currentAlgorithm === 'rpni') {
        explainer.textContent = "RPNI: Merges blue states in canonical shortlex order with the earliest compatible red state.";
      } else {
        explainer.textContent = "Angluin's L*: Active learner using observation table closedness/consistency with equivalence oracle queries.";
      }
    });
  });

  // Quick Run Button
  document.getElementById('btn-quick-run').addEventListener('click', () => {
    sfxClick();
    runInference();
  });

  // Dossier Modal
  document.getElementById('btn-open-dossier').addEventListener('click', openDossierModal);
  document.getElementById('btn-close-dossier').addEventListener('click', closeDossierModal);
  document.getElementById('modal-dossier-vault').addEventListener('click', (e) => {
    if (e.target.id === 'modal-dossier-vault') closeDossierModal();
  });

  // Audio Toggle
  const audioBtn = document.getElementById('btn-toggle-sfx');
  audioBtn.addEventListener('click', () => {
    soundEnabled = !soundEnabled;
    document.getElementById('sfx-icon').textContent = soundEnabled ? '🔊' : '🔇';
    document.getElementById('sfx-label').textContent = soundEnabled ? 'SFX: ON' : 'SFX: MUTE';
    if (soundEnabled) sfxClick();
  });

  // Graph Tools Dock
  document.getElementById('select-graph-layout').addEventListener('change', (e) => {
    sfxClick();
    if (cyLearned) applyGraphLayout(cyLearned, e.target.value);
  });
  document.getElementById('btn-fit-graph').addEventListener('click', () => {
    sfxClick();
    if (cyLearned) cyLearned.fit(35);
  });
  document.getElementById('btn-zoom-in').addEventListener('click', () => {
    sfxClick();
    if (cyLearned) cyLearned.zoom(cyLearned.zoom() * 1.25);
  });
  document.getElementById('btn-zoom-out').addEventListener('click', () => {
    sfxClick();
    if (cyLearned) cyLearned.zoom(cyLearned.zoom() * 0.8);
  });
  document.getElementById('btn-export-png').addEventListener('click', exportGraphPng);
  document.getElementById('btn-export-json').addEventListener('click', exportGraphJson);

  // Evidence Search & Filter
  document.getElementById('input-search-evidence').addEventListener('input', (e) => {
    currentEvidenceSearch = e.target.value.toLowerCase();
    filterAndRenderEvidence();
  });

  document.querySelectorAll('.evidence-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      sfxClick();
      document.querySelectorAll('.evidence-filter-btn').forEach(b => {
        b.classList.remove('active', 'bg-cyan-950', 'text-cyan-300', 'font-bold');
      });
      btn.classList.add('active', 'bg-cyan-950', 'text-cyan-300', 'font-bold');
      currentEvidenceFilter = btn.getAttribute('data-filter');
      filterAndRenderEvidence();
    });
  });

  // Plant Clue Modal
  setupPlantClueModal();

  // Simulator controls
  document.getElementById('btn-play-simulate').addEventListener('click', () => {
    sfxClick();
    animateStringPath();
  });
  document.getElementById('btn-step-simulate').addEventListener('click', () => {
    sfxClick();
    stepStringPath();
  });
  document.getElementById('btn-reset-simulate').addEventListener('click', () => {
    sfxClick();
    resetSimulation();
  });

  document.querySelectorAll('.btn-quick-string').forEach(btn => {
    btn.addEventListener('click', () => {
      sfxClick();
      document.getElementById('input-test-string').value = btn.getAttribute('data-str');
      resetSimulation();
      animateStringPath();
    });
  });

  // Replay controls
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
      sfxStep();
    }
  });
  document.getElementById('btn-replay-next').addEventListener('click', () => {
    if (currentReplayIndex < currentSteps.length - 1) {
      currentReplayIndex++;
      scrubber.value = currentReplayIndex;
      renderReplayStep(currentReplayIndex);
      sfxStep();
    }
  });
  document.getElementById('btn-replay-play').addEventListener('click', toggleReplayPlayback);

  // Compare & Experiments
  document.getElementById('btn-recompare').addEventListener('click', () => {
    sfxClick();
    runComparison();
  });
  document.getElementById('btn-run-learning-curve').addEventListener('click', () => {
    sfxClick();
    runLearningCurveExperiment();
  });
  document.getElementById('btn-run-noise-study').addEventListener('click', () => {
    sfxClick();
    runNoiseStudyExperiment();
  });
  document.getElementById('btn-run-active-study').addEventListener('click', () => {
    sfxClick();
    runActiveStudyExperiment();
  });
}

// ---------------------------------------------------------------------------
// Plant Custom Clue Setup
// ---------------------------------------------------------------------------

let newClueLabel = true;

function setupPlantClueModal() {
  const modal = document.getElementById('modal-plant-clue');
  document.getElementById('btn-plant-clue').addEventListener('click', () => {
    sfxClick();
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
    posBtn.className = 'hud-btn text-xs py-2 border border-emerald-500 bg-emerald-950/60 text-emerald-300 font-bold';
    negBtn.className = 'hud-btn text-xs py-2 border border-slate-700 bg-slate-900 text-slate-400 font-bold';
    sfxClick();
  });

  negBtn.addEventListener('click', () => {
    newClueLabel = false;
    negBtn.className = 'hud-btn text-xs py-2 border border-rose-500 bg-rose-950/60 text-rose-300 font-bold';
    posBtn.className = 'hud-btn text-xs py-2 border border-slate-700 bg-slate-900 text-slate-400 font-bold';
    sfxClick();
  });

  document.getElementById('btn-submit-clue').addEventListener('click', () => {
    const rawStr = document.getElementById('input-new-clue-string').value.trim();
    currentDataset.unshift({ string: rawStr, label: newClueLabel });
    modal.classList.add('hidden');
    document.getElementById('input-new-clue-string').value = '';
    filterAndRenderEvidence();
    sfxDeploy();
    runInference();
  });
}

// ---------------------------------------------------------------------------
// Dataset Generation & Evidence Rendering
// ---------------------------------------------------------------------------

async function generateData() {
  const target = document.getElementById('select-target-lang').value;
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

  let posCount = 0;
  let negCount = 0;
  currentDataset.forEach(ex => {
    if (ex.label) posCount++; else negCount++;
  });

  document.getElementById('train-count').textContent = currentDataset.length;
  document.getElementById('filter-all-cnt').textContent = currentDataset.length;
  document.getElementById('filter-pos-cnt').textContent = posCount;
  document.getElementById('filter-neg-cnt').textContent = negCount;

  if (filtered.length === 0) {
    list.innerHTML = '<div class="text-slate-500 italic text-center py-4">No matching forensic clues found.</div>';
    return;
  }

  filtered.forEach((ex, idx) => {
    const card = document.createElement('div');
    card.className = `evidence-card ${ex.label ? 'pos' : 'neg'}`;
    const strDisplay = ex.string === '' ? 'ε (empty string)' : ex.string;
    const lenDisplay = ex.string.length;

    card.innerHTML = `
      <div class="flex items-center space-x-2 font-mono">
        <span class="text-[10px] text-slate-500">#${String(idx+1).padStart(2, '0')}</span>
        <span class="text-xs font-bold ${ex.label ? 'text-emerald-300' : 'text-rose-300'}">${strDisplay}</span>
        <span class="text-[10px] px-1 py-0.2 rounded bg-slate-800 text-slate-400">len:${lenDisplay}</span>
      </div>
      <div class="flex items-center space-x-2">
        <span class="text-[9px] font-bold uppercase font-mono px-1.5 py-0.5 rounded ${
          ex.label ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
        }">${ex.label ? '+ POS' : '- NEG'}</span>
        <button class="btn-probe-evidence text-[9px] font-mono px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded border border-slate-700 transition" title="Test in Simulator">
          Probe ➜
        </button>
      </div>
    `;

    card.querySelector('.btn-probe-evidence').addEventListener('click', (e) => {
      e.stopPropagation();
      probeEvidenceInSimulator(ex.string);
    });

    card.addEventListener('click', () => {
      probeEvidenceInSimulator(ex.string);
    });

    list.appendChild(card);
  });
}

function probeEvidenceInSimulator(str) {
  sfxClick();
  const tabSim = document.querySelector('.nav-tab[data-target="tab-simulator"]');
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
  const langId = document.getElementById('select-target-lang').value;
  const btn = document.getElementById('btn-quick-run');
  const spin = document.getElementById('spin-inference');
  const text = document.getElementById('btn-run-text');

  spin.classList.remove('hidden');
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

    // Render Main Canvas with selected layout
    const chosenLayout = document.getElementById('select-graph-layout').value || 'cose';
    renderElements(cyLearned, data.cytoscape || [], chosenLayout);

    document.getElementById('badge-states-count').textContent = `${data.dfa.states.length} states`;
    document.getElementById('inference-meta').textContent = `Merges: ${data.metadata.merges_accepted || 0} | Steps: ${currentSteps.length}`;

    // Mirror to Sim Canvas
    renderElements(cySim, data.cytoscape || [], 'cose');

    // Setup Replay Scrubber
    setupReplayScrubber(currentSteps);

    // Run Comparison
    await runComparison();
    sfxAccept();
  } catch (err) {
    console.error("Inference run error:", err);
    sfxReject();
  } finally {
    spin.classList.add('hidden');
    text.textContent = 'Run Inference';
    btn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Export Helpers
// ---------------------------------------------------------------------------

function exportGraphPng() {
  if (!cyLearned) return;
  sfxClick();
  const pngData = cyLearned.png({ full: true, scale: 2.5, bg: '#070d1a' });
  const a = document.createElement('a');
  a.href = pngData;
  a.download = `automata_${document.getElementById('select-target-lang').value}_${currentAlgorithm}.png`;
  a.click();
}

function exportGraphJson() {
  if (!currentLearnedDFA) return;
  sfxClick();
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
  if (cySim) {
    cySim.elements().removeClass('highlighted');
  }
  document.getElementById('sim-path-display').innerHTML = '<span class="text-slate-500">Ready to simulate</span>';
  const badge = document.getElementById('sim-verdict-badge');
  badge.textContent = 'AWAITING INPUT';
  badge.className = 'px-5 py-2 rounded-full text-xs font-bold font-mono tracking-wider bg-slate-800 text-slate-400 border border-slate-700';
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
  if (cySim) {
    cySim.elements().removeClass('highlighted');
    const node = cySim.getElementById(activeState);
    if (node) node.addClass('highlighted');

    if (simCurrentStep > 0) {
      const from = path[simCurrentStep - 1];
      const edge = cySim.getElementById(`e_${from}_${activeState}`);
      if (edge) edge.addClass('highlighted');
    }
  }

  renderPathTrace(path, simCurrentStep);
  sfxStep();

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
    if (cySim) {
      cySim.elements().removeClass('highlighted');
      const node = cySim.getElementById(activeState);
      if (node) node.addClass('highlighted');

      if (i > 0) {
        const from = path[i - 1];
        const edge = cySim.getElementById(`e_${from}_${activeState}`);
        if (edge) edge.addClass('highlighted');
      }
    }
    renderPathTrace(path, i);
    sfxStep();
    await new Promise(r => setTimeout(r, 450));
  }
  showVerdict(simPathData.accepted);
}

function renderPathTrace(path, activeIndex) {
  const display = document.getElementById('sim-path-display');
  display.innerHTML = '';
  path.forEach((state, idx) => {
    const span = document.createElement('span');
    span.className = `px-2 py-0.5 rounded text-xs font-mono ${
      idx === activeIndex
        ? 'bg-cyan-400 text-slate-950 font-bold token-active shadow-md shadow-cyan-400/50'
        : idx < activeIndex
        ? 'bg-slate-800 text-slate-300'
        : 'text-slate-600'
    }`;
    span.textContent = state;
    display.appendChild(span);
    if (idx < path.length - 1) {
      const arrow = document.createElement('span');
      arrow.className = 'text-slate-600';
      arrow.textContent = '→';
      display.appendChild(arrow);
    }
  });
}

function showVerdict(accepted) {
  const badge = document.getElementById('sim-verdict-badge');
  if (accepted) {
    badge.textContent = 'VERDICT: ACCEPTED [SIGNATURE MATCH]';
    badge.className = 'px-5 py-2 rounded-full text-xs font-bold font-mono tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500 shadow-lg shadow-emerald-500/20';
    sfxAccept();
  } else {
    badge.textContent = 'VERDICT: REJECTED [ANOMALY DETECTED]';
    badge.className = 'px-5 py-2 rounded-full text-xs font-bold font-mono tracking-wider bg-rose-500/20 text-rose-400 border border-rose-500 shadow-lg shadow-rose-500/20';
    sfxReject();
  }
}

// ---------------------------------------------------------------------------
// Crime Scene Replay Scrubber
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
  document.getElementById('replay-state-count').textContent = `States: ${step.data?.state_count || '--'}`;

  if (step.cytoscape) {
    renderElements(cyReplay, step.cytoscape, 'cose');
  }
}

function toggleReplayPlayback() {
  const btn = document.getElementById('btn-replay-play');
  if (isReplayPlaying) {
    clearInterval(replayTimer);
    isReplayPlaying = false;
    btn.textContent = '▶ Auto-Play';
  } else {
    isReplayPlaying = true;
    btn.textContent = '⏸ Pause';
    replayTimer = setInterval(() => {
      if (currentReplayIndex < currentSteps.length - 1) {
        currentReplayIndex++;
        document.getElementById('replay-scrubber').value = currentReplayIndex;
        renderReplayStep(currentReplayIndex);
        sfxStep();
      } else {
        clearInterval(replayTimer);
        isReplayPlaying = false;
        btn.textContent = '▶ Auto-Play';
      }
    }, 600);
  }
}

// ---------------------------------------------------------------------------
// Ground Truth Equivalence & Polygraph
// ---------------------------------------------------------------------------

async function runComparison() {
  if (!currentLearnedDFA) return;
  const langId = document.getElementById('select-target-lang').value;

  try {
    // 1. Fetch Reference DFA
    const refRes = await fetch(`/api/reference-dfa/${langId}`);
    const refData = await refRes.json();
    renderElements(cyReference, refData.cytoscape || [], 'circle');
    document.getElementById('ref-name-badge').textContent = `${langId} (${refData.dfa.states.length} states)`;

    // 2. Run Comparison Endpoint
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

    const verdictPill = document.getElementById('compare-verdict-pill');
    const cexEl = document.getElementById('compare-counterexample');

    if (metrics.is_equivalent) {
      verdictPill.textContent = 'EXACTLY EQUIVALENT (100% MATCH)';
      verdictPill.className = 'inline-block px-3.5 py-1.5 rounded-full text-xs font-bold font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500';
      cexEl.textContent = 'No counterexample: machine recognizes the identical regular language!';
    } else {
      verdictPill.textContent = 'NOT EQUIVALENT';
      verdictPill.className = 'inline-block px-3.5 py-1.5 rounded-full text-xs font-bold font-mono bg-rose-500/20 text-rose-400 border border-rose-500';
      cexEl.textContent = `Counterexample string: ${metrics.counterexample === '' ? 'ε (empty string)' : metrics.counterexample}`;
    }

    // Populate Disagreements List
    const disagList = document.getElementById('disagreements-list');
    disagList.innerHTML = '';
    const diffs = compData.disagreements || [];
    if (diffs.length === 0) {
      disagList.innerHTML = '<p class="text-emerald-400 italic font-mono text-xs">No disagreements on test sample.</p>';
    } else {
      diffs.forEach(d => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between px-2.5 py-1 bg-rose-950/30 border border-rose-900/60 rounded text-xs';
        const strLabel = d.string === '' ? 'ε' : d.string;
        row.innerHTML = `
          <span class="text-slate-200 font-bold">${strLabel}</span>
          <span class="text-[10px] text-rose-400 font-bold">Learned: ${d.candidate_predicted ? '+' : '-'} | True: ${d.true_label ? '+' : '-'}</span>
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
  const langId = document.getElementById('select-target-lang').value;
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
            borderColor: '#00f0ff',
            backgroundColor: 'rgba(0, 240, 255, 0.12)',
            tension: 0.25,
            fill: true,
          },
          {
            label: 'RPNI Accuracy (%)',
            data: rpniAcc,
            borderColor: '#ff2a5f',
            backgroundColor: 'rgba(255, 42, 95, 0.12)',
            tension: 0.25,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: '#141f36' }, title: { display: true, text: 'Train Size', color: '#64748b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: '#141f36' }, min: 50, max: 100, title: { display: true, text: 'Test Accuracy (%)', color: '#64748b' } }
        }
      }
    });
    sfxAccept();
  } catch (err) {
    console.error("Learning curve error:", err);
  } finally {
    btn.textContent = 'Run Scaling Curves';
    btn.disabled = false;
  }
}

async function runNoiseStudyExperiment() {
  const langId = document.getElementById('select-target-lang').value;
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
            label: 'EDSM (Graceful Degradation)',
            data: edsmAcc,
            backgroundColor: 'rgba(0, 240, 255, 0.75)',
            borderColor: '#00f0ff',
            borderWidth: 1,
          },
          {
            label: 'RPNI (Premature Collapse)',
            data: rpniAcc,
            backgroundColor: 'rgba(255, 42, 95, 0.75)',
            borderColor: '#ff2a5f',
            borderWidth: 1,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: '#141f36' } },
          y: { ticks: { color: '#64748b' }, grid: { color: '#141f36' }, min: 50, max: 100 }
        }
      }
    });
    sfxAccept();
  } catch (err) {
    console.error("Noise study error:", err);
  } finally {
    btn.textContent = 'Run Noise Study';
    btn.disabled = false;
  }
}

async function runActiveStudyExperiment() {
  const langId = document.getElementById('select-target-lang').value;
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
            label: 'Active (Uncertainty Oracle)',
            data: activeAcc,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.12)',
            tension: 0.25,
            fill: true,
          },
          {
            label: 'Random Sampling Baseline',
            data: randomAcc,
            borderColor: '#64748b',
            backgroundColor: 'rgba(100, 116, 139, 0.12)',
            tension: 0.25,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { family: 'JetBrains Mono', size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: '#141f36' }, title: { display: true, text: 'Query Budget', color: '#64748b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: '#141f36' }, min: 50, max: 100 }
        }
      }
    });
    sfxAccept();
  } catch (err) {
    console.error("Active study error:", err);
  } finally {
    btn.textContent = 'Run Active Oracle';
    btn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Automata Architect Sector (ε-NFA ↔ NFA ↔ DFA ↔ Minimized DFA)
// ---------------------------------------------------------------------------

async function initArchitectSector() {
  try {
    const res = await fetch('/api/architect/presets');
    if (res.ok) {
      architectPresets = await res.json();
      renderArchitectPresets();
    }

    const btnRegex = document.getElementById('btn-arch-mode-regex');
    const btnCustom = document.getElementById('btn-arch-mode-custom');
    const boxRegex = document.getElementById('arch-box-regex');
    const boxCustom = document.getElementById('arch-box-custom');

    if (btnRegex && btnCustom && boxRegex && boxCustom) {
      btnRegex.addEventListener('click', () => {
        sfxClick();
        btnRegex.className = 'px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-600 font-bold';
        btnCustom.className = 'px-2 py-0.5 rounded text-slate-400 hover:text-slate-200';
        boxRegex.classList.remove('hidden');
        boxCustom.classList.add('hidden');
      });

      btnCustom.addEventListener('click', () => {
        sfxClick();
        btnCustom.className = 'px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-600 font-bold';
        btnRegex.className = 'px-2 py-0.5 rounded text-slate-400 hover:text-slate-200';
        boxCustom.classList.remove('hidden');
        boxRegex.classList.add('hidden');
      });
    }

    const btnCompile = document.getElementById('btn-arch-compile');
    if (btnCompile) {
      btnCompile.addEventListener('click', () => compileArchitect());
    }

    const tabBtns = document.querySelectorAll('.arch-tab-btn');
    tabBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.getAttribute('data-mode');
        switchArchitectRepresentation(mode);
      });
    });

    const layoutSel = document.getElementById('arch-layout-select');
    if (layoutSel) {
      layoutSel.addEventListener('change', () => {
        if (cyArchitect) {
          applyLayout(cyArchitect, layoutSel.value);
        }
      });
    }

    const btnFit = document.getElementById('btn-arch-fit');
    if (btnFit) {
      btnFit.addEventListener('click', () => {
        sfxClick();
        if (cyArchitect) cyArchitect.fit(35);
      });
    }

    const btnSimRun = document.getElementById('btn-arch-sim-run');
    if (btnSimRun) {
      btnSimRun.addEventListener('click', () => simulateArchitectString(false));
    }

    const btnSimStep = document.getElementById('btn-arch-sim-step');
    if (btnSimStep) {
      btnSimStep.addEventListener('click', () => simulateArchitectString(true));
    }

    const strInput = document.getElementById('arch-sim-string');
    if (strInput) {
      strInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          simulateArchitectString(false);
        }
      });
    }

    await compileArchitect();
  } catch (err) {
    console.error("Failed to initialize architect sector:", err);
  }
}

function renderArchitectPresets() {
  const container = document.getElementById('arch-preset-chips');
  if (!container) return;
  container.innerHTML = '';

  architectPresets.forEach((p, idx) => {
    const chip = document.createElement('button');
    chip.className = `px-2 py-1 rounded text-[11px] font-mono border transition ${
      idx === 0 ? 'bg-amber-950/80 text-amber-300 border-amber-600' : 'bg-slate-900 text-slate-300 border-slate-700 hover:border-amber-500/50'
    }`;
    chip.textContent = p.name;
    chip.title = `${p.pattern} (${p.description})`;
    chip.addEventListener('click', () => {
      sfxClick();
      document.querySelectorAll('#arch-preset-chips button').forEach(b => {
        b.className = 'px-2 py-1 rounded text-[11px] font-mono border transition bg-slate-900 text-slate-300 border-slate-700 hover:border-amber-500/50';
      });
      chip.className = 'px-2 py-1 rounded text-[11px] font-mono border transition bg-amber-950/80 text-amber-300 border-amber-600';

      const patInput = document.getElementById('arch-input-pattern');
      if (patInput) patInput.value = p.pattern;

      renderQuickTestStrings(p.sample_tests || []);
      compileArchitect();
    });
    container.appendChild(chip);
  });

  if (architectPresets.length > 0) {
    renderQuickTestStrings(architectPresets[0].sample_tests || []);
  }
}

function renderQuickTestStrings(samples) {
  const container = document.getElementById('arch-quick-strings');
  if (!container) return;
  container.innerHTML = '';

  samples.forEach(s => {
    const chip = document.createElement('button');
    chip.className = 'px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-slate-300 hover:border-cyan-400 hover:text-cyan-300 transition text-[11px] font-mono';
    chip.textContent = s === "" ? 'ε (empty)' : s;
    chip.addEventListener('click', () => {
      sfxClick();
      const strInput = document.getElementById('arch-sim-string');
      if (strInput) {
        strInput.value = s;
        simulateArchitectString(false);
      }
    });
    container.appendChild(chip);
  });
}

async function compileArchitect() {
  const spin = document.getElementById('spin-arch');
  if (spin) spin.classList.remove('hidden');

  try {
    const isCustom = !document.getElementById('arch-box-custom').classList.contains('hidden');
    let payload = {};
    if (isCustom) {
      payload = { custom_text: document.getElementById('arch-input-custom-text').value };
    } else {
      payload = { pattern: document.getElementById('arch-input-pattern').value };
    }

    const res = await fetch('/api/architect/compile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to compile automata');
    }

    currentArchitectData = await res.json();
    sfxDeploy();

    const tel = currentArchitectData.telemetry || {};
    const elEps = document.getElementById('arch-pipe-eps');
    const elNfa = document.getElementById('arch-pipe-nfa');
    const elDfa = document.getElementById('arch-pipe-dfa');
    const elMin = document.getElementById('arch-pipe-min');

    if (elEps) elEps.textContent = `${tel.eps_nfa_states ?? '--'} states (${tel.eps_nfa_epsilon_count ?? 0} ε-edges)`;
    if (elNfa) elNfa.textContent = `${tel.nfa_states ?? '--'} states`;
    if (elDfa) elDfa.textContent = `${tel.dfa_states ?? '--'} states`;
    if (elMin) elMin.textContent = `${tel.min_dfa_states ?? '--'} states`;

    switchArchitectRepresentation(activeArchitectMode);
  } catch (err) {
    console.error("Compile error:", err);
    sfxReject();
    alert(`Architect Error: ${err.message}`);
  } finally {
    if (spin) spin.classList.add('hidden');
  }
}

function switchArchitectRepresentation(mode) {
  if (!currentArchitectData || !currentArchitectData[mode]) return;
  activeArchitectMode = mode;
  sfxClick();

  const tabBtns = document.querySelectorAll('.arch-tab-btn');
  tabBtns.forEach(btn => {
    if (btn.getAttribute('data-mode') === mode) {
      btn.className = 'arch-tab-btn active px-3 py-1.5 text-xs font-mono font-bold rounded-lg bg-amber-950/80 text-amber-300 border border-amber-600/60 transition';
    } else {
      btn.className = 'arch-tab-btn px-3 py-1.5 text-xs font-mono font-semibold rounded-lg text-slate-400 hover:text-slate-200 transition';
    }
  });

  const machine = currentArchitectData[mode];
  const dict = machine.dict || {};

  const badgeEl = document.getElementById('arch-active-badge');
  const titleEl = document.getElementById('arch-canvas-title');
  const statesEl = document.getElementById('arch-stat-states');
  const transEl = document.getElementById('arch-stat-transitions');
  const alphaEl = document.getElementById('arch-stat-alphabet');
  const detEl = document.getElementById('arch-stat-determinism');

  if (badgeEl) badgeEl.textContent = mode.replace('_', '-').toUpperCase();
  if (titleEl) titleEl.textContent = `Representation: ${machine.name}`;
  if (statesEl) statesEl.textContent = machine.states_count;
  if (transEl) transEl.textContent = machine.transitions_count;
  if (alphaEl) alphaEl.textContent = (dict.alphabet || []).join(', ') || 'Σ';

  if (detEl) {
    if (machine.is_deterministic) {
      detEl.textContent = 'Deterministic';
      detEl.className = 'text-xs text-emerald-400 font-bold';
    } else {
      detEl.textContent = machine.has_epsilon ? 'Non-deterministic (ε-NFA)' : 'Non-deterministic (NFA)';
      detEl.className = 'text-xs text-amber-400 font-bold';
    }
  }

  if (cyArchitect && machine.cytoscape) {
    cyArchitect.elements().remove();
    cyArchitect.add(machine.cytoscape);
    const layoutName = document.getElementById('arch-layout-select').value || 'cose';
    applyLayout(cyArchitect, layoutName);
  }

  const verdictEl = document.getElementById('arch-sim-verdict');
  if (verdictEl) {
    verdictEl.textContent = `READY (${mode.replace('_', '-').toUpperCase()})`;
    verdictEl.className = 'px-3 py-1 rounded-full text-xs font-mono font-bold bg-slate-900 text-slate-400 border border-slate-800';
  }
}

async function simulateArchitectString(isStep = false) {
  if (!currentArchitectData) return;
  const strInput = document.getElementById('arch-sim-string');
  const testStr = strInput ? strInput.value : '';

  try {
    const isCustom = !document.getElementById('arch-box-custom').classList.contains('hidden');
    let payload = {
      machine_type: activeArchitectMode,
      string: testStr,
    };
    if (isCustom) {
      payload.custom_text = document.getElementById('arch-input-custom-text').value;
    } else {
      payload.pattern = document.getElementById('arch-input-pattern').value;
    }

    const res = await fetch('/api/architect/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Simulation failed');
    }

    currentArchitectSimResult = await res.json();
    const verdictEl = document.getElementById('arch-sim-verdict');
    const stepsBox = document.getElementById('arch-sim-steps-box');

    if (currentArchitectSimResult.accepted) {
      sfxAccept();
      if (verdictEl) {
        verdictEl.textContent = 'VERDICT: ACCEPTED ✔';
        verdictEl.className = 'px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500 shadow-md shadow-emerald-500/20';
      }
    } else {
      sfxReject();
      if (verdictEl) {
        verdictEl.textContent = 'VERDICT: REJECTED ✘';
        verdictEl.className = 'px-3 py-1 rounded-full text-xs font-mono font-bold bg-rose-950 text-rose-300 border border-rose-500 shadow-md shadow-rose-500/20';
      }
    }

    const steps = currentArchitectSimResult.steps || [];
    if (stepsBox) {
      stepsBox.innerHTML = '';
      steps.forEach(st => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between py-1 border-b border-slate-900';
        const symStr = st.symbol === null ? 'INIT (ε-closure)' : `Symbol '${st.symbol}'`;
        const actStr = (st.active_states || []).join(', ');
        row.innerHTML = `
          <span class="text-slate-400">Step ${st.step}: <span class="text-cyan-300 font-bold">${symStr}</span></span>
          <span class="text-amber-300 font-bold">{ ${actStr} }</span>
        `;
        stepsBox.appendChild(row);
      });
    }

    if (cyArchitect && steps.length > 0) {
      cyArchitect.nodes().removeClass('active-set highlighted');
      const finalStep = steps[steps.length - 1];
      const activeIds = finalStep.active_states || [];
      activeIds.forEach(id => {
        const node = cyArchitect.getElementById(id);
        if (node) {
          node.addClass(currentArchitectSimResult.is_nfa ? 'active-set' : 'highlighted');
        }
      });
    }
  } catch (err) {
    console.error("Simulation error:", err);
    sfxReject();
    alert(`Simulation Error: ${err.message}`);
  }
}
