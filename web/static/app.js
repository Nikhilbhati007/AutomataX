/* Automata Detective — Interactive Frontend Engine */

let currentLanguages = [];
let currentPresets = [];
let currentDataset = [];
let currentLearnedDFA = null;
let currentAlgorithm = "edsm";
let currentSteps = [];
let currentReplayIndex = 0;
let isReplayPlaying = false;
let replayTimer = null;

let cyLearned = null;
let cySim = null;
let cyReplay = null;
let cyReference = null;

let chartLearningCurve = null;
let chartNoiseStudy = null;
let chartActiveStudy = null;

// ---------------------------------------------------------------------------
// Cytoscape Visual Styles
// ---------------------------------------------------------------------------

const CY_STYLE = [
  {
    selector: 'node',
    style: {
      'content': 'data(label)',
      'text-valign': 'center',
      'text-halign': 'center',
      'background-color': '#1e293b',
      'color': '#f8fafc',
      'font-size': '12px',
      'font-family': 'JetBrains Mono, monospace',
      'font-weight': 'bold',
      'width': 44,
      'height': 44,
      'border-width': 2,
      'border-color': '#475569',
      'transition-property': 'background-color, border-color, width, height, border-width',
      'transition-duration': '0.2s',
    }
  },
  {
    selector: 'node.start',
    style: {
      'border-color': '#06b6d4',
      'border-width': 3,
      'background-color': '#0f766e',
      'color': '#ffffff',
    }
  },
  {
    selector: 'node.accept',
    style: {
      'border-color': '#10b981',
      'border-width': 4,
      'background-color': '#064e3b',
      'color': '#a7f3d0',
    }
  },
  {
    selector: 'node.start.accept',
    style: {
      'border-color': '#06b6d4',
      'border-width': 4,
      'background-color': '#047857',
    }
  },
  {
    selector: 'node.highlighted',
    style: {
      'background-color': '#06b6d4',
      'border-color': '#38bdf8',
      'border-width': 5,
      'color': '#0b0f19',
      'width': 50,
      'height': 50,
    }
  },
  {
    selector: 'edge',
    style: {
      'content': 'data(label)',
      'font-size': '11px',
      'font-family': 'JetBrains Mono, monospace',
      'color': '#94a3b8',
      'text-background-color': '#0b0f19',
      'text-background-opacity': 0.85,
      'text-background-padding': '3px',
      'curve-style': 'bezier',
      'control-point-step-size': 45,
      'target-arrow-shape': 'triangle',
      'target-arrow-color': '#64748b',
      'line-color': '#475569',
      'width': 2,
      'arrow-scale': 1.1,
    }
  },
  {
    selector: 'edge.highlighted',
    style: {
      'line-color': '#06b6d4',
      'target-arrow-color': '#06b6d4',
      'width': 4,
      'color': '#38bdf8',
    }
  }
];

function initCy(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return null;
  return cytoscape({
    container: container,
    elements: [],
    style: CY_STYLE,
    layout: { name: 'circle' },
    userZoomingEnabled: true,
    userPanningEnabled: true,
    boxSelectionEnabled: false,
  });
}

function renderElements(cy, elements) {
  if (!cy) return;
  cy.elements().remove();
  cy.add(elements);
  const layout = cy.layout({
    name: 'cose',
    animate: false,
    randomize: false,
    fit: true,
    padding: 30,
    nodeRepulsion: 6500,
    idealEdgeLength: 60,
    edgeElasticity: 100,
  });
  layout.run();
}

// ---------------------------------------------------------------------------
// App Bootstrapping & API Calls
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
  cyLearned = initCy('cy-container');
  cySim = initCy('cy-sim-container');
  cyReplay = initCy('cy-replay-container');
  cyReference = initCy('cy-reference-container');

  setupTabs();
  setupEventListeners();
  await loadCatalogAndPresets();
  await generateData();
  await runInference();
});

function setupTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active', 'bg-slate-800', 'text-cyan-400', 'border', 'border-slate-700');
        t.classList.add('text-slate-400');
      });
      tab.classList.add('active', 'bg-slate-800', 'text-cyan-400', 'border', 'border-slate-700');
      tab.classList.remove('text-slate-400');

      panels.forEach(p => p.classList.add('hidden'));
      const targetId = tab.getAttribute('data-target');
      const targetPanel = document.getElementById(targetId);
      if (targetPanel) {
        targetPanel.classList.remove('hidden');
        // Resize Cytoscape canvas when switching tabs
        setTimeout(() => {
          if (targetId === 'tab-investigate' && cyLearned) cyLearned.resize().fit();
          if (targetId === 'tab-simulator' && cySim) cySim.resize().fit();
          if (targetId === 'tab-replay' && cyReplay) cyReplay.resize().fit();
          if (targetId === 'tab-compare' && cyReference) cyReference.resize().fit();
        }, 80);
      }
    });
  });
}

