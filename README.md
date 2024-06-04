# YOUR PROJECT TITLE
#### Video Demo:  <URL HERE>
#### Description:
TODO

# I made use of GitHub CoPilot to assist me, but I don't think I abused it!
# This helped me in setting up TailWind CSS:
# 1) https://tailwindcss.com/docs/installation
# 2) https://flowbite.com/docs/getting-started/flask/
# 3) https://tw-elements.com/docs/standard/components/social-buttons/ (Social Media Icons)

CSRF protection is an important part of securing your web application, but it's not directly related to preventing SQL Injection attacks. CSRF (Cross-Site Request Forgery) protection is about preventing unauthorized commands from being transmitted from a user that the web application trusts.

SQL Injection is prevented in Flask by using the SQLAlchemy ORM for database queries. SQLAlchemy automatically escapes any variables that are passed into a query, which prevents SQL Injection attacks.

In your code, you're using SQLAlchemy, so as long as you're not manually constructing SQL queries with string concatenation or formatting, you should be safe from SQL Injection attacks.

# Student Default Image: Photo by <a href="https://unsplash.com/@jjying?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">JJ Ying</a> on <a href="https://unsplash.com/photos/mt-fuji-japan-9Qwbfa_RM94?utm_content=creditCopyText&utm_medium=referral&utm_source=unsplash">Unsplash</a>
  