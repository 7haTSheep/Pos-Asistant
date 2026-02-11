@echo off
echo Installing Puppeteer...
call npm install puppeteer --save-dev

echo Running reproduction script...
node reproduce_crash.js

pause
