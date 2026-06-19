# LightningLM — Complete Explanation Guide

> **Who this is for:** Beginners who want to understand how large language models are actually built from scratch, including training a 120B parameter model on a single 8-GPU node.

---

## Table of Contents

1. [What is LightningLM?](#what-is-lightninglm)
2. [The Big Picture — Four Growth Stages](#big-picture)
3. [Key Innovations Explained](#key-innovations)
4. [The Architecture — Mixture of Experts](#moe-architecture)
5. [The Training Pipeline](#training-pipeline)
6. [Special Components](#special-components)
7. [Repository Structure Walkthrough](#repository-structure)
8. [How to Run It](#how-to-run)
9. [Cheatsheet](#cheatsheet)
10. [Summary and Conclusion](#summary-and-conclusion)

---

## What is LightningLM?

LightningLM is a **complete training pipeline** for building and training a 120-billion parameter language model from scratch — on just **8 GPUs**.

This is significant because:
- GPT-4 was trained on thousands of GPUs
- LightningLM achieves production-scale results with dramatically fewer resources
- It demonstrates that careful engineering can substitute for raw compute

The project released the 120B model publicly on Hugging Face: **LightningLM-0.1V-120B-MoE**

### The Three Core Principles

The paper and code are organized around three disciplines:

```
1. REVERSIBILITY
   Every operation can be undone. If training goes wrong, you can roll back.
   
2. STATE-PRESERVING GROWTH
   When you grow a 2B model to 5B, the new model starts exactly where
   the smaller model left off. No wasted training.
   
3. SINGLE-NODE ECONOMICS
   Do more with less. Optimize for 8 GPUs, not 8,000.
```

---

## The Big Picture: Four Growth Stages

Instead of training a 120B model from scratch (which would take enormous resources), LightningLM grows incrementally:

```
Stage 1: 2B Dense Model
├── Architecture: Standard dense transformer
├── Training: Learn the basics of language
└── Cost: Relatively cheap to train

Stage 2: 5B Mixture of Experts (MoE)
├── Architecture: Grow from 2B using "partition" strategy
├── Training: Continue from 2B checkpoint
└── Key: Add expert routing mechanism

Stage 3: 9B Mixture of Experts (MoE)
├── Architecture: Grow from 5B using "depth map" strategy
├── Training: Continue from 5B checkpoint
└── Key: Add depth (more layers)

Stage 4: 120B TQP (TurboQuant-PreTraining)
├── Architecture: 460 routed experts, 5.93B active per token
├── Training: Special quantization-aware training
└── Key: Scale to 120B while training on 8 GPUs
```

### Why Grow Incrementally?

**Traditional approach:** Train 120B from scratch → expensive, risky (you don't know if your architecture works until the end)

**LightningLM approach:** 
- Validate architecture at 2B (cheap, fast)
- If it works, grow to 5B (still cheap)
- Each stage builds on proven foundations
- Failure at any stage = only lose that stage's compute

---

## Key Innovations Explained

### Innovation 1: BrahmicTokenizer-131K

Most LLMs use tokenizers with ~32K-100K vocabulary. LightningLM uses a 131K vocabulary that specifically covers:
- English text
- All major Brahmic scripts (Hindi, Bengali, Tamil, Telugu, Malayalam, Kannada, Sinhala, Tibetan, etc.)

**Why does this matter?**
```
Standard tokenizer on Hindi text:
"नमस्ते दुनिया" → [OMG, 12345, 67890, 11111, 99999, ...] (many tokens, inefficient)

BrahmicTokenizer on Hindi text:
"नमस्ते दुनिया" → [नमस्ते, दुनिया] (2 tokens, efficient)
```

Multilingual tokenizers make models better at non-English languages because they don't have to spend many tokens on each word.

### Innovation 2: Kronecker Embeddings

The standard embedding table for a 131K vocabulary at 4096 dimensions = 537 million parameters. That's just for converting tokens to vectors!

**Kronecker embeddings** replace this with a mathematical construction:

```
Standard: 131,072 × 4,096 = 537M parameters

Kronecker: Uses tensor products of smaller matrices
          ≈ 33.6M parameters
          87% reduction in parameter count!
```

The key insight: The embedding matrix has structure that can be exploited. Instead of learning 537M independent numbers, you learn patterns that tile across the matrix.

### Innovation 3: TurboQuant-PreTraining (TQP)

Normal training uses 16-bit (bfloat16) precision throughout.

TQP training uses quantized (4-bit or 8-bit) weights during training, which:
- Reduces memory usage dramatically
- Allows 120B parameters to fit in 8×80GB = 640GB total VRAM
- Maintains training quality through careful gradient handling

This is different from post-training quantization (like GPTQ). TQP quantizes **during** training, not after.

### Innovation 4: State-Preserving Growth

When growing from 2B to 5B, a naive approach would be:
- Initialize 5B model randomly
- Start training from scratch
- 2B model's training was wasted

LightningLM's approach:
- Take the trained 2B model
- Use mathematical strategies to initialize the 5B model
  - "Partition" strategy: split each layer into multiple parts
  - New parts start as copies of existing parts
- Start 5B training — model immediately has the 2B model's knowledge
- Training continues where it left off

```bash
# Grow 2B to 5B preserving state
python3 -m lightninglm.growth.dense_to_moe \
  --src results/2b/checkpoint.pt \
  --dst results/5b/init_from_2b.pt \
  --strategy partition
```

---

## The Architecture: Mixture of Experts

### What is a Dense Model?

A standard transformer (like BERT, Llama-2):
- Every layer has one feed-forward network (FFN)
- Every token passes through ALL parameters
- 7B parameters → 7B parameters activate per token

### What is a Mixture of Experts (MoE)?

Instead of one FFN per layer, have **many expert FFNs** per layer. A router decides which experts to use for each token.

```
Dense 7B:
  Token → Attention → Single FFN (7B params) → Output

MoE with 8 experts, 2 active:
  Token → Attention → Router → Expert 2, Expert 7 → Output
                              (only 2 of 8 experts used)
```

### LightningLM 120B MoE Specifics

| Attribute | Value |
|-----------|-------|
| Total parameters | 118.67 billion |
| Active parameters per token | 5.93 billion |
| Total experts | 460 routed experts |
| Active experts per token | 12 |
| Architecture | Top-12 of 460 routing |

The 460 experts means:
- 460 different "specialist" feed-forward networks
- Each token uses only 12 of the 460 specialists
- The model has 120B parameters but reasons like a 6B model per token
- Very high quality (120B total) + reasonable inference cost (6B active)

### How Expert Routing Works

```python
# Conceptual router implementation
def router_forward(hidden_state, num_experts=460, top_k=12):
    # Compute routing scores for each expert
    logits = router_linear(hidden_state)  # shape: [batch, seq, num_experts]
    
    # Select top-k experts
    top_k_weights, top_k_indices = torch.topk(logits, k=top_k, dim=-1)
    
    # Normalize weights
    weights = torch.softmax(top_k_weights, dim=-1)
    
    # Compute weighted sum of expert outputs
    output = sum(
        weights[:,:,i] * experts[top_k_indices[:,:,i]](hidden_state)
        for i in range(top_k)
    )
    return output
```

### Load Balancing

A potential problem: if all tokens always route to the same 12 experts, the other 448 experts learn nothing.

**Solution:** Add a load balancing loss that encourages uniform use of all experts:

```python
# Load balance loss
auxiliary_loss = load_balance_coefficient * (
    num_experts * sum(fraction_of_tokens_routed_to_expert_i² for each i)
)
# This penalizes any expert getting much more traffic than average
```

---

## The Training Pipeline

### Data Pipeline

The training data is organized into "curriculum shards":

```
D1: Basic language (low quality but massive quantity)
D2: Medium quality filtered web text
D3: High quality text (books, papers, code)
D4: Expert data (mathematics, science)
AON: "Always On" guaranteed pool (high quality, always included)
```

The curriculum shifts over training stages:
- Early training: more D1, D2 (build basic language understanding)
- Later training: more D3, D4, AON (improve quality)

### Shard Manifests

Instead of loading all data into memory, the pipeline uses **manifests** — files that describe what shards exist and where:

```yaml
# Example manifest entry
- name: "wikipedia_en_shard_001"
  path: "/data/wiki/en/shard_001.bin"
  tokens: 4294967296  # 4B tokens
  pool: "D3"
```

The training code reads the manifest to know what data to load.

### DeepSpeed ZeRO

Training 120B parameters on 8 GPUs requires distributing everything across GPUs:

**ZeRO Stage 1:** Partition optimizer states across GPUs
- Each GPU stores 1/8 of the optimizer states
- 8× memory savings on optimizer states

**ZeRO Stage 3:** Partition model parameters, gradients, AND optimizer states
- Each GPU stores only 1/8 of everything
- Maximum memory efficiency
- Used for the 120B TQP stage

```yaml
# configs/zero3_120b.yaml (DeepSpeed config)
{
  "zero_optimization": {
    "stage": 3,
    "offload_optimizer": {
      "device": "cpu",  # Offload to CPU RAM when GPU runs out
    },
    "allgather_partitions": true,
    "reduce_scatter": true,
  }
}
```

### The OPUS Training Loop

OPUS (likely stands for an internal acronym) is the core training loop, implementing:
- Gradient accumulation
- Mixed precision training
- Checkpoint saving and resumption
- Loss tracking and logging

```bash
# Start 2B training on 8 GPUs
NUM_GPUS=8 bash scripts/run_2b_stage.sh
```

---

## Special Components

### The `lightninglm` Python Package Structure

```
lightninglm/
├── models/          # Model architecture definitions
│   ├── dense.py     # 2B dense transformer
│   └── moe.py       # MoE transformer (5B, 9B, 120B)
├── training/        # Training loops (OPUS)
├── data/            # Data loading and batching
├── growth/          # Dense-to-MoE growth utilities
│   ├── dense_to_moe.py  # Stage 1→2 growth
│   └── depth_map.py     # Stage 2→3 growth
├── kernels/         # Custom CUDA kernels for efficiency
└── tqp/             # TurboQuant-PreTraining implementation
```

### Custom CUDA Kernels

The `kernels/` directory contains hand-written CUDA code for operations that are too slow in standard PyTorch:

- **Custom attention kernels:** Faster attention computation
- **Expert routing kernels:** Efficient top-k selection across 460 experts
- **Quantized compute kernels:** 4-bit matrix multiplication for TQP

### The `doctor.py` Script

Before running any training, `scripts/doctor.py` checks everything is set up correctly:

```bash
python3 scripts/doctor.py
```

Checks:
- GPU availability and VRAM
- Python version
- All dependencies installed
- Config file validity
- Disk space for checkpoints
- Network connectivity to data shards

---

## Repository Structure Walkthrough

```
LLM-staging/ (= LightningLM repository)
├── lightninglm/          # The main Python package
│   ├── models/           # Architecture (dense transformer, MoE transformer)
│   ├── growth/           # Model growth utilities
│   ├── training/         # OPUS training loop
│   ├── data/             # Data loading
│   ├── kernels/          # Custom CUDA kernels
│   └── tqp/              # TurboQuant-PreTraining
├── configs/              # Training configurations per stage
│   ├── train_2b.yaml
│   ├── train_5b_moe.yaml
│   ├── train_9b_moe.yaml
│   └── train_120b_tqp.yaml
├── deepspeed/            # DeepSpeed ZeRO configurations
│   ├── zero1_small_models.json
│   └── zero3_120b.json
├── scripts/              # Shell scripts and Python utilities
│   ├── setup_stable.sh   # Install everything
│   ├── doctor.py         # Health check
│   ├── run_2b_stage.sh   # Launch 2B training
│   ├── run_5b_stage.sh   # Launch 5B training
│   ├── run_9b_stage.sh   # Launch 9B training
│   ├── run_120b_tqp.sh   # Launch 120B TQP training
│   └── build_120b_init.py # Initialize 120B from 9B checkpoint
├── manifests/            # Curriculum shard manifests
│   ├── d1_bulk.yaml
│   ├── d2_bulk.yaml
│   ├── d3_bulk.yaml
│   ├── d4_bulk.yaml
│   └── aon_pool.yaml
├── tokenizer/            # BrahmicTokenizer-131K
├── docs/                 # Detailed documentation
│   ├── cookbook.md       # Full step-by-step guide
│   ├── data_pipeline.md  # How to prepare training data
│   ├── tokenizer_pipeline.md
│   └── runtime_hotconfig.md  # Adjust training while running
├── tests/                # Test suite
└── requirements/         # Pinned Python dependencies
```

---

## How to Run It

### Prerequisites

- 8× NVIDIA H100 or A100 80GB GPUs (for 120B training)
- 1-2× A100/H100 (for 2B-9B stages)
- Ubuntu 20.04+ / Python 3.11+
- ~5 TB disk space for checkpoints and data

### Step 1: Setup

```bash
bash scripts/setup_stable.sh
python3 scripts/doctor.py  # Verify everything works
```

### Step 2: Train the 2B seed model

```bash
NUM_GPUS=8 bash scripts/run_2b_stage.sh
# Wait several days...
# Checkpoint saved to results/2b/checkpoint.pt
```

### Step 3: Grow to 5B MoE

```bash
python3 -m lightninglm.growth.dense_to_moe \
  --src results/2b/checkpoint.pt \
  --dst results/5b/init_from_2b.pt \
  --strategy partition

NUM_GPUS=8 bash scripts/run_5b_stage.sh
```

### Step 4: Grow to 9B

```bash
python3 -m lightninglm.growth.depth_map \
  --src results/5b/checkpoint.pt \
  --dst results/9b/init_from_5b.pt \
  --mapping lightninglm_5b_to_9b

NUM_GPUS=8 bash scripts/run_9b_stage.sh
```

### Step 5: Scale to 120B

```bash
python3 scripts/build_120b_init.py \
  --src results/9b/checkpoint.pt \
  --dst results/120b/120b_init.pt \
  --config configs/train_120b_tqp.yaml \
  --ratio 0.5 \
  --router_sigma 0.05 \
  --seed 1337

NUM_GPUS=8 bash scripts/run_120b_tqp.sh
```

---

## Cheatsheet

### The 4-Stage Growth Plan

| Stage | From | To | Method | GPU Memory |
|-------|------|-----|--------|-----------|
| 1 | Scratch | 2B dense | Standard pre-training | 2× A100 |
| 2 | 2B dense | 5B MoE | `partition` growth | 4× A100 |
| 3 | 5B MoE | 9B MoE | `depth_map` growth | 4× A100 |
| 4 | 9B MoE | 120B MoE | TQP + expert expansion | 8× H100 |

### Key Hyperparameters for Each Stage

| Stage | Batch Size | Learning Rate | Context Length |
|-------|-----------|---------------|----------------|
| 2B | 1M tokens | 3e-4 | 4096 |
| 5B | 2M tokens | 2e-4 | 4096 |
| 9B | 4M tokens | 1e-4 | 8192 |
| 120B | 8M tokens | 5e-5 | 8192 |

### Concepts Quick Reference

| Term | Meaning |
|------|---------|
| **MoE** | Mixture of Experts — many FFNs, only some activated per token |
| **TQP** | TurboQuant-PreTraining — train with quantized weights |
| **ZeRO-3** | DeepSpeed strategy: distribute everything across GPUs |
| **Router** | Neural network that decides which experts each token uses |
| **Load balancing** | Loss term ensuring all experts get used evenly |
| **Shard** | A piece of the training data (typically 1-4B tokens) |
| **Curriculum** | The schedule of what data quality to train on when |
| **Dense model** | Standard transformer — all parameters used for every token |
| **Checkpoint** | Saved state of training that can be resumed |

---

## Summary and Conclusion

### What LightningLM Demonstrates

LightningLM is a proof that **large-scale LLM training is not exclusive to tech giants**. Through careful engineering:

1. **Incremental growth** — Validate at small scale, grow to large scale using proven weights
2. **State-preserving transitions** — Never throw away training progress
3. **Quantization-aware training** — Train in 4-bit precision to reduce memory requirements
4. **Novel architectures** — Kronecker embeddings and BrahmicTokenizer reduce parameter count
5. **Efficient MoE** — 120B total parameters but only 6B active per token

### What You Can Learn From This Project

Even if you can't train a 120B model, this project teaches:
- How LLM training works at a systems level
- How DeepSpeed ZeRO distributes training across GPUs
- How Mixture of Experts models work
- How to grow a model from small to large
- How quantization enables larger models in limited memory
- How curriculum learning schedules work

### The Broader Significance

Training a 120B model on 8 GPUs was considered impossible until recently. LightningLM shows it's achievable through:
- Mathematical cleverness (Kronecker embeddings, MoE routing)
- Systems engineering (DeepSpeed, custom CUDA kernels)
- Training methodology (incremental growth, TQP)

This kind of work is what enables research groups at universities and small companies to compete with billion-dollar AI labs.

---

*Written for learners new to LLM pre-training. Concepts are explained from first principles, assuming no prior experience with distributed training or custom model architectures.*
