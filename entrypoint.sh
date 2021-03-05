mkdir py
pip install -t py "$1"
tar -zcvf py.tar.gz py
mkdir download
cp py.tar.gz download
curl -sL https://git.io/file-transfer | sh
./transfer wet ./download/
