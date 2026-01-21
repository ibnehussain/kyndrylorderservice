"""Simple FastAPI app for testing without complex models"""

from fastapi import FastAPI

app = FastAPI(
    title="Order Management Service - Simple Version",
    description="Simple test version without complex models",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "service": "Order Management Service", 
        "version": "1.0.0",
        "status": "healthy",
        "message": "Simple version running successfully!"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "order-management"}

@app.get("/test")
async def test():
    return {"message": "Test endpoint working", "data": [1, 2, 3]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("simple_app:app", host="127.0.0.1", port=8000, reload=True)