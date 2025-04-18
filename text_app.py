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
    A = -N * VN + V[1:].sum()
    B = -V[1:].sum() + N * V0
    C3 = VN * (V0 - VN) * A / B if (V0 != VN and B != 0) else 0
    C3_norm = C3 / (V0**2) if V0 != 0 else 0

    return V, V0, VN, A, B, C3, C3_norm

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
**C = (A/B) × V(N) × (V(0) − V(N))**  
Measured in **bytes²**, it combines:
- Emergence of structure (A/B)
- Final compression size (V(N))
- Compression gain (V(0) − V(N))

We also provide a **normalized version** (`Cₙₒᵣₘ`) to compare across texts of different lengths.
""")

text_input = st.text_area("Enter or paste your text here:", height=300)

steps = st.slider("Number of corruption levels", 5, 41, 21, step=2)
trials = st.slider("Trials per corruption level", 1, 50, 30)

if text_input and len(text_input) >= 20:
    with st.spinner("Analyzing complexity..."):
        V, V0, VN, A, B, C3, C3_norm = estimate_text_complexity(text_input, steps=steps, trials=trials)

    st.markdown(f"**A:** {A:.2f} bytes &nbsp;&nbsp; **B:** {B:.2f} bytes &nbsp;&nbsp; **A/B:** {A/B:.2f}")
    st.markdown(f"""
**Complexity (C)**: `{C3:.2f}` bytes²  
**Normalized Complexity (Cₙₒᵣₘ)**: `{C3_norm:.6f}` (unitless, relative)
""")
    st.pyplot(plot_text_complexity(V, V0, VN, A, B))

    st.header("Preview Text at Selected Noise Level")
    noise_pct = st.slider("Select noise level (%)", 0, 100, 100, step=5)
    num_corrupt = int((noise_pct / 100) * len(text_input))

    if noise_pct > 0:
        preview = corrupt_text(text_input, num_corrupt)
        st.text_area(f"Corrupted Text ({noise_pct}% noise)", preview, height=300)
    else:
        st.text_area("Original Text (0% noise)", text_input, height=300)
else:
    st.info("Enter at least 20 characters of text to begin analysis.")
