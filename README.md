<div align="center">

# 🌟 Intelligent AI Assistant Platform

**A powerful, multi-frontend architecture powered by a Machine Learning FastAPI backend.**

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![PHP](https://img.shields.io/badge/PHP-777BB4?style=for-the-badge&logo=php&logoColor=white)](https://www.php.net/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)

---

</div>

## 📖 Overview

Welcome to the **Intelligent AI Assistant Platform**. This project is built using a modern, decoupled architecture designed for scalability and ease of use. It features a robust Python/FastAPI backend that handles natural language processing (NLP) and machine learning tasks, accompanied by two distinct frontends: a modern Next.js interface and a versatile PHP interface.

<br>

## 📂 Project Architecture

The repository is organized into distinct, modular components:

| Component | Directory | Description |
| :--- | :--- | :--- |
| **🧠 Backend** | `backend/` | FastAPI server handling ML pipelines (TF-IDF + Logistic Regression) and API endpoints. |
| **⚛️ React UI** | `frontend/` | Next.js application for a seamless, modern, and reactive user experience. |
| **🐘 PHP UI** | `php_frontend/` | Classic PHP-based frontend interface for lightweight deployment. |

<br>

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed on your machine:
*   <img src="https://upload.wikimedia.org/wikipedia/commons/d/d9/Node.js_logo.svg" width="20" align="top" /> **Node.js** (v18.0+)
*   <img src="https://upload.wikimedia.org/wikipedia/commons/c/c3/Python-logo-notext.svg" width="20" align="top" /> **Python** (v3.9+)
*   <img src="https://upload.wikimedia.org/wikipedia/commons/2/27/PHP-logo.svg" width="20" align="top" /> **PHP** (Optional, for the PHP frontend)

---

## 🚀 Quick Start Guide

### 1️⃣ Backend Setup (FastAPI & ML)

The backend powers the intelligence of the application. It runs the machine learning models and serves the `/predict` API.

<details>
<summary><b>Click to view Backend Setup Instructions</b></summary>

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Start the FastAPI development server
uvicorn main:app --reload --port 8000
```
> 🔗 API Server: `http://localhost:8000`  
> 📚 Swagger Docs: `http://localhost:8000/docs`

</details>

<details>
<summary><b>🤖 Model Training & Testing</b></summary>

*   **Train:** Run `python train.py` to ingest JSON training data, train the TF-IDF and Logistic Regression pipeline, and generate `model.pkl`.
*   **Test:** Run `python test_model.py` to run sample queries locally and view confidence scores.
</details>

<br>

### 2️⃣ Frontend Setup (Next.js)

A lightning-fast, reactive user interface for interacting with the AI.

<details>
<summary><b>Click to view Next.js Setup Instructions</b></summary>

```bash
# 1. Open a new terminal and navigate to the frontend
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Next.js development server
npm run dev
```
> 🌐 Web App: `http://localhost:3000`

</details>

<br>

### 3️⃣ PHP Frontend Setup (Alternative UI)

An alternative, lightweight frontend implementation.

<details>
<summary><b>Click to view PHP Setup Instructions</b></summary>

```bash
# 1. Open a new terminal and navigate to the PHP frontend
cd php_frontend

# 2. Start the built-in PHP development server
php -S localhost:8080
```
> 🌐 Web App: `http://localhost:8080`

</details>

---

## 💡 Important Notes

> [!IMPORTANT]
> The **FastAPI backend** must be actively running before starting either frontend, as the UIs rely on the backend API for intelligence.

> [!TIP]
> **API Proxying:** In the Next.js application, requests made to `/api/chat` are automatically proxied to the backend's `/predict` endpoint to prevent CORS issues.

> [!NOTE]
> **Fallback System:** If the AI receives an out-of-domain or low-confidence query, it gracefully degrades and returns a pre-configured, safe fallback response.

<br>

<div align="center">
  <i>Built with ❤️ using Modern Web Technologies</i>
</div>