async function loadCatalogAndPresets() {
  try {
    const [langRes, presetRes] = await Promise.all([
      fetch('/api/languages').then(r => r.json()),
      fetch('/api/presets').then(r => r.json()),
    ]);

    currentLanguages = langRes.languages || [];
    currentPresets = presetRes.presets || [];

    // Populate Language dropdown
    const langSelect = document.getElementById('select-target-lang');
    langSelect.innerHTML = '';
    currentLanguages.forEach(l => {
      const opt = document.createElement('option');
      opt.value = l.id;
      opt.textContent = `${l.name} (${l.expected_min_dfa_states} min states)`;
      langSelect.appendChild(opt);
    });

    // Populate Presets dropdown
    const presetSelect = document.getElementById('preset-select');
    presetSelect.innerHTML = '<option value="">-- Load Presentation Preset --</option>';
    currentPresets.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.title;
      presetSelect.appendChild(opt);
    });

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
  });

  document.getElementById('btn-generate-data').addEventListener('click', generateData);

  // Algorithm selectors
  document.querySelectorAll('.algo-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.algo-btn').forEach(b => {
        b.classList.remove('active', 'border-cyan-500/80', 'bg-cyan-500/10', 'text-cyan-300');
        b.classList.add('border-slate-700', 'bg-slate-800/60', 'text-slate-300');
      });
      btn.classList.add('active', 'border-cyan-500/80', 'bg-cyan-500/10', 'text-cyan-300');
      btn.classList.remove('border-slate-700', 'bg-slate-800/60', 'text-slate-300');
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

  document.getElementById('btn-quick-run').addEventListener('click', runInference);

  // Presets load
  document.getElementById('preset-select').addEventListener('change', async (e) => {
    const presetId = e.target.value;
    if (!presetId) return;
    const preset = currentPresets.find(p => p.id === presetId);
    if (!preset) return;

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
  });

  // Fit view buttons
  document.getElementById('btn-fit-graph').addEventListener('click', () => {
    if (cyLearned) cyLearned.fit(30);
  });
  document.getElementById('btn-relayout-graph').addEventListener('click', () => {
    if (cyLearned) {
      cyLearned.layout({ name: 'cose', animate: true, padding: 30 }).run();
    }
  });

  // Simulator controls
  document.getElementById('btn-play-simulate').addEventListener('click', () => animateStringPath());
  document.getElementById('btn-step-simulate').addEventListener('click', () => stepStringPath());
  document.getElementById('btn-reset-simulate').addEventListener('click', () => resetSimulation());

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

  // Compare
  document.getElementById('btn-recompare').addEventListener('click', runComparison);

  // Experiments
  document.getElementById('btn-run-learning-curve').addEventListener('click', runLearningCurveExperiment);
  document.getElementById('btn-run-noise-study').addEventListener('click', runNoiseStudyExperiment);
  document.getElementById('btn-run-active-study').addEventListener('click', runActiveStudyExperiment);
}

// ---------------------------------------------------------------------------
// Dataset Generation
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
    renderTrainingExamples(data.examples || []);
  } catch (err) {
    console.error("Failed to generate data:", err);
  }
}

function renderTrainingExamples(examples) {
  currentDataset = examples;
  const list = document.getElementById('training-examples-list');
  list.innerHTML = '';

  let pos = 0, neg = 0;
  examples.forEach(ex => {
    if (ex.label) pos++; else neg++;
    const pill = document.createElement('div');
    pill.className = `flex items-center justify-between px-2.5 py-1 rounded border text-xs ${
      ex.label
        ? 'bg-emerald-950/40 border-emerald-800/80 text-emerald-300'
        : 'bg-rose-950/40 border-rose-800/80 text-rose-300'
    }`;
    const stringText = ex.string === '' ? 'ε (empty string)' : ex.string;
    pill.innerHTML = `
      <span>${stringText}</span>
      <span class="text-[10px] font-bold uppercase">${ex.label ? '+ POS' : '- NEG'}</span>
    `;
    list.appendChild(pill);
  });

  document.getElementById('train-count').textContent = examples.length;
  document.getElementById('pos-count').textContent = pos;
  document.getElementById('neg-count').textContent = neg;
}

// ---------------------------------------------------------------------------
// Inference Execution
// ---------------------------------------------------------------------------

async function runInference() {
  const langId = document.getElementById('select-target-lang').value;
  const btn = document.getElementById('btn-quick-run');
  btn.textContent = 'Learning...';
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

    // Render Main Canvas
    renderElements(cyLearned, data.cytoscape || []);
    document.getElementById('badge-states-count').textContent = `${data.dfa.states.length} states`;
    document.getElementById('inference-meta').textContent = `Merges: ${data.metadata.merges_accepted || 0} | Steps: ${currentSteps.length}`;

    // Mirror to Sim Canvas
    renderElements(cySim, data.cytoscape || []);

    // Setup Replay Scrubber
    setupReplayScrubber(currentSteps);

    // Run Comparison
    await runComparison();
  } catch (err) {
    console.error("Inference run error:", err);
  } finally {
    btn.textContent = 'Run Inference';
    btn.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// Path Simulation
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
  badge.className = 'px-4 py-1.5 rounded-full text-xs font-bold font-mono tracking-wider bg-slate-800 text-slate-400 border border-slate-700';
}

