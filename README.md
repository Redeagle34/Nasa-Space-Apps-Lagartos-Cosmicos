# 🚀 NASA Space Apps - Lagartos Cosmicos

A complete web application built with Docker, featuring a frontend, backend API,
and MongoDB database.

## 🏗️ Architecture

- **Frontend**: Static HTML/CSS/JS served by Nginx
- **Backend**: Node.js/Express API server
- **Database**: MongoDB for data storage
- **Containerization**: Docker with Docker Compose orchestration

## 📁 Project Structure

```
Nasa-Space-Apps-Lagartos-Cosmicos/
├── docker-compose.yaml          # Orchestrates all services
├── dockerfiles/
│   ├── frontend.dockerfile      # Frontend container
│   └── node.dockerfile         # Backend container (renamed from existing)
├── frontend/                   # Static web files
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── nginx.conf
├── backend/                    # Node.js API
│   ├── server.js
│   ├── package.json
│   └── .env
└── src/
    └── app.js                  # Original hello world file
```

## 🚀 Quick Start

### Prerequisites

- Docker Desktop installed and running
- Git (optional, for cloning)

### Running the Application

1. **Start all services**:

   ```bash
   docker-compose up --build
   ```

2. **Access the application**:

   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:3001
   - **Health Check**: http://localhost:3001/health
   - **MongoDB**: localhost:27017

3. **Stop all services**:
   ```bash
   docker-compose down
   ```

### Development Mode

For development with auto-reload:

```bash
docker-compose up --build -d
```

To view logs:

```bash
docker-compose logs -f
```

## 🔧 Services

### Frontend (Port 3000)

- Nginx-served static files
- Interactive web interface
- Communicates with backend API
- Add and view data from MongoDB

### Backend (Port 3001)

- Express.js REST API
- MongoDB integration with Mongoose
- CORS enabled for frontend communication
- Environment variable configuration

### MongoDB (Port 27017)

- Document database
- Persistent data storage
- Automatic database initialization

## 📡 API Endpoints

| Method | Endpoint        | Description       |
| ------ | --------------- | ----------------- |
| GET    | `/health`       | Health check      |
| GET    | `/api/data`     | Get all data      |
| POST   | `/api/data`     | Add new data      |
| GET    | `/api/data/:id` | Get data by ID    |
| DELETE | `/api/data/:id` | Delete data by ID |

## 🛠️ Customization

### Environment Variables

Backend environment variables (`.env`):

```env
PORT=3001
MONGODB_URI=mongodb://mongodb:27017/nasa_space_apps
NODE_ENV=development
```

### Ports Configuration

To change ports, update `docker-compose.yaml`:

```yaml
ports:
  - "YOUR_PORT:CONTAINER_PORT"
```

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**:

   ```bash
   docker-compose down
   # Change ports in docker-compose.yaml
   docker-compose up --build
   ```

2. **MongoDB connection issues**:

   ```bash
   docker-compose logs mongodb
   ```

3. **Build issues**:
   ```bash
   docker-compose build --no-cache
   ```

### Viewing Logs

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs frontend
docker-compose logs backend
docker-compose logs mongodb
```

## 🧪 Testing

1. Open http://localhost:3000
2. Fill in the form and submit data
3. Click "Load Data" to verify data is stored in MongoDB
4. Check backend health at http://localhost:3001/health

## 🏆 Features

- ✅ Multi-container Docker setup
- ✅ Frontend-Backend-Database integration
- ✅ RESTful API design
- ✅ Persistent data storage
- ✅ CORS configuration
- ✅ Error handling
- ✅ Development-friendly setup
- ✅ Production-ready containers

## 📦 Production Deployment

For production, consider:

- Using environment-specific compose files
- Setting up proper environment variables
- Implementing authentication
- Adding HTTPS/SSL
- Setting up monitoring and logging

---

Built for NASA Space Apps Challenge 🛰️
