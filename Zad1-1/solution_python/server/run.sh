sed -i 's/\r$//' "$0"

echo "Starting server Python"
docker build -t z35_pserver .
docker run -it --rm --network z35_network --name z35_pserver_container z35_pserver
