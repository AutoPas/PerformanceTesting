FROM autopas/autopas-build-gcc

WORKDIR /usr/src/app

# Copy GitHub App Certificate and Database configuration file, moved up top to crash early if not found
COPY *.pem private-key.pem
COPY database.config .

RUN apt-get update
RUN apt-get install -y python3-pip

# TODO: Git update AutoPas automatically inside of Testing code
# Cloning Performance Testing Repo (should then itself update AutoPas)
RUN git clone https://github.com/AutoPas/PerformanceTesting.git
RUN git clone https://github.com/AutoPas/AutoPas.git

# install PerformanceTesting requirements
RUN pip3 install --no-cache-dir -r PerformanceTesting/requirements.txt

# move files to correct location in project folder
RUN mv *.pem PerformanceTesting/gitApp/
RUN mv database.config PerformanceTesting/gitApp/

# Expose Ports of django server
EXPOSE 8080/tcp
EXPOSE 8080/udp

WORKDIR /usr/src/app/PerformanceTesting/gitApp

# TODO: Run Performance Testing server, instead of via remote interpreter
# TODO: RUN PULL AND UPDATE BEFORE STARTING SERVER VIA CMD

ENV GITHUBAPPID 41626

RUN ["python3", "manage.py", "migrate"]

#ENTRYPOINT ["python3", "manage.py", "runserver", "0.0.0.0:8080", "--noreload"]

ENTRYPOINT ["./entry.sh"]

# TODO: optionally add Healthchecks

#CMD [ "/bin/bash" ]
