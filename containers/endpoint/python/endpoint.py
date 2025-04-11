from fastapi import FastAPI
import numpy as np

app = FastAPI()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Sample Container API"}

@app.get("/compute")
async def compute(a: int, b: int, c: int):
    """Compute random numbers."""
    # Generate random arrays based on the input parameters
    array1 = np.random.rand(a, b)
    array2 = np.random.rand(b, c)
    array3 = np.random.rand(c, a)
    
    # Perform some computation
    array1 @ array2 @ array3
    
    # Return success
    return {"result": "Success"}