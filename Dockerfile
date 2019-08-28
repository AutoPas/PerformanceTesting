FROM autopas/autopas-build-gcc

WORKDIR /usr/src/app

RUN apt-get update
RUN apt-get install -y python3-pip

# TODO: Git clone AutoPas automatically inside of Testing code
# Cloning Performance Testing Repo (should then itself clone AutoPas)
RUN git clone https://github.com/AutoPas/PerformanceTesting.git
# install its requirements
RUN pip3 install --no-cache-dir -r PerformanceTesting/requirements.txt

# Copy GitHub App Certificate and Database configuration file
# TODO: Move up to crash early if user doesnt provide files?
COPY *.pem PerformanceTesting/gitApp
COPY database.config PerformanceTesting/gitApp

# Expose Ports of django server
EXPOSE 3000/tcp
EXPOSE 3000/udp

# TODO: Run Performance Testing server, instead of via remote interpreter
# RUN python3 manage.py runserver 0.0.0.0:3000

CMD [ "/bin/bash" ]