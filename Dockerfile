FROM python:3.10

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN wget -qnc https://repo.nordvpn.com/deb/nordvpn/debian/pool/main/nordvpn-release_1.0.0_all.deb
RUN dpkg -i ./nordvpn-release_1.0.0_all.deb #replace pathToFile to location download folder
RUN apt update
RUN apt install nordvpn -y

COPY . .

CMD [ "python", "./main.py" ]