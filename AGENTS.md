# Agents.md

# Do 
- Use python for backend
- Use React for frontend
- Use persistent storage
- Add function headers and file headers when documenting code as shown in /backend/db.py
- When constructing backend tests use pytest
- Use uvicorn for serving API app
- When naming variables give them descriptive names
- Try to reduce returns to 1 per function

# Do not 
- Name variables as just letters

# Project Structure
- Backend code is located in /backend
- Frontend code is located in /frontend
- /backend/schema.sql contains schema
- /data contains the SQLite3 db
- /backend/app/routers contains FastAPI routers
- /backend/app/services contains API services
- /backend/app/queries contains db queries
- /backend/app/ai contains all ai service files
- /scripts contains CI/CD for github actions