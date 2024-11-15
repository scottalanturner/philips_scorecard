# Deploymemt / config notes for Microsoft
- Ensure the CORS policy in the app includes portal.azure...
- Verify the JSON being sent from the HTTP Action is valid. Copy it out, and paste it into the Test method in the App Function. Then see if it passes. It can get a 500 error in Power Automate, which is useless to debug.
- The only way to get the SQL actions to recognize table changes is to delete the connection and create a new one. Way to go MS. I saw some posts it can take 24-hours for the cache to refresh with changes otherwise.
- Mapping form fields is a PITA. Use Wispr to verbally search the list and find what to match on.

# Build notes
The 'no functions found' error in Azure deployment is often caused by missing dependencies in requirements.txt. But no output will indicate that.
Run this: pip freeze > ./requirements.txt 

pymsql on A1 chips get an error loading the package. They must be built from scratch. You'll also get wheel errors. Use uv to do the build.
uv pip install --pre --no-binary :all: pymssql --no-cache --force

see https://github.com/pymssql/pymssql/issues/880 for ARM issues with pymssql