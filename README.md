#  StreamSync — Real-Time Dynamic Pricing Engine

##  Overview

This project is a **full-stack web application** that dynamically changes the price of e-commerce products in real time based on how many users are viewing or adding them to cart.

It uses a **Redis Streams pipeline** to process user events continuously, and a pricing engine that automatically increases or decreases product prices based on demand — just like how Flipkart or Amazon pricing works.

---

##  Features

*  Real-time price updates based on user demand
*  Redis Streams for live event processing
*  REST API built with FastAPI
*  Pricing guardrails so prices don't go too high or too low
*  Live dashboard showing p99 latency, repricing rate, stream lag
*  Product listing, detail page, and cart
*  Works even without backend (frontend has mock data fallback)
*  Can run fully locally — no Redis installation needed
*  Docker support for full deployment

---

##  Tech Stack

**Backend**
* Python 3.11
* FastAPI
* Uvicorn
* Redis / fakeredis (for local testing)
* XGBoost
* Sentence Transformers
* Pandas
* NumPy
* Pydantic

**Frontend**
* React 18
* Vite
* Tailwind CSS
* React Router v6
* Axios
* Recharts
* Framer Motion
* Lucide React

**Other Tools**
* Docker & Docker Compose
* Redis 7

---

##  System Architecture

```
        ┌──────────────────────┐
        │      User (Browser)  │
        │   React Frontend     │
        └─────────┬────────────┘
                  │
                  ▼
        ┌──────────────────────┐
        │  Frontend (React)    │
        │  - Browse Products   │
        │  - Add to Cart       │
        │  - View Dashboard    │
        └─────────┬────────────┘
                  │  HTTP Request (/api/*)
                  ▼
        ┌──────────────────────┐
        │   FastAPI Backend    │
        │     (main.py)        │
        │ - Products API       │
        │ - Signal Ingestion   │
        │ - Analytics API      │
        └────────┬─────────────┘
                 │
       ┌─────────┴──────────┐
       ▼                    ▼
┌─────────────────┐  ┌──────────────────────┐
│  Redis Stream   │  │   data_producer.py   │
│ingestion_stream │◄─│  Sends fake VIEW /   │
│                 │  │  ADD_TO_CART events  │
└───────┬─────────┘  └──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  stream_consumer.py  │
│  - Reads events      │
│  - Updates velocity  │
│  - Triggers reprice  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Pricing Engine     │
│  pricing_model.py    │
│  + guardrails.py     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Price updated in    │
│  Redis + event log   │
└──────────────────────┘
```

---

##  Project Structure

```
StreamSync-main/
│
├── docker-compose.yml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # FastAPI app
│   ├── run_all.py               # Run everything locally in one command
│   │
│   ├── api/
│   │   ├── middleware/
│   │   │   └── monitor.py       # Tracks request latency
│   │   └── routes/
│   │       ├── products.py
│   │       ├── pricing.py
│   │       ├── analytics.py
│   │       └── ml_admin.py      # Protected route (needs API key)
│   │
│   ├── db/
│   │   ├── redis_client.py
│   │   └── mock_db.py           # Seeds 20 fake products into Redis
│   │
│   ├── engine/
│   │   ├── pricing_model.py     # Core repricing logic
│   │   ├── recommender.py       # Product recommendations
│   │   └── guardrails.py        # Price floor & ceiling rules
│   │
│   ├── workers/
│   │   ├── data_producer.py     # Simulates user traffic
│   │   └── stream_consumer.py   # Processes events from Redis stream
│   │
│   └── models/
│       └── pricing_v1.pkl
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    │
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── components/
        │   ├── Navbar.jsx
        │   ├── Footer.jsx
        │   ├── Layout.jsx
        │   ├── ProductCard.jsx
        │   └── Loader.jsx
        ├── context/
        │   └── CartContext.jsx
        ├── hooks/
        │   ├── useCart.js
        │   ├── useFetch.js
        │   └── useDebounce.js
        ├── pages/
        │   ├── Home.jsx
        │   ├── Products.jsx
        │   ├── ProductDetails.jsx
        │   ├── Cart.jsx
        │   └── Dashboard.jsx
        └── services/
            └── api.js
```

---

##  Installation & Setup

### Method 1 — Run Locally (Easiest, No Redis Needed)

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/StreamSync.git
```

#### 2. Go into the Project Folder

```bash
cd StreamSync-main
```

#### 3. Create Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
```

#### 4. Activate It

* Windows:

```bash
venv\Scripts\activate
```

* Mac/Linux:

```bash
source venv/bin/activate
```

#### 5. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### 6. Start the Backend

```bash
python run_all.py
```

> This one command does everything — seeds fake product data, starts the event producer, starts the stream consumer, and runs the API. It uses fakeredis internally so you don't need Redis installed at all.

#### 7. Open a New Terminal and Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

#### 8. Open in Browser

```
http://localhost:5173
```

---

### Method 2 — Docker Compose

#### 1. Make Sure Docker is Running, then:

```bash
docker-compose up --build
```

#### 2. API will be live at:

```
http://localhost:8000
```

> Note: Frontend is not included in Docker Compose, so still run `npm run dev` separately for the UI.

---

##  Environment Variables

| Variable     | Default                   | What it does                                      |
|--------------|---------------------------|---------------------------------------------------|
| `REDIS_URL`  | Not needed locally        | Redis URL — Docker sets this automatically        |
| `ML_API_KEY` | `ml-dev-secret-key-12345` | Key to access the protected `/api/ml-admin` route |

---

##  API Endpoints

| Method | Endpoint                        | Description                                    |
|--------|---------------------------------|------------------------------------------------|
| GET    | `/api/products`                 | Get all products                               |
| GET    | `/api/products/{id}`            | Get one product by ID                          |
| GET    | `/api/recommendations`          | Get recommended products                       |
| POST   | `/api/signals`                  | Send a user event (VIEW / ADD_TO_CART)         |
| GET    | `/api/metrics`                  | Dashboard stats (p99, reprice rate, lag)       |
| GET    | `/api/metrics/demand-velocity`  | Demand history chart data                      |
| GET    | `/api/metrics/repricing-events` | Recent repricing events                        |
| GET    | `/api/ml-admin/raw-stream`      | Raw stream data *(needs X-API-Key header)*     |

---

##  Frontend Scripts

| Script  | Command            | What it does                      |
|---------|--------------------|-----------------------------------|
| Dev     | `npm run dev`      | Start dev server on port 5173     |
| Build   | `npm run build`    | Build for production              |
| Preview | `npm run preview`  | Preview the production build      |

---

##  How the Pricing Logic Works

* Every time a user **views** or **adds to cart**, an event goes into the Redis Stream
* The stream consumer reads these events and updates the product's **demand velocity** (a score from 0–100)
* Based on velocity, the pricing engine decides:

  * Velocity **> 75** → Price goes **up by 2% to 8%** (high demand)
  * Velocity **< 30** → Price goes **down by 1% to 5%** (low demand)
  * Otherwise → Small random fluctuation (±1%)

* **Guardrails make sure prices stay within a safe range:**

  * Minimum: 85% of original base price
  * Maximum: 150% of original base price

---

##  Notes

* The XGBoost model and Sentence Transformers are included as dependencies but currently use simulation logic — they can be swapped in for a real trained model
* `fakeredis` is used locally so the entire app runs in-memory without any external setup
* The frontend never crashes even if the backend is down — it just falls back to mock data automatically
