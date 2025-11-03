# CRM Backend Optimization (Django + PostgreSQL)

A personal backend project inspired by real-world CRM systems.
It demonstrates large-scale data handling, query optimization, and benchmarking in Django with PostgreSQL.
The system models users, addresses, and loyalty relationships, focusing on efficient listing, searching, sorting, and pagination at scale.

---

## Project Purpose

This project was developed as a personal challenge to explore performance optimization in Django.
The focus is on modeling relational data efficiently, generating millions of records, and measuring the impact of query-level improvements.

---

## 1. Project Overview

**Tech Stack**
- Django 5.x
- PostgreSQL 17+
- Faker (for realistic randomized data generation)

**Core Features**
- Relational data model with 3 entities:
  - `AppUser` – customer details
  - `Address` – linked address
  - `CustomerRelationship` – loyalty and engagement metrics
- Management command to generate millions of rows efficiently using PostgreSQL `COPY FROM STDIN`
- API endpoint to:
  - Join all 3 tables
  - Support filtering, sorting, and pagination
  - Benchmark response times
- Benchmarks comparing baseline vs optimized versions

---

## 2. Project Structure

```
crm/
├── __init__.py
├── asgi.py
├── settings.py
├── urls.py
└── wsgi.py

core/
├── __init__.py
├── admin.py
├── api.py
├── apps.py
├── models.py
├── serializers.py
├── tests.py
├── urls.py
├── views.py
│
├── management/
│   └── commands/
│       ├── bench_list.py
│       └── generate_data.py
│
└── migrations/
    ├── 0001_initial.py
    ├── 0002_alter_address_city_alter_address_city_code_and_more.py
    └── __init__.py

reports/
└── benchmarks.csv

manage.py
requirements.txt
.gitignore
README.md
```

---

## 3. Setup & Local Development

### Step 1. Clone and Install

```bash
python -m venv .venv
.venv\Scripts\activate        # On Windows
# or
source .venv/bin/activate       # On macOS/Linux

pip install -r requirements.txt
```

### Step 2. Configure Database

In `crm/settings.py`:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "crmdb",
        "USER": "crmuser",
        "PASSWORD": "crmpass",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

Then run:

```bash
python manage.py migrate
```

---

## 4. Generate Sample Data

Efficient data generation via PostgreSQL `COPY FROM STDIN`.

**Quick test:**

```bash
python manage.py generate_data --n 100000 --chunk 50000
```

**Full-scale benchmark:**

```bash
python manage.py generate_data --n 3000000 --chunk 100000
```

This creates ~3 million `AppUser` rows (and corresponding addresses and relationships).
Each run overwrites the data safely via `TRUNCATE ... RESTART IDENTITY CASCADE`.

---

## 5. API and Benchmarking

**List & Search API**

All records joined across 3 tables, with filtering, sorting, and pagination.

Example requests:

```
/api/users/?page=1&page_size=50
/api/users/?last_name=smith
/api/users/?city=vienna&page=3
/api/users/?ordering=-relationship__points
```

---

**Benchmark Command**

Measure common queries with multiple repeats and export results to CSV:

```bash
python manage.py bench_list --repeat 5
```

Benchmarks are stored in `reports/benchmarks.csv`.

---

## 6. Benchmark Results (3M rows, page_size=50)

| Scenario                 | Baseline Avg (ms) | Optimized Avg (ms) | Best (ms) | Worst (ms) | Improvement |
|--------------------------|------------------:|-------------------:|----------:|-----------:|------------:|
| Initial page             | 178.4             | 149.1              | 122.7     | 256.3      | ~16% faster |
| Filter last_name=smith   | 152.3             | 132.0              | 121.5     | 171.5      | ~13% faster |
| Sort by points desc      | 145.6             | 127.8              | 121.9     | 155.0      | ~12% faster |
| City=Vienna + paginate   | 160.4             | 126.8              | 120.5     | 186.7      | ~21% faster |


Benchmarks were performed on **3,000,000 synthetic rows** using PostgreSQL 17 and page size 50.
Each scenario was executed **5 times** with `python manage.py bench_list --repeat 5`.

Average latency improvements range between **12–21%**, demonstrating the effect of:
- Indexing on common filter/sort fields
- Eliminating N+1 queries using `select_related`
- Efficient PostgreSQL COPY-based bulk inserts during data generation

---

## 7. Key Optimizations Implemented

- **Reduced N+1 queries** via `select_related("address", "relationship")`
- **Added indexes** for high-frequency filters and sorts:
  - `last_name`, `first_name`, `city`, `points`
  - Composite: `(customer_id, created DESC)`
- **Used PostgreSQL COPY** instead of ORM bulk inserts for faster data loading
- **Efficient pagination and filtering logic** in API view
- **Benchmarked using Django’s test client** for reproducibility

---

## 8. How to Run the Server

To start the Django development server:

```bash
python manage.py runserver
```

### API Endpoints

- **Main API endpoint (users):**
  [http://127.0.0.1:8000/api/users/](http://127.0.0.1:8000/api/users/)
- **Swagger UI:**
  [http://127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/)
- **OpenAPI JSON schema:**
  [http://127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/)

You can explore all available endpoints, filters, sorting options, and pagination parameters directly through the Swagger interface.

---

## 9. Author & License

**Ermis Chorinopoulos**
Vienna, Austria
[LinkedIn](https://www.linkedin.com/in/ermis-cho/)

This project is released under the MIT License.
Feel free to fork, explore, or adapt it for learning purposes.

---

### Notes for Reviewers

This implementation demonstrates:
- A realistic data scale (millions of rows)
- Measurable and documented performance improvement
- A maintainable Django architecture ready for production-like conditions