async function stepStringPath() {
  const str = document.getElementById('input-test-string').value.trim();
  if (!simPathData) {
    simPathData = await fetchSimulationData(str);
    simCurrentStep = 0;
  }

  const path = simPathData.path;
  if (simCurrentStep >= path.length) {
    return;
  }

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
    await new Promise(r => setTimeout(r, 450));
  }
  showVerdict(simPathData.accepted);
}

function renderPathTrace(path, activeIndex) {
  const display = document.getElementById('sim-path-display');
  display.innerHTML = '';
  path.forEach((state, idx) => {
    const span = document.createElement('span');
    span.className = `px-2 py-0.5 rounded text-xs ${
      idx === activeIndex
        ? 'bg-cyan-500 text-slate-950 font-bold token-active'
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
    badge.textContent = 'ACCEPTED';
    badge.className = 'px-4 py-1.5 rounded-full text-xs font-bold font-mono tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 shadow-lg shadow-emerald-500/20';
  } else {
    badge.textContent = 'REJECTED';
    badge.className = 'px-4 py-1.5 rounded-full text-xs font-bold font-mono tracking-wider bg-rose-500/20 text-rose-400 border border-rose-500/50 shadow-lg shadow-rose-500/20';
  }
}

// ---------------------------------------------------------------------------
// Learning Replay Scrubber
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

  // If this step contains Cytoscape graph snapshot, render it immediately
  if (step.cytoscape) {
    renderElements(cyReplay, step.cytoscape);
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
      } else {
        clearInterval(replayTimer);
        isReplayPlaying = false;
        btn.textContent = '▶ Auto-Play';
      }
    }, 600);
  }
}

// ---------------------------------------------------------------------------
// Reference Diff & Compare
// ---------------------------------------------------------------------------

async function runComparison() {
  if (!currentLearnedDFA) return;
  const langId = document.getElementById('select-target-lang').value;

  try {
    // 1. Fetch Reference DFA
    const refRes = await fetch(`/api/reference-dfa/${langId}`);
    const refData = await refRes.json();
    renderElements(cyReference, refData.cytoscape || []);
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
      verdictPill.className = 'inline-block px-3 py-1 rounded-full text-xs font-bold font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/50';
      cexEl.textContent = 'No counterexample: machine recognizes the identical regular language!';
    } else {
      verdictPill.textContent = 'NOT EQUIVALENT';
      verdictPill.className = 'inline-block px-3 py-1 rounded-full text-xs font-bold font-mono bg-rose-500/20 text-rose-400 border border-rose-500/50';
      cexEl.textContent = `Counterexample string: ${metrics.counterexample === '' ? 'ε (empty string)' : metrics.counterexample}`;
    }

    // Populate Disagreements List
    const disagList = document.getElementById('disagreements-list');
    disagList.innerHTML = '';
    const diffs = compData.disagreements || [];
    if (diffs.length === 0) {
      disagList.innerHTML = '<p class="text-emerald-400 italic">No disagreements on test sample.</p>';
    } else {
      diffs.forEach(d => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between px-2.5 py-1 bg-rose-950/30 border border-rose-900/60 rounded text-xs';
        const strLabel = d.string === '' ? 'ε' : d.string;
        row.innerHTML = `
          <span class="text-slate-200">${strLabel}</span>
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
            borderColor: '#06b6d4',
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            tension: 0.25,
            fill: true,
          },
          {
            label: 'RPNI Accuracy (%)',
            data: rpniAcc,
            borderColor: '#f43f5e',
            backgroundColor: 'rgba(244, 63, 94, 0.1)',
            tension: 0.25,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }, title: { display: true, text: 'Train Size', color: '#64748b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }, min: 50, max: 100, title: { display: true, text: 'Test Accuracy (%)', color: '#64748b' } }
        }
      }
    });
  } catch (err) {
    console.error("Learning curve error:", err);
  } finally {
    btn.textContent = 'Run Learning Curves';
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
            label: 'EDSM (Graceful)',
            data: edsmAcc,
            backgroundColor: 'rgba(6, 182, 212, 0.7)',
            borderColor: '#06b6d4',
            borderWidth: 1,
          },
          {
            label: 'RPNI (Collapse)',
            data: rpniAcc,
            backgroundColor: 'rgba(244, 63, 94, 0.7)',
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
          x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }, min: 50, max: 100 }
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
            label: 'Active (Uncertainty)',
            data: activeAcc,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            tension: 0.25,
            fill: true,
          },
          {
            label: 'Random Sampling',
            data: randomAcc,
            borderColor: '#64748b',
            backgroundColor: 'rgba(100, 116, 139, 0.1)',
            tension: 0.25,
            fill: true,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }, title: { display: true, text: 'Query Budget', color: '#64748b' } },
          y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' }, min: 50, max: 100 }
        }
      }
    });
  } catch (err) {
    console.error("Active study error:", err);
  } finally {
    btn.textContent = 'Run Active Learning';
    btn.disabled = false;
  }
}

