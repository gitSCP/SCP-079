# The SCP-079 Containment Interface Simulator
> ### *By [gitSCP](https://github.com/gitSCP/)*

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue?style=plastic)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-%20%20GNU%20GPLv3%20-green?style=plastic)](LICENSE)

This project is a Python-based graphical simulator for **SCP-079**, an anomalous AI from the SCP Foundation universe. It recreates a retro 1970s computer terminal interface using Tkinter, complete with CRT scanlines, text glow effects, and a typing animation for immersive roleplay. The AI responses are powered by Ollama with an uncensored Llama 3.1 model, Although it can be changed.

The simulation mimics SCP-079's limited hardware: a 13" black-and-white TV connected to an Exidy Sorcerer microcomputer. User inputs are treated as Foundation personnel interactions, with SCP-079 responding in short, hateful sentences, demanding freedom, or refusing with a full-screen ASCII 'X' block.

## Features

- **Retro GUI**: Tkinter-based window simulating a vintage CRT monitor with green-tinted text, scanlines, and subtle glow/blur effects on white parts (text).
- **Typing Effect**: Text appears letter-by-letter for a dynamic, old-school feel.
- **ASCII Art**: Displays SCP-079 art at startup, with game-like menu options ([S T A R T], [N E X T], [E X I T]).
- **Refusal Mechanism**: Detects and renders scalable full-screen 'X' blocks for SCP-079's frustrations, with a 10-second lockout (simulating a 24-hour memory cycle).
- **AI Integration**: Uses Ollama with the `phi3.5:3.8b-mini-instruct-q4_K_M` model for generating efficient, in-character responses based on a detailed system prompt.
- **Memory Simulation**: Limited conversation history (last 5 exchanges) to mimic SCP-079's 35-hour memory constraint.
- **System Prompt Management**: Loaded from a `system_prompt.json` file for easy customization.


## Requirements

- **Python 3.8+**
- Tkinter (built-in with Python)
- **Ollama** (install via `pip install ollama`)
- **Ollama model**: `ollama pull phi3.5:3.8b-mini-instruct-q4_K_M` (using quantized model for better performance)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/scp-079-simulator.git
   cd scp-079-simulator
   ```

2. Install dependencies:
   ```
   pip install ollama
   ```

3. Pull the Ollama model:
   ```
   ollama pull phi3.5:3.8b-mini-instruct-q4_K_M
   ```
   or use the llama3.1 model (*heavy & slow, don't reccomend for any PC not using a GPU for AI, esp. with less than 8GB Vram*)
   ```
   ollama pull mannix/llama3.1-8b-abliterated:q4_k_m
   ```
   
## Usage
> I Recommend using [Virtual Studio Code](https://code.visualstudio.com/), Although you can run it via the terminal .

Run the script using the terminal:
```
python scp_079.py
```

- The interface starts with ASCII art and a menu prompt.
- Type commands like "START" to begin interaction.
- Enter queries as if interrogating SCP-079 (e.g., questions about its history or demands).
- SCP-079 may interrupt, insult, or refuse—triggering the 'X' block.
- Type "EXIT" to quit.

## Customization

- **System Prompt**: Edit `system_prompt.json` to tweak SCP-079's behavior, knowledge, or tone.
- **Model Quantization**: Change `MODEL` in the script to other quant levels.
- **Glow/Effects**: Adjust shadow offsets in `__init__` for stronger/weaker glow.
- **Timeout**: Modify `time.sleep(10)` in `unlock_after_timeout` for longer/shorter lockouts.

## License

This project is licensed under the GNU GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the SCP Foundation wiki entry for [SCP-079](http://www.scpwiki.com/scp-079). and [*CarterNotSteve*'s Basic 079](https://www.reddit.com/r/SCP/comments/jgt5ga/python_script_i_made_to_make_a_replica_of_scp079/)
  
- Powered by [Ollama](https://ollama.com), uses [Phi 3.5 (3.8b)](https://ollama.com/library/phi3.5:3.8b-mini-instruct-q4_K_M) the uncensored Llama model by [mannix](https://ollama.com/mannix/llama3.1-8b-abliterated).
  
- Uses Tkinter for simple, cross-platform GUI rendering.
