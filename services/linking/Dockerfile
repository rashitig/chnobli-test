FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04


ENV DEBIAN_FRONTEND=noninteractive 

RUN  apt-get update

RUN apt-get -y install build-essential checkinstall && apt-get -y install \
  libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev \
  libc6-dev libbz2-dev libffi-dev zlib1g-dev wget git unzip

WORKDIR /opt

RUN wget https://www.python.org/ftp/python/3.11.0/Python-3.11.0.tgz && \
  tar xzf Python-3.11.0.tgz && rm Python-3.11.0.tgz

WORKDIR /opt/Python-3.11.0

RUN ./configure --enable-optimizations && make install

WORKDIR /home/nla/

#RUN git clone https://gitlab.ethz.ch/library/adl/nla.git

WORKDIR /home/nla

COPY deployment_key/adl_key .
RUN chmod 600 adl_key

RUN eval $(ssh-agent) && \
    ssh-add adl_key && \
    ssh-keyscan -H gitlab.ethz.ch >> /etc/ssh/ssh_known_hosts && \
    git clone git@gitlab.ethz.ch:library/adl/nla.git /home/nla/nla

ENV PATH="${PATH}:/opt/Python-3.8.13/"

ENV VIRTUAL_ENV=/opt/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies:

WORKDIR /home/nla/nla

RUN git checkout deployment

RUN wget -O models.zip https://polybox.ethz.ch/index.php/s/o3NKzmHfFJXBhTY/download && unzip models.zip && rm models.zip

RUN pip install -U pip && pip install -r requirements.txt
