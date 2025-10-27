# rpi-ble
mucking around with ble on rpi


# on clean install of raspian 32 bit

sudo apt-get update
sudo apt-get -y install pyenv git wget cmake libdbus-1-dev libcairo2-dev python3-dbus \
            python3-venv python3-gi gpsd libgirepository1.0-dev python3-dev
sudo systemctl enable gpsd
sudo systemctl start gpsd

# reboot .. set auto login
git clone <this repo>
cd rpi-ble


python -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=.

pip install pygobject==3.50.0  (add to requirements.txt)


(what about auto login on startup?)

upon new prompt on rpi
sudo apt-get update
sudo apt-get install git cmak

git clone https://github.com/sprintf/rpi-ble.git
cd rpi-ble


