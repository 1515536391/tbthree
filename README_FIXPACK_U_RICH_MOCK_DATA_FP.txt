Fixpack U - Rich mock data (frontend FP alignment)

What this fixes
- Frontend expects fixed-point values scaled by 1e6 (FP=1_000_000) for:
  - edge.score
  - edge.hmmProbT / hmmProbS / hmmProbM
  - edge.b / edge.d / edge.u
- Previous fixpacks used total=1000 and/or different HMM field names, which makes the UI show lots of 0.00.

This fixpack updates backend/app/mock_data.py so:
- b/d/u and HMM are generated in FP=1e6 units
- HMM keys match frontend: hmmProbT / hmmProbS / hmmProbM
- Scores and probabilities are more varied (so charts look better)

How to apply
1) From your repo root (the folder that contains the 'backend/' directory), run:

   tar -xzf /path/to/tb3_backend_rich_mock_data_fixpack_U.tgz

2) Restart uvicorn.

3) Enable mock mode:
   export TB3_MOCK_DATA=1
   # or: export MOCK_DATA=1

Notes
- Mock mode bypasses chain CLI reads/writes for the endpoints covered by the mock layer.
- Data is generated in-memory per process start; restart to regenerate.
