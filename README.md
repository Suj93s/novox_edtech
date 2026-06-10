# 🚀 Novox Mentor AI Backend

An intelligent AI-powered learning assistant backend built using **FastAPI**, **Supabase**, **OpenRouter**, and **Google Gemini**.

The platform provides personalized learning experiences through curriculum-aware tutoring, student profiling, mastery tracking, behavioral memory, Retrieval-Augmented Generation (RAG), intelligent model routing, and secure authentication.

---

# 📌 Features

## 🤖 AI Mentor Chat

* Real-time AI-powered tutoring
* Context-aware conversations
* Session-based memory
* Curriculum-guided responses

---

## 💬 Chat Management

* Persistent chat sessions
* Complete conversation history
* Session continuation support
* User-specific conversations

---

## 👤 Student Profiles

* Automatic profile creation
* Behavioral preferences storage
* Personalized prompt injection
* Student learning customization

---

## 📚 Curriculum Management

* Course management
* Module management
* Concept mapping
* Curriculum-aware tutoring

Example:

```json
{
  "course_name": "Advanced Java",
  "module_title": "Recursion and Memory",
  "concepts": [
    "recursive functions",
    "call stack",
    "base case",
    "memory usage"
  ]
}
```

---

## 🎯 Mastery Tracking

Tracks student proficiency for each curriculum module.

Example:

```text
Recursion → 0.25
Arrays → 0.80
OOP → 0.60
```

The mentor automatically adjusts explanations based on mastery level.

---

## 🧠 Behavioral Memory

Automatically learns student preferences.

Examples:

* Use simpler explanations
* Prefer code examples
* Struggles with recursion
* Avoid long answers

Behavioral memory is continuously updated from conversations.

---

## ⚡ Background Processing

* Asynchronous behavioral analysis
* Non-blocking profile updates
* Retry mechanism
* Webhook support

---

## 🔐 Authentication & Authorization

Powered by Supabase Authentication.

Features:

* JWT Validation
* Secure API access
* Session ownership validation
* User-level data isolation
* Row Level Security (RLS)

---

## 📄 Retrieval-Augmented Generation (RAG)

Supports:

* PDF Documents
* Markdown Files
* Text Files

Pipeline:

```text
Document Upload
      ↓
Chunking
      ↓
Embeddings
      ↓
Vector Storage
      ↓
Similarity Search
      ↓
Prompt Injection
      ↓
AI Response
```

---

## 🔍 Vector Search

Uses:

* pgvector
* OpenAI text-embedding-3-small
* Supabase PostgreSQL

Features:

* Semantic Search
* User-owned Documents
* Secure Retrieval

---

## 🧭 Intelligent Model Routing

Automatically selects the best AI model.

Examples:

| Query Type             | Model             |
| ---------------------- | ----------------- |
| Simple Questions       | Gemini Flash Lite |
| Coding Questions       | Gemini Pro        |
| Debugging Tasks        | Gemini Pro        |
| Document-heavy Queries | Advanced Model    |

Benefits:

* Lower Cost
* Faster Responses
* Better Accuracy

---

# 🏗️ Tech Stack

### Backend

* FastAPI
* Python

### Database

* Supabase PostgreSQL
* pgvector

### AI & LLM

* Google Gemini
* OpenRouter

### Authentication

* Supabase Auth
* JWT

### Storage

* Supabase

### Vector Search

* pgvector
* OpenAI Embeddings

---

# 📂 Project Structure

```text
.
├── api/
│   ├── auth.py
│   ├── chat.py
│   ├── documents.py
│   ├── health.py
│   ├── webhook.py
│   └── index.py
│
├── agents/
│   └── mentor_agent.py
│
├── services/
│   ├── chat_service.py
│   ├── curriculum_service.py
│   ├── mastery_service.py
│   ├── profile_service.py
│   ├── profile_analysis.py
│   ├── background_processing_service.py
│   ├── rag_service.py
│   ├── model_router.py
│   └── openrouter.py
│
├── database/
│   └── supabase.py
│
├── models/
│   └── domain.py
│
├── core/
│   ├── config.py
│   └── constants.py
│
├── prompts/
│   └── mentor_prompts.py
│
├── schema.sql
├── requirements.txt
└── vercel.json
```

---

# 🔄 System Architecture

```text
Student
   ↓
Authentication
   ↓
Student Profile
   ↓
Curriculum Context
   ↓
Mastery Tracking
   ↓
Behavioral Memory
   ↓
RAG Retrieval
   ↓
Model Router
   ↓
Mentor Agent
   ↓
Gemini/OpenRouter
   ↓
Response
```

---

# 🚀 API Endpoints

## Health

```http
GET /api/health
```

---

## Chat

```http
POST /api/chat
```

---

## Upload Documents

```http
POST /api/documents/upload
```

---

## Search Documents

```http
POST /api/documents/search
```

---

## Behavioral Analysis Webhook

```http
POST /api/webhook/analyze
```

---

# ⚙️ Environment Variables

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
OPENROUTER_API_KEY=

MODEL_FLASH_LITE=
MODEL_PRO=
MODEL_OVERRIDE=
```

---

# 🧪 Testing

Implemented test suites for:

* Authentication
* Curriculum Management
* Mastery Tracking
* Behavioral Memory
* Background Processing
* RAG
* Model Routing

Run tests:

```bash
python scratch/test_auth_ownership.py
python scratch/test_curriculum_flow.py
python scratch/test_mastery_flow.py
python scratch/test_behavioral_memory.py
python scratch/test_background_processing.py
python scratch/test_rag_flow.py
python scratch/test_model_router.py
```

---

# 🎓 Learning Objectives

This project demonstrates:

* FastAPI Development
* REST API Design
* Authentication & Authorization
* Retrieval-Augmented Generation (RAG)
* Vector Databases
* Embeddings
* AI Agents
* Prompt Engineering
* Background Processing
* Personalized Learning Systems
* Scalable Backend Architecture

---

# ⭐ Future Enhancements

* Advanced Analytics Dashboard
* Real-time Streaming Responses
* Multi-Agent Collaboration
* Learning Progress Visualizations
* Adaptive Assessment Generation
* Voice-based Learning Assistant

---
