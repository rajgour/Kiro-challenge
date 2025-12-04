# Kiro Challenge

## Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Infrastructure (CDK)

```bash
cd infrastructure
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cdk synth
cdk deploy
```
