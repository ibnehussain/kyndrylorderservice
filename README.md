# Order Management Service

A production-ready RESTful API service for managing customer orders, built with FastAPI, Azure Cosmos DB, and following enterprise best practices.

## 🚀 Features

- **RESTful API** - Complete CRUD operations for orders
- **Azure Cosmos DB Integration** - Scalable NoSQL database with global distribution
- **Data Validation** - Comprehensive input validation using Pydantic
- **Async Support** - High-performance async/await patterns
- **Auto-Documentation** - Interactive API docs with Swagger/OpenAPI
- **Production Ready** - Logging, error handling, health checks
- **Test Coverage** - Comprehensive unit tests with pytest
- **Docker Support** - Containerized deployment
- **Type Safety** - Full type hints with mypy validation
- **📈 Order Analytics** - Daily revenue, order count, and business metrics
- **📊 Analytics API** - Comprehensive reporting and dashboard endpoints
- **📋 Business Intelligence** - Customer insights, trends, and growth metrics

## 🏗️ Architecture

```
📁 app/
├── 🎯 api/v1/endpoints/     # API endpoints
├── 🔧 core/                # Configuration & settings  
├── 🗃️ models/              # Data models (Pydantic)
├── 📋 schemas/             # Request/Response schemas
├── 🏪 repositories/        # Data access layer
├── 🎪 services/           # Business logic layer
└── 📄 main.py             # FastAPI application

📁 tests/
├── 🧪 unit/               # Unit tests
└── 📋 conftest.py         # Test configuration
```

## 🛠️ Technology Stack

- **API Framework**: FastAPI 0.104.1
- **Database**: Azure Cosmos DB (NoSQL)
- **Validation**: Pydantic 2.5.0
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: black, isort, mypy, flake8
- **Deployment**: Docker + Docker Compose

## 🚦 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd endtoendapp

# Copy environment template
cp .env.example .env
```

### 2. Install Dependencies

**Option A: Using pip**
```bash
pip install -r requirements.txt
```

**Option B: Using Poetry**
```bash
poetry install
poetry shell
```

### 3. Start Cosmos DB Emulator (Local Development)

```bash
# Using Docker Compose (recommended)
docker-compose up cosmos-emulator -d

# Or install Azure Cosmos DB Emulator locally
# Download from: https://aka.ms/cosmosdb-emulator
```

### 4. Run the Service

```bash
# Development mode
uvicorn app.main:app --reload --port 8000

# Or using Docker Compose
docker-compose up order-service
```

### 5. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔗 API Endpoints

### Orders Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/orders/` | Create a new order |
| `GET` | `/api/v1/orders/` | List orders (paginated) |
| `GET` | `/api/v1/orders/{order_id}` | Get order by ID |
| `PUT` | `/api/v1/orders/{order_id}` | Update order |
| `DELETE` | `/api/v1/orders/{order_id}` | Delete order |
| `POST` | `/api/v1/orders/{order_id}/cancel` | Cancel order |
| `GET` | `/api/v1/orders/number/{order_number}` | Get order by number |
| `GET` | `/api/v1/orders/customers/{customer_id}/orders` | Get customer orders |

