# Deployment Guide

This document describes the deployment configuration for ChronOS on Google Cloud.

## 1. Backend Service (FastAPI + LangGraph)
The backend container is designed for deployment on **Google Cloud Run**.

### Build and Deploy Command
```bash
cd backend
gcloud run deploy chronos-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ENV=production,GEMINI_API_KEY=...,SUPABASE_URL=..."
```

## 2. Database (Supabase PostgreSQL)
Supabase handles database hosting. Migrations are executed via:
```bash
npx supabase db push
```

## 3. Frontend (React + Vite)
The static frontend can be deployed to Vercel, Netlify, or Firebase Hosting.
```bash
cd frontend
npm run build
```
