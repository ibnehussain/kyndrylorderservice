# Security Middleware Documentation

## Overview

This FastAPI application implements comprehensive security middleware for production deployment, including:

1. **CORS (Cross-Origin Resource Sharing)** - Controls which domains can access the API
2. **Rate Limiting** - Prevents API abuse by limiting request rates
3. **Security Headers** - Adds industry-standard HTTP security headers
4. **Request Validation** - Validates incoming requests for size and content type

## Configuration

All security settings are managed through environment variables in the `.env` file or through the `Settings` class in `app/core/config.py`.

### Environment Variables

```bash
# CORS Settings
ALLOWED_HOSTS=["http://localhost:3000", "https://yourdomain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT="100/minute"
RATE_LIMIT_STRICT="10/minute"

# Request Validation
MAX_REQUEST_SIZE=10485760  # 10MB in bytes

# Security Headers
ENABLE_SECURITY_HEADERS=true
```

## Security Features

### 1. CORS Configuration

The CORS middleware is configured to:
- Accept requests from domains specified in `ALLOWED_HOSTS`
- Allow credentials (cookies, authorization headers)
- Support explicit HTTP methods: GET, POST, PUT, DELETE, PATCH
- Cache preflight requests for 10 minutes (max_age=600)

**Production Recommendation:**
```python
# In .env file
ALLOWED_HOSTS=["https://yourdomain.com", "https://app.yourdomain.com"]
```

**Development (default):**
```python
ALLOWED_HOSTS=["*"]  # Allows all origins - NOT recommended for production
```

### 2. Rate Limiting

Rate limiting is implemented using the `slowapi` library and prevents API abuse.

**Features:**
- Default rate limit: 100 requests per minute per IP address
- Strict rate limit: 10 requests per minute (for sensitive endpoints)
- Automatic rate limit headers in responses
- Returns 429 status code when limit is exceeded

**Usage:**

The rate limiter is applied to endpoints using decorators:

```python
from app.main import limiter
from fastapi import Request

@app.get("/endpoint")
@limiter.limit("100/minute")
async def endpoint(request: Request):
    return {"data": "response"}

# For stricter limits on sensitive endpoints
@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request):
    return {"token": "..."}
```

**Configuration:**
- `RATE_LIMIT_DEFAULT`: Default rate limit applied to all endpoints
- `RATE_LIMIT_STRICT`: Stricter limit for authentication/critical endpoints
- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (boolean)

### 3. Security Headers Middleware

The `SecurityHeadersMiddleware` adds the following HTTP security headers to all responses:

#### X-Content-Type-Options: nosniff
Prevents browsers from MIME-sniffing responses, reducing XSS risks.

#### X-Frame-Options: DENY
Prevents the application from being embedded in iframes, protecting against clickjacking attacks.

#### X-XSS-Protection: 1; mode=block
Enables browser XSS protection and blocks the page if an attack is detected.

#### Strict-Transport-Security: max-age=31536000; includeSubDomains
Forces HTTPS connections for 1 year, including all subdomains.

#### Content-Security-Policy
Defines which content sources are allowed to be loaded:
- `default-src 'self'`: Only load resources from the same origin by default
- `script-src 'self' 'unsafe-inline'`: Allow inline scripts (customize for your needs)
- `style-src 'self' 'unsafe-inline'`: Allow inline styles
- `img-src 'self' data: https:`: Allow images from same origin, data URIs, and HTTPS
- `connect-src 'self'`: Only connect to same origin for AJAX/WebSocket
- `frame-ancestors 'none'`: Prevent embedding (similar to X-Frame-Options)

**Customization:**

Edit `app/middleware/security.py` to customize the CSP policy for your needs:

```python
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://trusted-cdn.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    # ... customize other directives
)
```

#### Referrer-Policy: strict-origin-when-cross-origin
Controls how much referrer information is sent with requests.

#### Permissions-Policy
Disables unnecessary browser features:
- Geolocation
- Microphone
- Camera
- Payment APIs

### 4. Request Validation Middleware

The `RequestValidationMiddleware` validates incoming requests for:

#### Request Size Limits
- Default maximum: 10MB (configurable via `MAX_REQUEST_SIZE`)
- Returns `413 Request Entity Too Large` if exceeded
- Checks the `Content-Length` header before processing

#### Content-Type Validation
- Validates Content-Type header for POST/PUT/PATCH requests
- Allowed content types:
  - `application/json`
  - `application/x-www-form-urlencoded`
  - `multipart/form-data`
- Returns `415 Unsupported Media Type` if invalid
- GET/DELETE requests bypass content-type validation

## Middleware Order

Middleware is applied in a specific order for optimal security:

