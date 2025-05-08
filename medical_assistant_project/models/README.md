# Local LLM Models Setup

This directory is used to store local LLM model files for fallback when the HuggingFace API is unavailable.

## Setup Instructions

1. Install the required dependencies:
   ```
   pip install transformers accelerate bitsandbytes
   ```

2. Update your `.env` file with the following settings:
   ```
   # LLM Configuration
   USE_HUGGINGFACE_API=true
   LOCAL_MODELS_DIR=/absolute/path/to/your/medical_assistant_project/models
   LOCAL_MODEL_DEVICE=cuda  # Use 'cpu' if you don't have a GPU
   LOCAL_MODEL_DTYPE=auto   # Options: auto, float16, bfloat16, float32
   ```

3. The first time you run with a local model, it will automatically download the model files to your HuggingFace cache directory (usually `~/.cache/huggingface/`). You can also specify a custom cache directory by setting the `TRANSFORMERS_CACHE` environment variable.

## Environment Variables

- `USE_HUGGINGFACE_API`: Set to "true" to use HuggingFace API as primary, "false" to always use local models
- `LOCAL_MODELS_DIR`: Directory for any additional model files
- `LOCAL_MODEL_DEVICE`: Device to run models on ("cuda" for GPU, "cpu" for CPU)
- `LOCAL_MODEL_DTYPE`: Data type for model weights ("auto", "float16", "bfloat16", "float32")
- `TRANSFORMERS_CACHE`: (Optional) Custom directory for downloaded model files

## GPU Memory Requirements

Different models require different amounts of GPU memory:

- TinyLlama (1.1B): ~2GB VRAM
- Phi-3-mini (3.8B): ~8GB VRAM
- Mistral-7B: ~14GB VRAM
- Llama-3-8B: ~16GB VRAM

If you have limited GPU memory, you can:

1. Use smaller models like TinyLlama or Phi-3-mini
2. Enable 8-bit quantization by adding `load_in_8bit=True` to the model loading parameters
3. Use CPU mode by setting `LOCAL_MODEL_DEVICE=cpu` (much slower but works on any machine)

## Model Optimization Tips

For faster inference and reduced memory usage:

1. For 4-bit quantization (saves memory, slight quality loss):
   ```python
   # Add to model loading parameters
   load_in_4bit=True,
   bnb_4bit_compute_dtype=torch.float16,
   bnb_4bit_quant_type="nf4"
   ```

2. For 8-bit quantization (balanced approach):
   ```python
   # Add to model loading parameters
   load_in_8bit=True
   ```

3. For CPU offloading (when GPU memory is limited):
   ```python
   # Use device_map="auto" instead of specific device
   device_map="auto"
   ```

## Troubleshooting

- If you encounter CUDA out-of-memory errors, try a smaller model or enable quantization
- If models are loading slowly, they're being downloaded - subsequent runs will be faster
- For specific model errors, check the model's Hugging Face page for special requirements
