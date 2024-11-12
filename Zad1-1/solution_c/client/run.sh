sed -i 's/\r$//' "$0"

echo "Starting client C"
docker build -t z35_cclient .
docker run -it --rm --network z35_network --name z35_cclient_container z35_cclient
