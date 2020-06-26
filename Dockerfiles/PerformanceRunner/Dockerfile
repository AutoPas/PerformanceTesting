FROM autopas/autopas-build-gcc

WORKDIR /usr/src/app

# Copy GitHub App Certificate and Database configuration file, moved up top to crash early if not found
COPY *.pem private-key.pem
COPY database.config .

RUN apt-get update
RUN apt-get install -y python3-pip

# Cloning Performance Testing Repo and AutoPas (should then update AutoPas, during deployment)
RUN git clone https://github.com/AutoPas/AutoPas.git
RUN echo "cache buster 11"
RUN git clone https://github.com/AutoPas/PerformanceTesting.git

# install PerformanceTesting requirements
RUN pip3 install --no-cache-dir -r PerformanceTesting/requirements.txt

# move files to correct location in project folder
RUN mv *.pem PerformanceTesting/gitApp/
RUN mv database.config PerformanceTesting/gitApp/

WORKDIR /usr/src/app/PerformanceTesting/gitApp
ENV PYTHONPATH /usr/src/app/PerformanceTesting/gitApp

# ENV IMGURCLIENTID XXXX
# ENV GITHUBAPPID XXXXX
# TODO: Might be overwritten globally from CheckFlow
ENV OMP_NUM_THREADS 12
# TODO: Setting this to 0 will not disable production mode. Commenting it will disable
ENV PRODUCTION 1


# allow write for the git and test scripts
RUN ["chmod", "-R", "777", "/usr/src/app"]

# Run down the queue
ENTRYPOINT ["python3", "/usr/src/app/PerformanceTesting/gitApp/checks/Worker.py"]

# TODO: optionally add Healthchecks
# CMD [ "/bin/bash" ]
