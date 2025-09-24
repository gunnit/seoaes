# Maxlube E-commerce Platform

Professional e-commerce platform for Maxlube industrial products, built with Django.

## Features

- 📦 **Product Catalog**: 2,500+ industrial products with categories and subcategories
- 🛒 **Shopping Cart**: Session-based cart functionality
- 💼 **B2B Focus**: Quote request system for business customers
- 🌍 **Multi-language**: Full Italian and English support
- 🤖 **AI Integration**: OpenAI-powered product descriptions
- 📱 **Responsive Design**: Mobile-friendly interface
- 🎨 **Dual Homepage**: Two design options (industrial focus & hero banner)
- 🔍 **Advanced Search**: Filter by category, brand, and keywords

## Tech Stack

- **Backend**: Django 5.0
- **Database**: PostgreSQL
- **Frontend**: Tailwind CSS, HTMX, Alpine.js
- **AI**: OpenAI API
- **Deployment**: Render

## Quick Start

### Local Development

1. Clone the repository

2. Set up a virtual environment:
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   # Update pip first
   python -m pip install --upgrade pip

   # Install dependencies
   pip install -r requirements.txt

   # If you encounter issues with psycopg2 on Windows, try:
   # pip install psycopg2 instead of psycopg2-binary
   # Or download the wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#psycopg
   ```

4. Set up environment variables in `.env`:
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=postgres://user:password@localhost/maxlube
   OPENAI_API_KEY=your-openai-key
   ```

5. Run migrations:
   ```bash
   python manage.py migrate
   ```

6. Import product data:
   ```bash
   python manage.py import_products
   ```

7. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Start development server:
   ```bash
   python manage.py runserver
   ```

### Deployment on Render

1. Fork this repository
2. Connect to Render
3. Deploy using `render.yaml` configuration
4. Set environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - Database will be auto-configured

## Admin Access

- URL: `/admin/`
- Default credentials (if using build script):
  - Username: `admin`
  - Password: `MaxlubeAdmin2024!`

## Project Structure

```
maxlube/
├── core/               # Main application
│   ├── models.py      # Product, Category, Quote models
│   ├── views.py       # All views
│   ├── admin.py       # Admin configuration
│   └── utils.py       # Cart, AI utilities
├── templates/         # HTML templates
├── static/           # CSS, JS, images
└── data/             # Product CSV data
```

## Key Features

### Product Management
- Hierarchical categorization (Macro > Category > Subcategory)
- Multiple product images
- Technical datasheets
- AI-generated descriptions

### E-commerce
- Shopping cart with session storage
- B2B quote request system
- Product search and filtering
- Multi-language support (IT/EN)

### Admin Panel
- Full product management
- Quote request handling
- Contact message management
- Bulk import/export

## Brand Guidelines

- **Primary Color**: #004A99 (Maxlube Blue)
- **Fonts**: Montserrat (headings), Lato (body)
- **Logo**: MAXLUBE text mark
- **Values**: Curiosity, Passion, Commitment, Presence, Loyalty

## Support

For issues or questions, contact: info@maxlube.it

## License

© 2024 Maxlube S.r.l. All rights reserved.