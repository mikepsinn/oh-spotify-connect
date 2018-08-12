# Google Takeout - Location History

This project allows users to upload their Location History from the Google Takeout archive to OpenHumans, and visualize the same on an interactive heatmap

To run the project from source:

- Install python dependencies using [pipenv](https://github.com/pypa/pipenv#installation)
```
pipenv install
```
- Populate the environment variables listed in `env.sample` in `.env`
- Apply migrations
```
python manage.py migrate
```
- Run server
```
python manage.py runserver
```
