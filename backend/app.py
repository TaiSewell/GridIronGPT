from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"ok": True, "service": "backend"}

app.get("/meta/weeks")
def weeks_meta():
    return {"min_w": None, "max_w": None}