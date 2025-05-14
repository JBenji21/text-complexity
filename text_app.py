import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import zlib
import random
import string

# === Compression & Corruption Functions ===
def compress_size(text: str) -> int:
    return len(zlib.compress(text.encode('utf-8')))

def corrupt_text(text: str, num_corrupt: int) -> str:
    chars = list(text)
    indices = random.sample(range(len(text)), num_corrupt)
    for idx in indices:
        chars[idx] = random.choice(string.printable)
    return ''.join(chars)

def estimate_text_complexity(text: str, steps=21, trials=30):
    n = len(text)
    step_fracs = np.linspace(0.0, 1.0, steps)
    compressed_sizes = []

    for frac in step_fracs:
        keep = int(frac * n)
        corrupt = n - keep
        sizes = []
        for _ in range(trials):
            corrupted = corrupt_text(text, corrupt)
            sizes.append(compress_size(corrupted))
        compressed_sizes.append(np.mean(sizes))

    V = np.array(compressed_sizes)
    V0, VN = V[0], V[-1]
    N = steps - 1
    A = -(N+1) * VN + V.sum()
    B = -V.sum() + (N+1) * V0
    EF = A / B if B != 0 else 0
    AC = VN
    SS = (V0 - VN) / V0 if V0 != 0 else 0
    C = EF * AC * SS
    C_norm = C / (V0) if V0 != 0 else 0
    return V, V0, VN, A, B, EF, AC, SS, C, C_norm

def plot_text_complexity(V, V0, VN, A, B):
    N = len(V) - 1
    x = np.arange(N + 1)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, V, 'o-', label='V(i)', lw=2)
    ax.hlines(V0, 0, N, colors='gray', linestyles='--', label='V(0)')
    ax.hlines(VN, 0, N, colors='black', linestyles='--', label='V(N)')
    ax.fill_between(x, V, V0, where=V <= V0, color='orange', alpha=0.3, label=f'B = {B:.1f}')
    ax.fill_between(x, V, VN, where=V >= VN, color='skyblue', alpha=0.3, label=f'A = {A:.1f}')
    ax.plot(0, V0, 'ro'); ax.text(0, V0, ' V(0)', va='bottom', ha='left')
    ax.plot(N, VN, 'ro'); ax.text(N, VN, ' V(N)', va='bottom', ha='right')
    ax.set_title("Text V(i) with A & B areas")
    ax.set_xlabel("Step i → increasing order (less noise)")
    ax.set_ylabel("V(i) = compressed size (bytes)")
    ax.legend(loc='lower left')
    ax.grid(True)
    fig.tight_layout()
    return fig

# === Streamlit App ===
st.title("Text Complexity Analyzer")

st.markdown("""
This app calculates the **structural complexity** of a block of text using a novel compression-based method.

### 📌 How it works:
- Your text is progressively corrupted with random characters, from total noise (100%) to the original version (0% noise).
- At each step, we compress the corrupted version and record the file size.
- The resulting curve reveals how structured and interdependent your text is.

### 📌 Complexity Metric (C):
**C = (A/B) × V(N) × ((V(0) − V(N))/V(0))**  
Measured in **bytes**, it combines:
- Emergence of structure (A/B)
- Final compression size (V(N))
- Compression gain (V(0) − V(N))/V(0)

We also provide a **normalized version** (`Cₙₒᵣₘ`) to compare across texts of different lengths.
""")

# --- Input section ---
uploaded_file = st.file_uploader(
    "Upload a text file (.txt or .md)", type=["txt", "md"]
)

file_text = ""
if uploaded_file is not None:
    raw = uploaded_file.read()
    # Try UTF‑8 first, fall back to latin‑1 so exotic chars don’t crash:
    try:
        file_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        file_text = raw.decode("latin1", errors="ignore")

text_input = st.text_area(
    "Enter or edit your text here:",
    value=file_text,          # pre‑populate if a file was uploaded
    height=300
)

# Prefer whatever is in the box; fall back to the uploaded file’s text
text_to_analyze = text_input.strip() or file_text

steps = st.slider("Number of corruption levels", 5, 41, 21, step=2)
trials = st.slider("Trials per corruption level", 1, 50, 30)

if len(text_to_analyze) >= 20:
    with st.spinner("Analyzing complexity..."):
        V, V0, VN, A, B, EF, AC, SS, C, C_norm = estimate_text_complexity(text_to_analyze, steps=steps, trials=trials)

    st.markdown(f"""
**Baseline size (V₀)**: `{V0:.1f}` bytes  
**Structured size (Vₙ)**: `{VN:.1f}` bytes  

**Emergence Factor (A/B)**: `{EF:.2f}`  
**Absolute Complexity (Vₙ)**: `{AC:.1f}` bytes  
**Structure Spread (SS)**: `{SS:.4f}`

---

**Emergent Structural Complexity (C):** `{C:.2f}` bytes,  
**Normalized Complexity (Cₙₒᵣₘ)**: `{C_norm:.6f}` (unitless, relative)
""")
    st.pyplot(plot_text_complexity(V, V0, VN, A, B))

    st.header("Preview Text at Selected Noise Level")
    noise_pct = st.slider("Select noise level (%)", 100, 0, 100, step=5)
    num_corrupt = int((noise_pct / 100) * len(text_to_analyze))

    if noise_pct > 0:
        preview = corrupt_text(text_to_analyze, num_corrupt)
        st.text_area(f"Corrupted Text ({noise_pct}% noise)", preview, height=300)
    else:
        st.text_area("Original Text (0% noise)", text_to_analyze, height=300)
else:
    st.info("Enter at least 20 characters of text to begin analysis.")
