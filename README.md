# Aira ChatBot (v1)

Aira ChatBot is an AI-driven conversational assistant framework originally architected as a core component of the Mynera ecosystem. This repository hosts **v1**, the foundational prototype and baseline architecture designed for modular dialog orchestration, context processing, and containerized deployment.

---

## 📌 Project Roadmap & Lifecycle Status

* **v1 (Current Version):** Initial baseline prototype establishing core chat endpoints, container isolation, and interaction workflows.
* **v2 (Iteration Stage):** Enhanced conversational pipeline with optimized processing logic and extended integrations.
* **v3 (Discontinued):** Planned as the production-ready enterprise deployment. Development was halted and archived due to the suspension of the parent project, **Mynera**.

---

## 🛠 Tech Stack & Environment

* **Containerization:** Docker
* **Version Control:** Git
* **Target Runtime:** Python / Node.js Microservice Environment

---

## ⚙️ Getting Started

### Prerequisites

* Git installed on your local machine
* Docker Engine & Docker Compose installed

### Setup & Local Execution

1. Clone the repository:
   ```bash
   git clone [https://github.com/ZaurAsgarli/Aira-ChatBot.git](https://github.com/ZaurAsgarli/Aira-ChatBot.git)
   cd Aira-ChatBot
   ```

2. Build the Docker container:
   ```bash
   docker build -t aira-chatbot:v1 .
   ```

3. Run the container:
   ```bash
   docker run -d -p 8000:8000 --name aira-v1 aira-chatbot:v1
   ```

---

## 📌 Repository Structure

```text
Aira-ChatBot/
├── .dockerignore       # Docker build exclusions
├── .git/               # Git version control metadata
└── README.md           # Project documentation
```

---

## 📄 License & Archival Notice

This repository represents an archived academic and historical prototype developed under the Mynera project initiative.