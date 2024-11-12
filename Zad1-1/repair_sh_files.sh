find . -type f -name "*.sh" -exec sed -i 's/\r//g' {} \;
find . -type f -name "*.sh" -exec chmod 744 {} +