### Analytics & Reporting

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/analytics/daily` | Daily order metrics and revenue |
| `GET` | `/api/v1/analytics/orders/status` | Order metrics by status |
| `GET` | `/api/v1/analytics/customers/top` | Top customers by spending |
| `GET` | `/api/v1/analytics/summary` | Comprehensive analytics dashboard |
| `GET` | `/api/v1/analytics/revenue/trends` | Revenue trends over time |
| `GET` | `/api/v1/analytics/customers/{customer_id}` | Individual customer analytics |
| `GET` | `/api/v1/analytics/quick/today` | Today's analytics |
| `GET` | `/api/v1/analytics/quick/week` | Last 7 days analytics |
| `GET` | `/api/v1/analytics/quick/month` | Current month summary |

### System Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Basic health check |
| `GET` | `/api/v1/health/ready` | Readiness probe |
| `GET` | `/api/v1/health/live` | Liveness probe |

## 📋 Sample API Usage

### Create Order

```bash
curl -X POST "http://localhost:8000/api/v1/orders/" \
-H "Content-Type: application/json" \
-d '{
  "customer_id": "cust_123",
  "customer_email": "john.doe@example.com",
  "items": [
    {
      "product_id": "prod_456",
      "product_name": "Premium Widget",
      "quantity": 2,
      "unit_price": 29.99
    }
  ],
  "billing_address": {
    "street": "123 Main St",
    "city": "Seattle",
    "state": "WA",
    "postal_code": "98101",
    "country": "US"
  },
  "payment_info": {
    "method": "credit_card",
    "last_four_digits": "1234"
  },
  "tax_amount": 5.99,
  "shipping_amount": 9.99
}'
```

### List Orders

```bash
curl "http://localhost:8000/api/v1/orders/?customer_id=cust_123&page=1&page_size=10"
```

### Get Order

```bash
curl "http://localhost:8000/api/v1/orders/order_789?customer_id=cust_123"
```

### Get Analytics

```bash
# Daily analytics for last 30 days
curl "http://localhost:8000/api/v1/analytics/daily"

# Order status breakdown
curl "http://localhost:8000/api/v1/analytics/orders/status?start_date=2026-01-01&end_date=2026-01-31"

# Top customers
curl "http://localhost:8000/api/v1/analytics/customers/top?limit=10"

# Analytics summary with growth metrics
curl "http://localhost:8000/api/v1/analytics/summary"

# Revenue trends
curl "http://localhost:8000/api/v1/analytics/revenue/trends?days=7"

# Customer analytics
curl "http://localhost:8000/api/v1/analytics/customers/cust_123"
```

## 🧪 Testing

### Run All Tests

```bash
# Using pytest
pytest

# With coverage report  
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_order_service.py -v

# Run analytics tests
pytest tests/unit/test_analytics_service.py -v

# Run API tests
pytest tests/unit/test_analytics_api.py -v
```

### Code Quality Checks

```bash
# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t order-management-service .

# Run with docker-compose (includes Cosmos DB emulator)
docker-compose up

# Production deployment
docker-compose -f docker-compose.prod.yml up
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `COSMOS_ENDPOINT` | Azure Cosmos DB endpoint URL | `https://localhost:8081` |
| `COSMOS_KEY` | Azure Cosmos DB primary key | Emulator key |
| `COSMOS_DATABASE` | Database name | `OrderManagement` |
| `COSMOS_CONTAINER` | Container name | `Orders` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Azure Cosmos DB Setup

**For Production:**
1. Create Azure Cosmos DB account
2. Get connection string from Azure portal
3. Set `COSMOS_ENDPOINT` and `COSMOS_KEY` environment variables

**For Development:**
- Use included Cosmos DB emulator in docker-compose.yml
- Default emulator settings are pre-configured

## 📊 Analytics Features

### Daily Revenue Analytics
- **Daily Metrics**: Order count, total revenue, average order value
- **Period Comparisons**: Growth rates vs previous periods
- **Trend Analysis**: Revenue trends over time with gap filling for missing days
- **Currency Support**: Multi-currency analytics with USD as default

### Customer Intelligence  
- **Top Customers**: Ranked by total spending with order history
- **Customer Lifetime Value**: Total spent, order frequency, date ranges
- **Customer Segmentation**: Analytics for individual customer performance

### Business Insights
- **Order Status Breakdown**: Distribution of orders by status with percentages
- **Performance Metrics**: Busiest days, highest revenue days
- **Growth Analytics**: Period-over-period growth calculations
- **Summary Dashboards**: Comprehensive analytics overview

### Quick Analytics Endpoints
- **Today's Performance**: Real-time daily metrics
- **Weekly Trends**: Last 7 days analysis
- **Monthly Overview**: Current month comprehensive summary

## 📋 Analytics API Examples

### Daily Revenue Report

