# 🚀 Reality Router

### **The Intelligent Decision Engine for AI Agents**
*Eliminate Model Lock-in. Automate Intelligence. Optimize for the User.*

**Reality Router** is a high-performance LLM routing gateway designed for the agentic era. While standard proxies simply pass requests through, Reality Router uses **Expected Utility Theory** and real-time calibration to choose the perfect model for every single prompt. 

In a world where model performance fluctuates and costs vary by orders of magnitude, Reality Router puts the power back in the hands of the user—ensuring you always get the best "bang for your buck" without manual switching.

---

## 🧠 Why Reality Router?

For developers building AI Agents (Roo Code, OpenClaw, AutoGPT), picking a model is usually a trade-off between "Too Expensive" (GPT-4o/Claude 3.5 Sonnet) and "Too Unreliable" (Small local models). 

Reality Router solves this by acting as a **Smart Middleware** that:
1. **Evaluates Intelligence:** Uses the **Reality Check API** to predict the success probability of a model for a specific task.
2. **Calculates Utility:** Applies a mathematical formula to balance Accuracy, Cost, and Speed.
3. **Enforces Quality:** Acts as a "Guardian" to fix malformed tool calls and prevent hallucinated syntax.

---

## ⚙️ The Core Engine: Expected Utility Theory (EUT)

Every request is passed through our decision-theoretic engine. We calculate the utility of every model $m$ in your pool:

$$EU(m) = p \cdot 100 - \alpha \cdot cost - \beta \cdot time$$

- **$p$ (Probability):** The calibrated likelihood of success for the given prompt.
- **$100$ (Constant Reward):** Success is weighted as a constant value of 100 units.
- **$\alpha$ (Cost Sensitivity):** Your preference for saving money.
- **$\beta$ (Time Sensitivity):** Your preference for low latency.

> **Dynamic Tuning:** Use the interactive Dashboard slider to shift priorities in real-time. Slide left for maximum frugality; slide right for raw speed.

---

## 🛡️ Strict Validation Gateway (The "Guardian")

Reality Router doesn't just route; it protects. It sits between the model and your agent to ensure protocol compliance:
- **Leak Protection:** Detects and scrubs raw tool tags (like `<function>`) that models accidentally leak into text.
- **Ghost Tool Detection:** Rejects responses that attempt to call tools you didn't provide.
- **Heuristic Rescue:** Automatically recovers valid JSON tool calls buried in conversational fluff.
- **JSON Validation:** Validates arguments against your schema before the agent ever sees them.

---

## 🚀 Key Features

### **1. ⚡ Intelligent Routing Strategies**
*   **Snap (Single-shot):** High-speed routing to the model with the highest predicted utility.
*   **Ladder (Sequential):** The ultimate reliability mode. Starts with the most cost-effective model and automatically escalates to "smarter" models only if the response fails validation or confidence is too low.

### **2. 🔄 Automatic Feedback Loop**
The system learns as you use it. Validated tool calls automatically send "Happy Path" signals back to the calibration engine, refining future routing decisions.

### **3. 🔌 Multi-Provider Auto-Discovery**
Bring your own keys. Reality Router automatically discovers and benchmarks models from:
*   **OpenAI, Anthropic, Mistral, Gemini, & DeepSeek**
*   **Local Ollama** instances
*   **Custom OpenAI-compatible** endpoints

### **4. 📊 Live Developer Dashboard**
Monitor your agent's "Unit Economics" in real-time. Track savings, model success rates, and event traces through a built-in Control Center.

---

## ⚡ Quick Start

### **Linux / macOS**
```bash
curl -fsSL https://raw.githubusercontent.com/Lars-confi/RealityRouterTemp/main/install.sh | bash
```

### **Windows (PowerShell)**
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Lars-confi/RealityRouterTemp/main/install.ps1'))
```

---

## 🛠️ Developer Integration

Reality Router is **100% OpenAI API compatible**. You don't need to rewrite your agent; just change your environment variables:

- **Base URL:** `http://localhost:8000/v1`
- **API Key:** `any` (or your configured secret)
- **Model:** `gpt-4o` (or any string—the router will intercept and choose the best actual model for the job).

---

## 🤝 Contributing

We are building the future of user-centric AI infrastructure. If you're interested in decision theory, agent protocols, or high-performance routing, we'd love your help!

*Built with ❤️ by Confidentia AI and the open-source community.*