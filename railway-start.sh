# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput
mkdir -p media
# Start the app
gunicorn stock_prediction_main.wsgi --log-file -