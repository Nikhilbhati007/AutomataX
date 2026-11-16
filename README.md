# Automata Detective
**Problem 8: Learning and Visualizing DFA/NFA Models from Training Data**

Automata Detective is an interactive grammatical inference platform that learns minimal Deterministic Finite Automata (DFAs) from labeled positive and negative training strings, rigorously benchmarks algorithm performance across sample sizes and label noise, and visualizes both the learned automata and the state-merging process in real time.

---

## Architecture Overview

```
                      +---------------------------------------+
                      |       Input Strings / Generator       |
                      |   (Uniform, Stratified, Walk, Char)   |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |      Prefix Tree Acceptor (PTA)       |
                      |   (Canonical Shortlex State Order)    |
                      +-------------------+-------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                        v                                   v
             +--------------------+               +--------------------+
             |   RPNI Algorithm   |               |   EDSM Algorithm   |
             | (Canonical Merges) |               | (Evidence Scoring) |
             +----------+---------+               +---------+----------+
                        |                                   |
                        +-----------------+-----------------+
                                          |
                                          v
                      +---------------------------------------+
                      |     Automata Engine & Verification    |
                      |   • Hopcroft Minimization (O(n log n))|
                      |   • Equivalence Checking + Counterex. |
                      |   • Angluin's L* Active Learning Table|
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |       Interactive Web Dashboard       |
                      |   • Cytoscape.js Graph Canvas         |
                      |   • Token Path Simulation Animation   |
                      |   • PTA Collapse Scrubber (Replay)    |
                      |   • Reference Diff & Counterexamples  |
                      |   • Chart.js Learning & Noise Plots   |
                      +---------------------------------------+
```

---

## Repository Layout

* **`core/`** — Formal automata representations:
  * `dfa.py`: Complete and partial DFA simulation with step-by-step execution path tracking.
  * `nfa.py`: NFA with $\varepsilon$-transitions and set-of-states simulation.
  * `algorithms.py`: Subset construction ($NFA \to DFA$), Hopcroft partition-refinement minimization, and product-automaton BFS equivalence checking with shortest counterexamples.
  * `languages.py` & `reference_machines.py`: Benchmark languages across $\{0, 1\}$ and $\{a, b\}$.
* **`data/`** — Data synthesis:
  * `regex.py`: Thompson NFA regex compiler.
  * `generator.py`: Stratified, uniform, and random-walk sampling; label noise flips; disjoint train/test splitters; and minimal DFA characteristic sample synthesis.
* **`learn/`** — Grammatical inference algorithms:
  * `pta.py`: Deterministic shortlex Prefix Tree Acceptor with fast union-find state folding.
  * `rpni.py`: Regular Positive and Negative Inference (Oncina & García).
  * `edsm.py`: Evidence-Driven State Merging (Lang, Pearlmutter, Price / Abbadingo winner).
  * `lstar.py`: Angluin's $L^*$ active learning observation table with closedness/consistency enforcement and equivalence counterexample decomposition.
* **`experiments/`** — Empirical benchmark laboratory:
  * `metrics.py`: Accuracy, F1, state counts, and equivalence checking.
  * `benchmarks.py`: Multi-seed learning curves, noise sensitivity studies, and diversity vs. quantity experiments.
  * `baselines.py`: Pure-Python CART Decision Tree baseline & active learning vs. random sampling studies.
  * `clustering.py`: DFA end-state partitioning and n-gram K-means clustering.
* **`web/`** — Full-stack interface:
  * `api.py`: FastAPI server exposing endpoints for generation, learning, simulation, diff comparison, and experiments.
  * `static/`: Modern Tailwind CSS + Cytoscape.js + Chart.js single-page application.
* **`run.py`** — Single-command web server launcher.

---

## Quickstart

### 1. Launch the Web Application

```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Launch the interactive server & open browser
python run.py
```
Open **`http://127.0.0.1:8000`** in your browser.

### 2. Run the Test Suite

```powershell
.\.venv\Scripts\pytest.exe -v
```
All **96 unit and integration tests** verify correct behavior across the automata engine, learners, benchmarks, and API.

---

## 3-Minute Live Presentation Script

Use the **"Story Presets"** dropdown in the top header of the web app to demonstrate the platform in under 3 minutes:

### Story 1: "Too Few Examples" (30 seconds)
1. Select **"Story 1: Too Few Examples"** from the top preset dropdown.
2. Click **Run Inference**.
3. **What to show:** With only 4 training strings (`ab` [+], `aab` [+], `a` [-], `b` [-]), the learner constructs an incomplete hypothesis. 
4. Switch to the **Reference Diff** tab to highlight the red counterexample string where the learned machine disagrees with the true language.

### Story 2: "Diverse Examples Self-Correct" (45 seconds)
1. Select **"Story 2: Diverse Examples Self-Correct"**.
2. Click **Run Inference**.
3. **What to show:** Using a compact **characteristic sample** (shortlex access prefixes + pairwise distinguishing suffixes), the learned machine self-corrects and achieves **100% exact equivalence** with the true minimal 3-state DFA.
4. Switch to the **Learning Replay Scrubber** tab and drag the timeline slider to show the PTA collapsing step-by-step as merges are evaluated.

### Story 3: "Noise Tolerance Showdown" (45 seconds)
1. Select **"Story 3: Noise Tolerance Showdown"**.
2. Switch to **Benchmark Labs & Charts** and click **Run Noise Study**.
3. **What to show:** Compare RPNI against EDSM under 0%, 5%, 10%, and 20% label noise. Point out how RPNI overfits and collapses due to false-negative constraints, whereas EDSM's evidence heuristic degrades gracefully.

### Story 4: "Active Learning with Angluin's L*" (60 seconds)
1. Select **"Story 4: Active Learning vs Random"**.
2. Click **Run Inference** (or **Run Active Learning** in Labs).
3. **What to show:** Angluin's $L^*$ queries membership and equivalence oracles directly, isolating boundary transitions and converging on the exact minimal 8-state DFA for the exponential-blowup language (*3rd symbol from end is 'a'*) in a fraction of the sample budget.
4. Type an unseen test string into the **String Simulation** tab and click **Animate Path** to watch the glowing token navigate through the states in real time.
