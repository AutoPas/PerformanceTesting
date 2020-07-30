FROM autopas/autopas-build-gcc

WORKDIR /usr/src/app

# Copy GitHub App Certificate and Database configuration file, moved up top to crash early if not found
COPY *.pem private-key.pem
COPY database.config .

RUN apt-get update
RUN apt-get install -y python3-pip

# Cloning Performance Testing Repo and AutoPas (should then update AutoPas, during deployment)
RUN git clone https://github.com/AutoPas/AutoPas.git
RUN echo "cache buster 26"
RUN git clone https://github.com/AutoPas/PerformanceTesting.git

# install PerformanceTesting requirements
RUN pip3 install --no-cache-dir -r PerformanceTesting/requirements.txt

# move files to correct location in project folder
RUN mv *.pem PerformanceTesting/gitApp/
RUN mv database.config PerformanceTesting/gitApp/

# Expose Ports of django server
EXPOSE 8080/tcp
EXPOSE 8080/udp

WORKDIR /usr/src/app/PerformanceTesting/gitApp

# ENV IMGURCLIENTID XXXX
# ENV GITHUBAPPID XXXXX
# ENV OMP_NUM_THREADS 8

# Initialize database
RUN ["python3", "manage.py", "makemigrations"]
RUN ["python3", "manage.py", "migrate"]
# TODO: safe solution for user adding, only useful for lock checking
#RUN... echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'pass')" | python3 manage.py shell

#ENTRYPOINT ["python3", "manage.py", "runserver", "0.0.0.0:8080", "--noreload"]

# allow write for the git and test scripts
RUN ["chmod", "-R", "777", "/usr/src/app"]
RUN ["chmod", "u+x", "entry.sh"]
ENTRYPOINT ["./entry.sh"]

# TODO: optionally add Healthchecks

#CMD [ "/bin/bash" ]
