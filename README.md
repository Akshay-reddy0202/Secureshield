# 🛡️ SecureShield AI Gateway
An enterprise-grade AI security middleware and proxy that acts as an intelligent "bouncer" for Large Language Models (LLMs), enforcing data governance, preventing prompt injection, and scrubbing PII in real-time.

🌟 Features
- **⚡ Multi-Layered Security Pipeline**: Requests pass through Unicode Normalization, Input Guard, RBAC Policy Engine, Toxicity Guard, Semantic Guard, and PII Redaction.
- **🛡️ Active Rate Limiting (Network Guard)**: Middleware rate limiter to restrict request velocity and defend against DDoS attacks.
- **👤 Role-Based Access Control (RBAC)**: Fine-grained, department-level prompt safety policies (e.g., HR, Finance, and general employee constraints).
- **🤖 LLM-as-a-Judge Auditing**: Concurrently evaluates prompt toxicity and semantic jailbreak attempts using high-speed cloud LLMs.
- **🔍 Advanced PII Redaction**: Scrubs emails, phone numbers, API keys, and corporate vault secrets using spaCy, Microsoft Presidio, and custom regex pattern lists.
- **🔐 Secrets Leak Protection (Output Guard)**: Scans AI responses for leaked JWT tokens, API keys, and server credentials before they leave the gateway.
- **📊 Admin Monitoring Dashboard**: Visualizes operational traffic, threat analytics, risk distribution graphs, attack correlation trends, and recent activity logs.

🛠️ Tech Stack
### Frontend
- **React.js & Vite** - Modern, responsive web interface
- **Tailwind CSS** - Sleek, flexible, and premium dark-mode custom styles
- **Recharts** - Dynamic data visualization for traffic and threats
- **Framer Motion** - Fluid micro-animations and page transitions

### Backend
- **Python 3.12** - Core backend runtime
- **FastAPI & Uvicorn** - High-concurrency asynchronous endpoints
- **MongoDB & Motor** - Asynchronous database driver for logging, policies, and users

### AI / Security / NLP
- **Instructor** - Strict JSON structural output enforcement
- **OpenRouter API** - Gateway connection to model providers (`Llama 3.1 8b`, `Gemini 2.0 Flash`)
- **Microsoft Presidio & spaCy** - Highly optimized NLP-based anonymization
- **Lakera Guard API** - Advanced third-party prompt injection analyzer

Project Structure
```
SecureShield-AI/
├── backend/             # FastAPI backend
│   ├── app/             # Server core directories
│   │   ├── layers/      # 6 pipeline security layers
│   │   ├── services/    # DB, users, logging, and AI handlers
│   │   └── config.py    # Environment settings
│   ├── tests/           # Pipeline test suites
│   ├── .env.example     # Configuration template
│   └── requirements.txt # Python dependencies
├── frontend/            # React + Vite frontend
│   ├── src/             # Frontend source files
│   │   ├── pages/       # Dashboard, chat, logs, settings
│   │   └── components/  # Charts, layout, and pipeline simulator
│   └── package.json     # Node.js dependencies
└── README.md            # Project documentation
```

⚙️ Installation

1️⃣ Clone the Repository
```bash
git clone <PRIVATE_URL>
cd SecureShield-AI
```

2️⃣ Setup Backend
```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python -m app.main
```
Backend runs on: `http://localhost:8000`

3️⃣ Setup Frontend
```bash
cd ../frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend runs on: `http://localhost:5173`

🔥 How It Works
1. **Submit Prompt**: A user submits a query via the chat dashboard.
2. **Standardize & Intercept**: Network rate limits apply and Unicode normalizes characters to prevent bypasses.
3. **Policy & Intent Scan**: Role-based access controls and concurrent LLM judges scan for malicious prompt injection or toxic content.
4. **PII Scrubbing**: SpaCy, Presidio, and the corporate vault redact emails, phone numbers, and keys.
5. **Secure Dispatch**: The clean, safe prompt is forwarded to the backend LLM brain.
6. **Response Audit**: The response is validated to block or scrub secret leakage before hitting the user interface.

🚀 Future Enhancements
- **Active Firewall Blocking**: Real-time IP banning for users triggering recurrent high-severity security threats.
- **Exportable PDF Reports**: Automated SOC2/GDPR compliance reporting.
- **Unified SIEM Integrations**: Export security telemetry straight to Splunk or Datadog.
- **Multi-Model Routing**: Intelligently dispatch safe prompts to different models depending on tasks and cost optimization.

🤝 Contributing
Contributions are welcome!
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/NewFeature`)
3. Commit your changes (`git commit -m 'Add NewFeature'`)
4. Push to the branch (`git push origin feature/NewFeature`)
5. Open a Pull Request