```json
{
  "metrics": [
    {
      "date": "2026-01-21", 
      "order_count": 15,
      "total_revenue": 1500.00,
      "average_order_value": 100.00,
      "currency": "USD"
    }
  ],
  "period_summary": {
    "period_start": "2026-01-01",
    "period_end": "2026-01-21", 
    "total_revenue": 25000.00,
    "total_orders": 250,
    "average_order_value": 100.00
  },
  "total_days": 21
}
```

### Customer Analytics Response

```json
{
  "customer_id": "cust_123",
  "customer_email": "customer@example.com", 
  "total_orders": 12,
  "total_spent": 1200.00,
  "average_order_value": 100.00,
  "first_order_date": "2025-06-15T10:00:00Z",
  "last_order_date": "2026-01-15T14:30:00Z"
}
```

### Order Structure

```json
{
  "id": "order_789",
  "order_number": "ORD-20260121-ABC123",
  "customer_id": "cust_456",
  "customer_email": "customer@example.com",
  "status": "pending",
  "items": [
    {
      "product_id": "prod_123",
      "product_name": "Premium Widget",
      "quantity": 2,
      "unit_price": 29.99,
      "total_price": 59.98
    }
  ],
  "subtotal": 59.98,
  "tax_amount": 5.99,
  "shipping_amount": 9.99,
  "discount_amount": 0.00,
  "total_amount": 75.96,
  "currency": "USD",
  "billing_address": { "street": "123 Main St", "city": "Seattle", "state": "WA", "postal_code": "98101" },
  "payment_info": { "method": "credit_card", "status": "pending", "last_four_digits": "1234" },
  "created_at": "2026-01-21T10:00:00Z",
  "updated_at": null
}
```

## 🔒 Security Features

This application implements comprehensive security middleware for production deployment:

- **CORS Configuration**: Configurable cross-origin resource sharing with explicit methods
- **Rate Limiting**: IP-based rate limiting to prevent API abuse (100 req/min default)
- **Security Headers**: Industry-standard HTTP security headers
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: DENY
  - X-XSS-Protection: 1; mode=block
  - Strict-Transport-Security with HSTS
  - Content-Security-Policy (CSP)
  - Referrer-Policy
  - Permissions-Policy
- **Request Validation**: Size limits (10MB default) and content-type validation
- **Input Validation**: Comprehensive validation with Pydantic
- **Data Sanitization**: Protection against injection attacks
- **Error Handling**: Secure error responses without data leakage
- **Health Checks**: Kubernetes-ready liveness/readiness probes

📖 **See [Security Documentation](docs/SECURITY.md) for detailed configuration and best practices**

## 📈 Monitoring & Observability

- **Health Endpoints**: `/health`, `/api/v1/health/ready`, `/api/v1/health/live`
- **Structured Logging**: JSON formatted logs for production
- **Error Tracking**: Comprehensive exception handling
- **Metrics Ready**: Prepared for Prometheus integration

## 🚀 Production Deployment

### Recommended Infrastructure

- **Compute**: Azure Container Instances or Azure Kubernetes Service
- **Database**: Azure Cosmos DB with auto-scaling
- **Monitoring**: Azure Application Insights
- **Load Balancer**: Azure Application Gateway
- **CI/CD**: GitHub Actions (see `.github/workflows/`)

### Environment Setup

1. **Azure Cosmos DB**: Create account with global distribution
2. **Container Registry**: Push Docker images to Azure Container Registry
3. **Application Gateway**: Configure load balancing and SSL termination
4. **Monitoring**: Set up Application Insights and alerts

## 🤝 Contributing

1. **Code Style**: Follow Black formatting and isort import sorting
2. **Type Hints**: All functions must have type annotations
3. **Testing**: Maintain >90% test coverage
4. **Documentation**: Update README for any API changes
5. **Commits**: Use conventional commit messages

### Development Workflow

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black app/ tests/
isort app/ tests/

# Type check
mypy app/

# Commit changes
git add .
git commit -m "feat: add order cancellation endpoint"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- 📧 Email: support@orderservice.com  
- 📚 Documentation: [API Docs](http://localhost:8000/docs)
- 🐛 Issues: GitHub Issues tab
- 💬 Discussions: GitHub Discussions tab

