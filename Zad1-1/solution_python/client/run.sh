sed -i 's/\r$//' "$0"

echo "Starting client Python"
docker build -t z35_pclient .
docker run -it --rm --network z35_network --name z35_pclient_container z35_pclient
