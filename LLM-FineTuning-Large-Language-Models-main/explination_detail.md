# LLM Fine-Tuning: Large Language Models — Complete Explanation Guide

> **Who this is for:** Beginners who want to learn hands-on LLM fine-tuning through Jupyter notebooks, covering everything from BERT to Llama-3, from basics to advanced techniques.

---

## Table of Contents

1. [What is This Project?](#what-is-this-project)
2. [Understanding the Technology Stack](#technology-stack)
3. [Module 1 — BERT and Classic Transformer Models](#module-1-bert)
4. [Module 2 — Modern LLM Fine-Tuning](#module-2-modern-llm)
5. [Module 3 — Advanced Techniques (QLoRA, DPO, ORPO)](#module-3-advanced)
6. [Module 4 — Inference and Production](#module-4-inference)
7. [Key Concepts Explained](#key-concepts)
8. [The Training Pipeline End to End](#training-pipeline)
9. [Cheatsheet](#cheatsheet)
10. [Summary and Conclusion](#summary-and-conclusion)

---

## What is This Project?

This is a **collection of Jupyter notebooks** covering the full spectrum of LLM fine-tuning — from classic BERT-based models to state-of-the-art Llama-3, Mistral, and Falcon models.

Think of it as a **practical course library** where each notebook teaches one specific technique:

```
notebooks/
├── classic models (BERT, DistilBERT, DeBERTa, Pegasus)
├── medium LLMs (Mistral 7B, Falcon 7B, Phi, TinyLlama)
├── large LLMs (Llama-2-70B, CodeLlama-34B, Mixtral 8x7B)
└── techniques (QLoRA, DPO, ORPO, quantization, inference)
```

Each notebook is **self-contained** — you can open it in Google Colab and run it without any setup.

---

## Understanding the Technology Stack

### The Hardware Reality

| Model Size | Minimum GPU | Cost per Hour |
|-----------|-------------|---------------|
| BERT (110M) | Any GPU / CPU | Free (Colab) |
| Llama-2-7B | 16 GB VRAM | Free (Colab T4) |
| Mistral-7B | 16 GB VRAM | Free (Colab T4) |
| Llama-2-13B | 24 GB VRAM | Colab Pro ($10/mo) |
| Llama-2-70B | 80 GB VRAM (with QLoRA: 48 GB) | A100 rent (~$2/hr) |
| CodeLlama-34B | 40 GB VRAM (with QLoRA: 24 GB) | A10G ($0.75/hr) |

**QLoRA changes everything** — it makes 70B models trainable on consumer hardware.

### Key Python Libraries

| Library | Purpose | Who Makes It |
|---------|---------|-------------|
| **transformers** | Load and use any Hugging Face model | Hugging Face |
| **peft** | LoRA and other parameter-efficient fine-tuning | Hugging Face |
| **trl** | High-level training loops (SFT, DPO, etc.) | Hugging Face |
| **bitsandbytes** | 4-bit and 8-bit quantization | Tim Dettmers |
| **accelerate** | Distribute training across GPUs | Hugging Face |
| **datasets** | Load and process training data | Hugging Face |
| **unsloth** | Optimized LoRA training (2x faster, 80% less VRAM) | Unsloth AI |
| **langchain** | LLM application framework | LangChain AI |
| **streamlit** | Build web apps for LLMs in Python | Streamlit |
| **gradio** | Quick demos and UIs for ML models | Hugging Face |

---

## Module 1: BERT and Classic Transformer Models

### What is BERT?

BERT (Bidirectional Encoder Representations from Transformers) — released by Google in 2018 — was the model that transformed NLP (Natural Language Processing).

Unlike GPT-style models that read left-to-right, BERT reads the **entire sentence at once** (bidirectionally), understanding context from both directions.

```
"I went to the bank [to deposit money]"  ← BERT sees both halves
vs
"I went to the bank by the [river]"      ← understands which meaning of "bank"
```

### BERT for Classification (Sentiment Analysis, Review Prediction)

**Use case:** Predicting if a customer review is positive or negative.

**How it works:**
```
Input: "This product is amazing!"
       ↓
BERT tokenizes: [CLS] This product is amazing! [SEP]
       ↓
BERT processes with 12 layers of attention
       ↓
[CLS] token output → Classification head → Positive (98%)
```

The `[CLS]` (classification) token is special — BERT is trained to pack the overall sentence meaning into this token.

**Notebooks in this project:**
- `Fine_Tuning_HuggingFace_Transformer_BERT_Yelp_Customer_Review_Predictions` — Predict Yelp review ratings (1-5 stars)
- `bert-base-uncased-fine-tuned-kaggle-hate-speech-dataset` — Classify hate speech
- `FineTuning_BERT_for_Multi_Class_Classification_Turkish` — Multi-class classification

**Example code pattern:**
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer

# Load pre-trained model + tokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModelForSequenceClassification.from_pretrained(
    "bert-base-uncased",
    num_labels=5  # 5 star ratings
)

# Tokenize your data
def tokenize(examples):
    return tokenizer(examples["text"], truncation=True, padding=True)

tokenized_dataset = dataset.map(tokenize, batched=True)

# Train
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
)
trainer.train()
```

### Named Entity Recognition (NER)

**Use case:** Find names, organizations, dates in text.

```
"Apple Inc. was founded by Steve Jobs in Cupertino, California"
  [ORG]                      [PER]          [LOC]     [LOC]
```

BERT is excellent at this because it reads the whole sentence to understand context.

**Notebooks:**
- `YT_Fine_tuning_BERT_NER_v1.ipynb` — Basic NER fine-tuning
- `Zero_Shot_Learning_multilingual-NER.ipynb` — NER without training data

### Text Summarization (Pegasus, BART, T5)

These are **encoder-decoder models** — they read a document (encoder) and generate a summary (decoder).

```
Input: [Long article about climate change...]
       ↓ Encoder reads → Decoder generates
Output: "Scientists warn of accelerating climate change affecting coastal cities."
```

**Notebooks:**
- `Fine_Tuning_Pegasus_for_Text_Summarization.ipynb`
- `Text_Summarization_ BART _T5_Pegasus.ipynb`

### Topic Modeling (BERTopic)

**Use case:** Automatically discover what topics a collection of documents covers.

You have 10,000 news articles. What are the main themes?

```
BERTopic discovers:
- Topic 1: "elections, voting, candidates, polls" (Politics)
- Topic 2: "stocks, market, earnings, revenue" (Finance)
- Topic 3: "vaccine, virus, outbreak, health" (Healthcare)
```

**How it works:**
1. Convert documents to embeddings using BERT
2. Reduce dimensions with UMAP
3. Cluster similar embeddings with HDBSCAN
4. Generate topic labels using c-TF-IDF

**Notebooks:**
- `Topic-modeling-with-bertopic-arxiv-abstract/` — Topic modeling on academic papers
- `Topic_Modeling_with_BERT_and_Automatic_cluster_labeling/` — With automatic labeling

---

## Module 2: Modern LLM Fine-Tuning

### The Shift from BERT to GPT-style Models

BERT is great for **understanding** tasks (classification, NER). For **generation** tasks (chat, code writing, Q&A), **autoregressive models** like Llama, Mistral, and Falcon are better.

The key difference:
- **BERT:** Reads text, extracts meaning (encoder only)
- **GPT/Llama/Mistral:** Generates text, one token at a time (decoder only)

### Mistral 7B Fine-Tuning

Mistral 7B is one of the best open-source models in the 7B parameter range. It punches above its weight, often matching much larger models.

**Notebooks:**
- `Mistral_FineTuning_with_PEFT_and_QLORA.ipynb` — Standard QLoRA fine-tuning
- `Mistral-7B-Inferencing.ipynb` — Running inference only (no training)

**The fine-tuning process:**
```
1. Load Mistral-7B in 4-bit (uses ~8 GB GPU memory)
2. Apply LoRA adapters to attention layers
3. Format your data as chat conversations
4. Train with SFTTrainer for 1-3 epochs
5. Save the LoRA adapter (~50 MB file)
6. (Optional) Merge adapter into model
```

### Falcon 7B Fine-Tuning

Falcon was the first open-source model to genuinely compete with GPT-3.5 on benchmarks. Made by the Technology Innovation Institute in Abu Dhabi.

**Notebook:** `Falcon-7B_FineTuning_with_PEFT_and_QLORA.ipynb`

Training on the **Guanaco dataset** — a high-quality multi-turn conversation dataset derived from OpenAssistant.

### TinyLlama Fine-Tuning

TinyLlama is a 1.1B parameter model that fits on almost any hardware. Useful when:
- You have very limited compute
- You need fast inference on edge devices
- You want to quickly prototype fine-tuning without large resource requirements

**Notebooks:**
- `tinyllama_fine-tuning_Taylor_Swift.ipynb` — Fun notebook: teach TinyLlama Taylor Swift lyrics
- `TinyLlama_with_Unsloth_and_RoPE_Scaling_dolly-15k.ipynb` — More serious training

### Llama-2 Fine-Tuning

Llama-2 from Meta is the gold standard open-source model family. Comes in 7B, 13B, and 70B sizes.

**Notebooks:**
- `LlaMa-2-FineTuning.ipynb` — Basic fine-tuning
- `Local-Inferencing_LlaMa-2.ipynb` — Running locally
- `Inference_Yarn-Llama-2-13b-128k_Github.ipynb` — Long context (128K tokens) inference

### CodeLlama Fine-Tuning

CodeLlama is Llama-2 further pre-trained on code. Excellent for:
- Code generation
- Code completion
- Bug fixing
- Code explanation

**Notebooks:**
- `Finetune_codellama-34B-with-QLoRA.ipynb` — Fine-tune the 34B code model
- `CodeLLaMA_34B_Conversation_with_Streamlit.py` — Build a code chat app

**The conversation format for code models:**
```
[INST] Write a Python function to sort a list of dictionaries by a key [/INST]
def sort_dicts(lst, key):
    return sorted(lst, key=lambda x: x[key])
[/INST]
```

### Gemma Fine-Tuning (Google's Model)

Gemma is Google's open-source model family, released in 2024.

**Notebook:** `gemma-2b_ORPO_FineTuning_full_precision/`

Trains with **ORPO** (Odds Ratio Preference Optimization) — a newer training method that combines supervised fine-tuning and preference learning in one pass.

---

## Module 3: Advanced Techniques

### Technique 1 — DPO (Direct Preference Optimization)

**The problem:** Standard fine-tuning (SFT) teaches the model what text looks like. But it doesn't teach the model to prefer good answers over bad ones.

**RLHF (Reinforcement Learning from Human Feedback)** was the original solution — have humans rate responses, train a reward model, use RL to maximize reward. Complex and unstable.

**DPO** achieves the same goal without RL, using only preference pairs:

```json
{
  "prompt": "What is the capital of France?",
  "chosen": "The capital of France is Paris.",
  "rejected": "France's capital is London."
}
```

DPO trains the model to prefer the `chosen` response over the `rejected` one directly.

**Mathematical idea:** DPO reformulates the RLHF objective so it can be optimized as a classification problem. No reward model needed.

**Notebook:** `Mistral_7b_FineTuning_with_DPO_Direct_Preference_Optimization.ipynb`

**Code:**
```python
from trl import DPOTrainer

trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,  # frozen reference model
    tokenizer=tokenizer,
    train_dataset=dataset,
    beta=0.1,  # controls how much the model deviates from reference
)
trainer.train()
```

### Technique 2 — ORPO (Odds Ratio Preference Optimization)

**DPO** requires a separate reference model (doubles memory).

**ORPO** eliminates the reference model by incorporating the preference objective directly into the SFT loss:

```
ORPO Loss = SFT Loss + λ × Odds Ratio Loss

Where odds ratio penalizes generating rejected responses
```

Benefits:
- No reference model needed
- 50% less memory than DPO
- Often better quality than DPO

**Used in:** `gemma-2b_ORPO_FineTuning_full_precision/v2_Colab_Gemma_2b_orpo.ipynb`

### Technique 3 — GPTQ Quantization

**GPTQ** = GPT Quantization. An algorithm that converts model weights from 16-bit floating point to 4-bit integers while minimizing quality loss.

```
Original: 1.234567890 (32-bit float = 4 bytes)
GPTQ:     12 (4-bit int = 0.5 bytes) ← 8x smaller!
```

The trick: GPTQ doesn't just round to the nearest integer. It uses a technique called **Second Order Error Minimization** — it looks at how the quantization error propagates through the network and minimizes the total error, not just per-weight error.

**Use cases:**
- Deploy 7B models on consumer GPUs (8 GB VRAM)
- Faster inference (4-bit compute is faster on modern GPUs)
- Lower serving costs

**Notebooks:**
- `LLM_Techniques_and_utils/4-bit_LLM_Quantization_with_GPTQ.ipynb`
- `Finetune_llama_2_GPTQ/` — Fine-tune an already-quantized model

### Technique 4 — Understanding Rotary Positional Embeddings (RoPE)

**The problem:** Transformers need to know the position of each token. Classic approaches (absolute position embeddings) don't generalize well to sequences longer than training length.

**RoPE:** A clever mathematical trick that encodes position by rotating the embedding vectors.

```
Token at position 0: embedding vector rotated by 0 degrees
Token at position 1: embedding vector rotated by θ degrees
Token at position 2: embedding vector rotated by 2θ degrees
...
```

The dot product between two rotated vectors naturally encodes their relative distance, making attention position-aware.

**YaRN:** An extension of RoPE that allows inference at contexts longer than training (e.g., train on 4K tokens, run inference at 128K tokens).

**Notebook:** `Inference_Yarn-Llama-2-13b-128k_Github.ipynb` — Demonstrates 128K context inference using YaRN.

### Technique 5 — Mixture of Experts (MoE)

**Mistral 7B** is dense — all 7B parameters are used for every token.

**Mixtral 8x7B** is a Mixture of Experts:
- Has 8 "expert" feed-forward networks (each 7B-equivalent)
- For each token, only 2 of the 8 experts are activated
- A "router" decides which experts to use

```
Total parameters: 8 × 7B = 56B (but only 47B are actually unique due to shared layers)
Active parameters per token: 2 × 7B = 14B

So it has 56B parameters but runs like a 14B model!
```

This means Mixtral is quality-equivalent to a 56B model but inference cost of a 14B model.

**Notebooks:**
- `togetherai-api-with_Mixtral.ipynb` — Using Mixtral via API
- `LLM_Techniques_and_utils/MOE-Mixture-of-Experts/` — Deep dive on MoE math
- `LLM_Techniques_and_utils/MoE_implementation_Mistral_official_Repo.ipynb` — Implementation

### Technique 6 — AirLLM (Layered Inference)

**The problem:** Llama-2-70B needs 140 GB to load fully into memory.

**AirLLM's solution:** Load only one layer at a time. Process it. Load the next layer.

```
Layer 1 → process tokens → save output → unload layer 1 → load layer 2 → ...
```

This allows running a 70B model inference on a **single 4 GB GPU** — at the cost of speed (much slower than normal inference).

**Notebook:** `layered_inference_with_airllm_70B_LLM_Inference_on_a_Single_4GB_GPU.ipynb`

---

## Module 4: Inference and Production

### Web Scraping with LLMs (AnthropicAI + LangChain)

**Use case:** Extract structured data from web pages using Claude.

**How it works:**
1. Scrape HTML from a website
2. Pass to Claude with a prompt: "Extract product name, price, description"
3. Claude returns structured JSON

**Advantages over traditional scrapers:**
- No need to write CSS selectors that break when the page changes
- Can handle ambiguous and varied page layouts
- Can understand context and infer missing fields

**Notebook:** `Web_scraping_with_Large_Language_Models_LLM_AnthropicAI_LangChainAI.ipynb`

### TogetherAI API Integration

TogetherAI is a cloud provider that hosts many open-source models (Llama, Mistral, Falcon) via API, similar to OpenAI's API but for open-source models.

**Notebooks:**
- `TogetherAI_API_with_LangChain.ipynb` — Using LangChain with TogetherAI
- `togetherai-api-with_Mixtral.ipynb` — Running Mixtral inference

### CodeLlama Streamlit App

Build a **web interface for a code assistant** using Streamlit:

```python
import streamlit as st
from transformers import pipeline

@st.cache_resource
def load_model():
    return pipeline("text-generation", model="codellama/CodeLlama-34b-Instruct-hf")

model = load_model()

prompt = st.text_area("Enter your coding question:")
if st.button("Generate Code"):
    with st.spinner("Generating..."):
        response = model(prompt, max_new_tokens=500)[0]["generated_text"]
        st.code(response)
```

**File:** `CodeLLaMA_34B_Conversation_with_Streamlit.py`

---

## Key Concepts

### The Transformer Architecture (Quick Reference)

```
Transformer = Encoder + Decoder (or just one or the other)

Attention = "Which parts of the input are most relevant to this token?"

Multi-head attention = Run attention multiple times in parallel,
                       each head focuses on different aspects

Feed-forward network = Process each position independently
                       (two linear layers with ReLU between)

Layer norm = Normalize activations for training stability

Residual connections = Skip connections that preserve gradient flow
```

### Tokenization

Before any model processes text, it converts text to numbers (tokens).

```
Text: "Hello, world!"
Tokens: [15496, 11, 995, 0]  (GPT-2 tokenizer)
```

**Vocabulary:** The set of all possible tokens. GPT-4 uses ~100K tokens, Llama uses 32K.

**Subword tokenization:** Common words → single token. Rare words → multiple tokens.
```
"running" → [running]     (1 token)
"antidisestablishmentarianism" → [ant, idis, est, ablish, ment, arian, ism]  (7 tokens)
```

### Chat Templates

Different models use different formats for conversations. You must use the right template:

**Llama-2 format:**
```
<s>[INST] System: You are a helpful assistant. [/INST]</s>
<s>[INST] User question here [/INST] Assistant answer here </s>
```

**ChatML format (used by Mistral, Qwen):**
```
<|im_start|>system
You are a helpful assistant.<|im_end|>
<|im_start|>user
User question here<|im_end|>
<|im_start|>assistant
Assistant answer here<|im_end|>
```

**Notebook:** `LLM_Techniques_and_utils/apply_chat_template.ipynb`

### Evaluation — Perplexity

**Perplexity** measures how "surprised" a model is by text. Lower = better.

```
Very good model: Perplexity ≈ 5-10
                "I predicted most of the text correctly"

Poor model: Perplexity ≈ 100+
            "I was frequently surprised by what came next"
```

The formula: `Perplexity = exp(cross-entropy loss)`

If your model achieves 3.5 perplexity, it means on average it would pick the correct next token from ~3.5 possibilities — very good!

**Notebook:** `LLM_Techniques_and_utils/Validation_log_perplexity.md`

---

## The Training Pipeline End to End

### Step 1: Choose Your Model

```
Task type?
├── Classification, NER, Regression → BERT-family (110M-1B)
├── Instruction following, Chat → Llama/Mistral (7B-70B)
└── Code generation → CodeLlama, DeepSeek-Coder (7B-34B)
```

### Step 2: Prepare Your Data

```python
from datasets import Dataset

# Your data must have "text" or "prompt"/"response" fields
data = [
    {"text": "<|user|>What is Python?<|assistant|>Python is..."},
    {"text": "<|user|>How do I open a file?<|assistant|>Use open()..."},
]

dataset = Dataset.from_list(data)
```

### Step 3: Configure Your Training

```python
from peft import LoraConfig
from trl import SFTConfig

lora_config = LoraConfig(r=16, lora_alpha=32, ...)
training_config = SFTConfig(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    learning_rate=2e-4,
    ...
)
```

### Step 4: Train

```python
trainer = SFTTrainer(
    model=model,
    args=training_config,
    train_dataset=dataset,
    peft_config=lora_config,
)
trainer.train()
```

### Step 5: Evaluate

```python
# Qualitative: generate responses and review manually
# Quantitative: use evaluation benchmarks (MMLU, HumanEval, etc.)
```

### Step 6: Save and Deploy

```python
# Save LoRA adapter only
trainer.save_model("./my-adapter")

# Or merge and export to GGUF for efficient inference
# Then run with llama.cpp or Ollama
```

---

## Cheatsheet

### Model Selection Guide

| If you need... | Use model | Size | Framework |
|----------------|-----------|------|-----------|
| Fast classification | DistilBERT | 65M | HuggingFace |
| Strong classification | DeBERTa-v3 | 183M | HuggingFace |
| Summarization | Pegasus/BART | 568M | HuggingFace |
| General chat (limited GPU) | TinyLlama | 1.1B | Unsloth |
| General chat (consumer GPU) | Mistral-7B | 7B | QLoRA |
| Code generation | CodeLlama-7B | 7B | QLoRA |
| High quality chat | Llama-2-70B | 70B | QLoRA on A100 |
| Best open source | Mixtral 8x7B | 47B | QLoRA |

### Training Technique Selection

| Goal | Technique |
|------|----------|
| Learn new style/format | SFT (Supervised Fine-Tuning) |
| Improve response quality | DPO |
| Save memory vs DPO | ORPO |
| Limited GPU | QLoRA |
| Any GPU size | LoRA |
| Best quality | DoRA or AdaLoRA |

### Common Bugs and Fixes

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| CUDA out of memory | Batch too large or model too big | Reduce batch size, use gradient accumulation |
| Training loss not decreasing | Learning rate too low or wrong | Try 2e-4 to 3e-4 |
| Gibberish outputs | Wrong chat template | Check tokenizer.apply_chat_template() |
| Very slow training | Not using bfloat16 | Add bf16=True to training args |
| Model forgets its base knowledge | Too many training epochs | Use 1-3 epochs max |

---

## Summary and Conclusion

### What This Project Covers

This project is a **comprehensive library** of practical LLM fine-tuning notebooks spanning:
- **Classic NLP models** (BERT, DistilBERT, RoBERTa, DeBERTa)
- **Encoder-decoder models** (Pegasus, BART, T5 for summarization)
- **Modern decoder LLMs** (Llama-2, Llama-3, Mistral, Falcon, Phi, TinyLlama)
- **Specialized models** (CodeLlama for code, Gemma from Google)
- **Advanced techniques** (QLoRA, DPO, ORPO, GPTQ quantization, MoE)
- **Production patterns** (API integration, Streamlit apps, layered inference)

### The Learning Path

1. **Start with BERT notebooks** — simpler architecture, faster to train, great for classification
2. **Move to Mistral-7B with QLoRA** — the practical workhorse for most tasks
3. **Learn DPO** — to improve response quality beyond just imitation learning
4. **Explore Mixtral** — to understand MoE architectures
5. **Study CodeLlama** — if code is your use case

### Key Insight

The biggest breakthrough in LLM fine-tuning is not a single technique — it's the combination of **quantization** (QLoRA) + **parameter efficiency** (LoRA) that allows training models that previously required data centers on a single consumer GPU.

This democratization means that fine-tuning is now accessible to individual researchers, students, and small companies — not just organizations with massive GPU clusters.

---

*This explanation is written for learners new to LLM fine-tuning. Technical concepts are explained from first principles with practical code examples.*
