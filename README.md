# ReelsEd – Educational Reels Generator with OpenAI

ReelsEd is a Django-based platform that automatically generates short-form educational video reels from long-form lecture content using OpenAI’s GPT models. It is designed for instructors and students who benefit from microlearning formats like those seen on TikTok or Instagram Reels.

---

## Features

- Generate short educational reels from long videos  
- Summarize content using OpenAI GPT-4  
- Instructor dashboard for uploading and managing content  
- Student dashboard to view and rate reels  
- Auth system with instructor and student roles  
- Dockerized for easy setup  

---

## Setup Instructions (Docker Deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/lstavrinu/ReelsEd-CHIGREECE-2025
cd ReelsEd-CHIGREECE-2025/
```

---

### 2. Build Docker Services

```bash
docker-compose build
```


---

### 3. Create and Start Docker Containers

```bash
docker-compose up
```

Access the app at: [http://localhost:20000/web_app/index/](http://localhost:20000/web_app/index/)

---


### 4. Run Migrations (if needed manually)

Open a new terminal window and run:

```bash
docker-compose exec web python manage.py migrate
```

---


### 5. Stop Docker Containers

```bash
docker-compose stop
```

### 6. Delete the Containers (and volumes with -v)

```bash
docker-compose down -v
```

##  Platform Usage Guide

1. **Create 2 user accounts** from the registration page:
   - One as **Instructor**
   - One as **Student**

2. **Log in as the Instructor** and open the **Instructor Dashboard**.

3. Upload a **YouTube video** by pasting its URL.  
   > Tip: Use a short video (under 5 minutes) to save your OpenAI API credits.

4. Click **"Generate Reels"** to process the video.  
   This will:
   - Download the video
   - Extract the transcript
   - Use OpenAI to identify key moments
   - Automatically generate short reels with summaries

5. After generation completes, **assign the video** to the Student you registered earlier.

6. **Log in as the Student** and verify that:
   - The video appears in their dashboard
   - The reels are visible and playable

##  OpenAI API Key Setup


### Hardcoded Key in Code 

Open `web_app/utils.py` and manually update this line:

```python
openai.api_key = "your_openai_key_here"
```


---

Generate your OpenAI API key at:  
https://platform.openai.com/account/api-keys

---

## Database

- This project starts with an **empty database**
- Each user uploads their own content and generates their own data
- Database migrations will initialize a clean schema for you

---

## Tech Stack

- Django (Python)
- PostgreSQL (via Docker)
- Docker & Docker Compose
- OpenAI GPT API (GPT-4 or GPT-3.5)
- yt-dlp for video downloads
- MoviePy for reel editing
- YouTube Transcript API

---

## Directory and Files Overview

```
ReelsEd-CHIGREECE-2025/
├── media/
├── project/
├── staticfiles/
├── web_app/
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── manage.py
├── policy.xml
├── README.md
└── requirements.txt
```
