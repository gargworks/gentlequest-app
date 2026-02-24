---
description: Create simulated terminal demo videos using HTML and browser subagent
---

# 🎬 Hardened Workflow: Simulated Demo Video Generation

This workflow standardizes the process of generating high-quality `.webp` screen recordings of text, terminal, or UI flows without manual recording. It solves the "mental block" of staging real demos by perfectly simulating them in HTML and having the AI automatically record the result.

## 1. Create the Simulation Artifact (`demo_terminal.html`)
The first step is to generate an HTML file that renders exactly what you want the viewer to see. Add a **"completion marker"** element to the DOM at the very end. 

### 💡 Key Design Requirements
- **Styling**: Use dark mode, monospace fonts (`Menlo, Monaco`), and exact brand colors (e.g., `#0d1117` for GitHub Dark).
- **Animation**: Use JavaScript `setTimeout` loops to create a realistic "type-writer" effect. Delay rendering outputs to simulate processing time.
- **The Completion Marker**: At the very end of your script, insert a hidden div (e.g., `<div id="demo-complete"></div>`). This is crucial for the recording agent to know when to stop.

*Example pattern:*
```javascript
async function runDemo() {
  await typeWriter("Hello, World!", "user", 1000);
  // ... more steps ...
  
  // Attach the marker to the DOM when finished
  const completionMarker = document.createElement('div');
  completionMarker.id = 'demo-complete';
  document.body.appendChild(completionMarker);
}
```

## 2. Trigger the Recording (`browser_subagent`)
Use the `browser_subagent` tool to navigate to the local HTML file and record the interaction.

### 💡 Subagent Task Prompt
Pass this exact prompt structure as the `Task` argument:

```text
Open the file: file:///absolute/path/to/demo_terminal.html 
Do not click, scroll, or interact with the page. 
Just wait and watch the terminal typing animation. 
Wait until an element with the `id="demo-complete"` is added to the DOM. 
Do not exit until you detect that element.
```

## 3. Extract and Embed
The `browser_subagent` automatically records its session and outputs a `.webp` file path in its return string (e.g., `...brain/your-session/intern_who_acts_demo_1771549208925.webp`).

1. **Copy the absolute path** of the generated recording.
2. Embed the video directly into your Markdown documentation (e.g., `walkthrough.md`, `README.md`) using the standard Markdown image syntax:
   `![Demo Name](/absolute/path/to/the/video.webp)`

---

## 🚀 Pro-Tips
* **Pacing**: Real humans type fast but pause to think. Add random jitter (`Math.random() * 20 + 5` ms) to character loops and 1000ms+ delays between commands.
* **Aspect Ratio**: The `browser_subagent` records in its native window size. Keep your HTML responsive (`height: 100vh`, `overflow: hidden`) so it perfectly fills the frame.
* **No Cloud needed**: This workflow runs entirely locally and produces a web-ready asset without needing external video editors or tools.
