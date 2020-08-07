FROM autopas/autopas-build-gcc

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y python3-pip

# Cloning Performance Testing Repo
RUN echo "cache buster 7"
RUN git clone https://github.com/AutoPas/PerformanceTesting.git

# install PerformanceTesting requirements
RUN pip3 install --no-cache-dir -r PerformanceTesting/requirements.txt

WORKDIR /usr/src/app/PerformanceTesting/gitApp/manualMethods
ENV PYTHONPATH /usr/src/app/PerformanceTesting/gitApp

# Expose Ports of Flask
EXPOSE 8050/tcp
EXPOSE 8050/udp

# ENV MONGOHOST
# ENV USERNAME autopasmongo
# ENV PASSWORD XXXXXXXXXXX

# Run the server
ENTRYPOINT ["gunicorn", "plotlyExplorer:server", "-b 0.0.0.0:8050", "-w 4"]
