from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from agent import run_kmap_agent

app = FastAPI(
    title="Agentic AI K-Map Solver API",
    description="ESC392 Project P7 — Tool-Calling AI Agent for Karnaugh Map Minimization",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GridSolveRequest(BaseModel):
    num_vars: int = Field(default=4, ge=2, le=4)
    minterms: List[int] = Field(default_factory=list)
    dont_cares: List[int] = Field(default_factory=list)


class PromptSolveRequest(BaseModel):
    prompt: str = Field(..., min_length=3)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Agentic K-Map Solver"}


@app.post("/api/solve-grid")
def solve_from_grid(req: GridSolveRequest):
    try:
        return run_kmap_agent(
            num_vars=req.num_vars,
            minterms=req.minterms,
            dont_cares=req.dont_cares,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/solve-prompt")
def solve_from_prompt(req: PromptSolveRequest):
    try:
        return run_kmap_agent(user_prompt=req.prompt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)