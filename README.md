# Food Conscious

A health and nutrition web application designed to help users track their daily energy intake and calculate the energy content of custom recipes and meals.

**Video Demo:** [Watch on YouTube](https://youtu.be/dR1ocMMoRgc)

---

## Features

1. **Food Logbook**: Log your meals (Breakfast, Lunch, Dinner, Snack, Other) with dates and energy counts (kJ or Calories) to monitor your daily intake.
2. **Energy Calculator**: 
   - Search a database of over 1,500 ingredients with automatic energy calculations per portion size.
   - Add custom ingredients with custom energy counts.
   - Save, revisit, and delete custom recipes.
   - Calculate total and per-serving energy count for batch recipes.
3. **Smart Units**: Automatic two-way conversion between kilojoules (kJ) and kilocalories (Calories).
4. **User Authentication**: Secure user registration, password hashing, and login sessions.

---

## Tech Stack

- **Backend**: Python, [Flask](https://flask.palletsprojects.com/), [Flask-Session](https://flask-session.readthedocs.io/), [CS50 SQL](https://cs50.readthedocs.io/libraries/cs50/python/)
- **Frontend**: HTML5, Jinja templates, CSS3, [Bootstrap 5](https://getbootstrap.com/), [Select2](https://select2.org/) (searchable ingredient dropdowns)
- **Database**: SQLite (local development) / PostgreSQL (production)
- **Production Server**: [Gunicorn](https://gunicorn.org/)

---

## Local Setup & Installation

Follow these steps to run Food Conscious on your local machine.

### Prerequisites

- **Python**: Version 3.9, 3.10, 3.11, or 3.12
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/IzzybellaDu/Food-Conscious.git
cd Food-Conscious
```

### 2. Create and Activate a Virtual Environment

- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **Windows**:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

For local development, the app automatically uses the pre-seeded SQLite database (`system.db`):

```bash
python application.py
```

Or using Flask CLI:

```bash
flask run
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## Environment Variables

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | No | `sqlite:///system.db` | Connection string for PostgreSQL (e.g. on Neon, Supabase, Render). If unset, falls back to local SQLite. |
| `SECRET_KEY` | No | Dev default string | Secret key for Flask session security and flash messages. Set to a random secure string in production. |

---

## Database Configuration

- **Local Development (SQLite)**: The repository includes `system.db`, which is already loaded with 1,534 foods in `fooddata` and the required schemas for users, recipes, food logs, and ingredients.
- **Production (PostgreSQL)**: When deploying to cloud hosts with Postgres (e.g., Neon, Supabase), run the included [`seed_postgres.sql`](seed_postgres.sql) script in your database SQL console to create all tables and populate the food database.

---

## Free Cloud Deployment (Render + Neon)

Food Conscious can be hosted 100% free using **Render** (for the web service) and **Neon** (for serverless PostgreSQL):

### Step 1: Create Free PostgreSQL on Neon
1. Sign up at [neon.tech](https://neon.tech/) (free, no credit card required).
2. Create a new project (e.g., `food-conscious`).
3. Open the **SQL Editor** tab in Neon, paste the contents of [`seed_postgres.sql`](seed_postgres.sql), and click **Run**.
4. Copy your database connection string (starts with `postgresql://...`).

### Step 2: Deploy to Render
1. Push your latest code to your GitHub repository.
2. Sign up or log into [render.com](https://render.com/).
3. Click **New + > Web Service** and connect your `Food-Conscious` repository.
4. Render will detect [`render.yaml`](render.yaml) automatically, or configure manually:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn application:app`
   - **Instance Type**: `Free`
5. Under **Environment Variables**, set:
   - `DATABASE_URL`: *(your Neon connection string)*
   - `SECRET_KEY`: *(generate or enter a secure random secret)*
6. Click **Deploy Web Service**.

---

## File Structure

- `application.py`: Main application file containing Flask routes, custom Jinja filters, energy conversion helper functions, and database handlers.
- `system.db`: SQLite database containing food data, user accounts, recipes, and food diary logs for local development.
- `seed_postgres.sql`: PostgreSQL schema and seed data containing all 1,534 food items for cloud database deployments.
- `Procfile`: Process definition for Gunicorn web server deployment.
- `render.yaml`: Infrastructure configuration for one-click deployment on Render.
- `templates/`: HTML templates rendered with Jinja2 for each application route.
- `static/`: Static assets including icons, images, and custom CSS stylesheet.

---

## Design Choices

A few deliberate design choices were made in this project:

- **Logbook Structure**: For the food logbook, a dictionary of lists is used to hold query results grouped by date. This allows date-grouped logs to render efficiently in templates with a single argument.
- **Custom Jinja Filters**: Custom filters handle units and formatting directly in templates (e.g., `kjtocal` for kJ-to-calorie conversion, and `totalling` for array sums), avoiding redundant calculations in route handlers.
- **Unit Normalization**: The database standardizes all energy counts in kilojoules (kJ). Users can enter or view data in either kJ or Calories, with helper functions performing conversions seamlessly.
- **Relational Integrity**: Unique primary keys on ingredients, recipes, and food logs allow secure deletions and queries targeted by unique ID.

---

## Future Developments

- A water logbook that helps users track their daily hydration.
- An ingredient comparator to quickly compare foods by energy density.
- Recipe search via an external nutrition API.
