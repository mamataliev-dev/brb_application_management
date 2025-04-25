# 🚀 BRB Application Management

## 📋 Description
**BRB Application Management** is a project designed for automatic processing of applications via **StatimicAPI**, featuring secure authentication and role-based access control (RBAC) for Admins and Managers.

## ✨ Features
  * 🔄 Automatic application processing from StatimicAPI.
  * 🔐 Admin and Manager authentication with JWT.
  * 🛡️ Role-based access control (RBAC).
  * 🗄️ Integration with PostgreSQL and Redis.
  * 🛠️ Docker-ready for easy deployment.
  * 📚 API implemented with GraphQL.

---

## 🛠️ Tech Stack
- **Python**
- **Flask**
- **PostgreSQL**
- **Redis**
- **Docker**
- **GraphQL**
- **JWT Authentication**
- **Pytest**

---

## 🚀 Getting Started

### Prerequisites
Make sure you have installed:
- Python 3.9+
- PostgreSQL
- Redis
- Docker (optional, for containerization)

### Installation
Clone the repository:

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

Install the dependencies:

```python
pip install -r requirements.txt
```

Make sure PostgreSQL and Redis services are running.

Set up environment variables (example .env file):
```bash
FLASK_APP=run.py
FLASK_ENV=development
DATABASE_URL=postgresql://username:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your_jwt_secret_key
```

### Running the Project
```python
python run.py
```

### 🔐 Authentication
Authentication is implemented via JWT (JSON Web Tokens).
  * Admins and Managers authenticate via login endpoint.
  * Access to resources is controlled using Role-Based Access Control (RBAC).

