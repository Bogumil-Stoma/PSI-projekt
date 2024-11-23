sed -i 's/\r$//' "$0"

cd ./server && ./run.sh
