# 🛠️ ETL Pipeline with Apache Airflow and Docker: AWS RDS ➡️ On-Prem PostgreSQL

This project is an automated **ETL pipeline** using **Apache Airflow** to fetch data from an **AWS RDS (PostgreSQL)** instance and ingest it into an **on-premise PostgreSQL** database.

---

## 🧰 Tech Stack

- **Apache Airflow** – Workflow orchestration
- **AWS RDS (PostgreSQL)** – Source database
- **On-Prem PostgreSQL** – Destination database
- **Pandas** – Data manipulation
- **Python** – Core ETL logic
- **Docker** – Containerized development setup
- **YAML** – Configuration-driven execution

---

## ⚙️ How It Works

1. The Airflow DAG reads a list of tables to migrate from a YAML config file.
2. For each table:
   - Connects to **AWS RDS** using credentials/SSH (if needed).
   - Fetches data incrementally or fully.
   - Cleans/transforms the data using **Pandas**.
   - Inserts the data into **on-premise PostgreSQL**.
3. All logs are viewable via Airflow UI.

---
## 1. Clone the repository
```bash
git clone https://github.com/your-username/etl-airflow-pipeline.git
cd etl-airflow-pipeline
```
---
## ⚙️ Add your credentials in the .env file as 

# Source: AWS RDS
RDS_HOST=your-rds-host.amazonaws.com
RDS_PORT=5432
RDS_DB=source_db
RDS_USER=your_user
RDS_PASSWORD=your_password

# Destination: On-Prem PostgreSQL
ONPREM_HOST=host.docker.internal
ONPREM_PORT=5432
ONPREM_DB=target_db
ONPREM_USER=postgres
ONPREM_PASSWORD=postgres

--- 
## Start service 

docker-compose up -d


---

Let me know if you'd like help creating:
- A sample `config.yaml`
- `.env` template
- `requirements.txt` or `.gitignore`
- Diagram of the data flow (RDS → Airflow → On-Prem)

Happy to assist!


❤️ Made with love by Deepu
This project was designed and built with care, passion, and a lot of debugging 😅


