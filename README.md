# PLENT API

Frontend code: https://github.com/bitterapple0/50.001-Plent-Application

PLENT is an event planner Android application designed and created as part of the 50.001 course in Fall 2020.

This application includes:
- User authentication with Firebase Auth
- Curation of all available events in scrollable categories
- Quick event sign up with pre-existing account information
- Calendar view showing color-coded events based on their categories
- Alerts for timing clashes when signing up for events
- Collation of participant information for event organizers

Technical details:
- A simple Flask API was used to connect our Android application to our MongoDB database.
- Images uploaded by event creators were stored on Cloudinary, with the Cloudinary links stored in our MongoDB database.
- Firebase Auth was used for user authentication.
- The Flask API was deployed using Heroku.

A video demonstration of PLENT can be found here: https://youtu.be/8L8xmo6JUxs
