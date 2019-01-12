if [ -e results ]; then
	rm -rf results/*
else
	mkdir results
fi
./analyse.py bagadres.csv
