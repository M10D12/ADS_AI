Backend (Django)
bash
cd Project/backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

Frontend (React)
bash
cd Project/frontend
npm install
npm install react-router-dom
npm start


Frontend: http://localhost:3000
Backend: http://localhost:8000
API Status: http://localhost:8000/api/status/

Project/
├── backend/
│   ├── config/
│   │   ├── settings.py      # Django + DRF + CORS
│   │   └── urls.py          # API de status
│   ├── manage.py
│   └── requirements.txt     # Django, DRF, CORS
└── frontend/
    ├── src/
    │   ├── App.js           # Montar app
    │   ├── index.js
    │   └── index.css
    ├── package.json         # React + Axios + Proxy
    └── public/
```
