# Food Conscious
## General
### Video Demo:  <https://youtu.be/dR1ocMMoRgc>
### Description:
Food Conscious is a health web application and has two main parts:
1. Food Logbook
It is where users can log what they eat to monitor their daily energy intake.
2. Energy Calculator
It is where users can figure out the energy count of their recipes and meals.

## Files
- static: my icons/images and my CSS stylesheet
- templates: all my html templates for each route
- application.py:
	In my application file, I created routes for my web application, custom jinja filters and python functions that helped condense my code.

	I created quite a few routes for my project. Some of my routes were very common: login, register, change password, logout. One of the main routes was my kJ/calories calculator. In this route, I displayed a page that asked the user to choose a recipe name and then allowed them to add ingredients to calculate the energy count of the recipe. Another route I created was for my logbook. I firstly retrieved information from my SQL database about past food logs so that I could pass it into my render template function as an argument. The user could then add more food logs.

	I also created two custom jinja filters for Food Conscious. One filter was a "kJ to calories converter". It was very helpful as all the information stored on my database was in kilojoules (kJ) but not all users use the kJ measurement. The other filter accepted two arguments and counted the sum of the values in an array. This allowed me to find the total energy count of a recipe. Lastly, I created a python function which converted calories to  kJ, as some users would input information in calories but the information stored in my database is in kJ.

- food.db: The SQL database storing the energy count of every food.
- system.db: The SQL database storing all the information I added: users, recipe names and ingredients.

## Design Choices
I made a few design choices so that my code could be more concise and my project would work out. For example, for the food logbook, I used a data structure of a dictionary of lists. Those lists held dictionaries that stored the results of SQL queries. This allowed me to display the logbook information on the webpage by passing in one additional argument to the render template function. I also created my own custom Jinja filters so that I could condense my code by calling filters for certain values. For example, instead of storing the kilojoule (kJ) and calorie values of an ingredient or food, I'd only store the kJ count and use a filter to convert it to calories. Another important choice I made when choosing the number of fields for each table of my SQL database was adding a primary key for the ingredients and food logs. It allowed me to easily implement a method for deleting a log or ingredient by executing a SQL query using the item's unique ID.

### Libraries Used
Each library has been used for a particular reason/s.
- Bootstrap: for CSS styling, alert messages and the navigation bar
- Select2: to create a dropdown menu with a search bar for the kJ/Calories Calculator
- cs50: to use SQL
- werkzeug: to keep passwords safe by hashing them
- flask
  - I imported **flash** from flask so that I could pass messages between routes.
- flask_session
- functools

## Future Developments
- A water logbook that helps users remember how much water they drink each day
- A function that compares ingredients based on their energy count
- Using an API to help users find recipes based on their energy count
