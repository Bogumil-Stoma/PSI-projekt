
echo "Starting server C"
docker build -t z35_cserver .
docker run -it --rm --network z35_network --name z35_cserver_container z35_cserver