1. **Rate Limiting** - Reject excessive requests early
2. **Security Headers** - Ensure all responses have security headers
3. **Request Validation** - Validate request size and content-type
4. **CORS** - Handle cross-origin requests

This order is defined in `app/main.py`:

```python
# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers
if settings.enable_security_headers:
    app.add_middleware(SecurityHeadersMiddleware)

# Add request validation
app.add_middleware(RequestValidationMiddleware, max_request_size=settings.max_request_size)

# Add CORS
app.add_middleware(CORSMiddleware, ...)
```

## Testing

The security middleware includes comprehensive tests:

### Run Security Tests

```bash
# Run all tests
pytest tests/unit/test_security_middleware.py -v
pytest tests/unit/test_main_security.py -v

# Run specific test class
pytest tests/unit/test_security_middleware.py::TestSecurityHeadersMiddleware -v
pytest tests/unit/test_security_middleware.py::TestRequestValidationMiddleware -v
```

### Manual Testing

Test security headers with curl:

```bash
# Test security headers
curl -I http://localhost:8000/

# Test rate limiting (make multiple rapid requests)
for i in {1..110}; do curl http://localhost:8000/; done

# Test request size limit
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -H "Content-Length: 99999999" \
  -d '{"test": "data"}'

# Test invalid content-type
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: text/plain" \
  -H "Content-Length: 10" \
  -d 'plain text'
```

## Production Deployment Checklist

Before deploying to production, ensure:

- [ ] Update `ALLOWED_HOSTS` to specific domains (not `["*"]`)
- [ ] Set `DEBUG=false` in environment
- [ ] Configure appropriate rate limits for your use case
- [ ] Review and customize Content-Security-Policy for your frontend
- [ ] Enable HTTPS/TLS at the reverse proxy/load balancer level
- [ ] Set `SECRET_KEY` to a strong, random value
- [ ] Configure logging and monitoring for rate limit violations
- [ ] Test all security features in a staging environment
- [ ] Review CORS settings to ensure minimum necessary access
- [ ] Consider adding additional security measures:
  - API key authentication
  - JWT token validation
  - Request signing
  - IP allowlisting for admin endpoints

## Example Production Configuration

```env
# .env for production

# Application
APP_NAME="Order Management Service"
DEBUG=false

# Security
SECRET_KEY="your-very-secure-random-secret-key-here"

# CORS
ALLOWED_HOSTS=["https://yourdomain.com", "https://app.yourdomain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT="100/minute"
RATE_LIMIT_STRICT="10/minute"

# Request Validation
MAX_REQUEST_SIZE=10485760  # 10MB

# Security Headers
ENABLE_SECURITY_HEADERS=true

# Database
COSMOS_ENDPOINT="https://your-cosmos-account.documents.azure.com:443/"
COSMOS_KEY="your-cosmos-key"
```

## Troubleshooting

### Rate Limit Too Restrictive

If legitimate users are hitting rate limits:

1. Increase the rate limit in configuration
2. Implement authenticated rate limiting (higher limits for authenticated users)
3. Use Redis for distributed rate limiting across multiple servers

### CORS Errors in Browser

If you see CORS errors in the browser console:

1. Verify the origin is in `ALLOWED_HOSTS`
2. Check that the HTTP method is allowed
3. Ensure `allow_credentials=True` if sending cookies
4. For development, temporarily set `ALLOWED_HOSTS=["*"]` to debug

### Content-Type Validation Blocking Requests

If legitimate requests are being blocked:

1. Verify the Content-Type header is set correctly
2. Check that the content type is in the allowed list
3. Modify `app/middleware/security.py` to add additional content types if needed

### Security Headers Conflicting with Frontend

If security headers cause issues with your frontend:

1. Customize the Content-Security-Policy to allow your CDN/resources
2. Adjust frame-ancestors if you need to embed the app
3. Consider relaxing `'unsafe-inline'` restrictions once you've implemented CSP-compliant code

## Security Best Practices

1. **Keep Dependencies Updated**: Regularly update FastAPI, Starlette, and security libraries
2. **Use HTTPS**: Always use HTTPS in production (configured at load balancer/reverse proxy)
3. **Monitor Rate Limits**: Set up alerts for rate limit violations
4. **Audit Logs**: Log security events (rate limit hits, validation failures)
5. **Regular Security Audits**: Periodically review and update security settings
6. **Defense in Depth**: Use multiple layers of security (middleware + WAF + network security)
7. **Principle of Least Privilege**: Only allow what's necessary (CORS origins, methods, etc.)

## References

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [FastAPI Security Guide](https://fastapi.tiangolo.com/tutorial/security/)
- [Content Security Policy Reference](https://content-security-policy.com/)
- [CORS Best Practices](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [SlowAPI Documentation](https://slowapi.readthedocs.io/)
