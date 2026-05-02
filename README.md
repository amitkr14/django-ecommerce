# 🛒 IndiaShop: High-Concurrency AI E-Commerce Platform

A scalable, production-ready backend architecture designed to handle high-traffic operations, featuring a custom **Machine Learning recommendation engine** and multi-tier caching[cite: 3]. This project focuses on data integrity, query optimization, and the practical application of AI in a backend environment[cite: 3].

## 🧠 Advanced Features & Architecture

### 1. 🤖 AI-Powered Recommendation Engine (Scikit-Learn)
Implemented a custom "Similar Items" feature using a **TF-IDF (Term Frequency-Inverse Document Frequency) Vectorizer** and **Cosine Similarity** matrix.
*   **Weighted Ranking**: Optimized the similarity math by weighting product titles over descriptions to ensure highly relevant matches (e.g., matching mice with mice).
*   **Disconnected Data Pipeline**: Built as a standalone Python module (`recommendations.py`) that performs heavy mathematical calculations without blocking the main web server.
*   **Result Caching**: Calculated similarity IDs are pushed to **Upstash Redis** for sub-millisecond retrieval on product detail pages.

### 2. ⚡ Multi-Tier Caching & Performance (Redis)
*   **Dynamic Search Caching**: Utilizes Upstash Redis to cache search queries and pagination results[cite: 3].
*   **Efficient Lookups**: Recommendation results bypass the primary PostgreSQL database entirely, fetching pre-calculated IDs directly from RAM to maintain high performance under load[cite: 3].

### 3. 🛡️ Concurrency Control & Data Integrity
*   **Race Condition Prevention**: Implemented PostgreSQL `select_for_update()` locks during checkout to prevent inventory overselling during high-traffic events[cite: 3].
*   **Atomic Transactions**: Integrated `transaction.atomic()` with the Razorpay API to ensure order status and payment verification stay perfectly in sync[cite: 3].

### 4. ⚙️ Asynchronous Task Management (Celery)
*   Offloaded time-intensive third-party network requests, such as generating payment receipts and sending customer emails, to background workers[cite: 3].

## 🚀 Tech Stack
*   **Backend**: Django, Django REST Framework (DRF)[cite: 3]
*   **Database**: PostgreSQL[cite: 3]
*   **In-Memory Store**: Upstash Redis (Cloud)[cite: 3]
*   **AI/ML**: Scikit-learn, Pandas
*   **Task Queue**: Celery[cite: 3]
*   **Payments**: Razorpay API[cite: 3]

## 🛠️ Setup & Maintenance

### Environment Management
This project uses `python-dotenv` to manage secrets and connection strings across different execution environments, ensuring standalone scripts can access secure configurations[cite: 1, 2].

### Rebuilding the AI Matrix
To integrate new products into the recommendation engine, run the following command to update the Redis similarity cache:
```bash
python -m myapp.recommendations