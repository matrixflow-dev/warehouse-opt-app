FROM python:3.10 as builder
RUN apt-get update && \
    apt-get install \
    build-essential \
    cmake \
    clang \
    gcc \
    libsparsehash-dev \
    libboost-all-dev -qq --fix-missing


COPY MCA-RMCA /MCA-RMCA
RUN mkdir /MCA-RMCA/build
WORKDIR /MCA-RMCA/build
RUN cmake .. && make

FROM python:3.10 as base
RUN apt-get update && \
    apt-get install \
    libsparsehash-dev \
    libboost-all-dev -qq --fix-missing

RUN mkdir /root/ai
COPY --from=builder /MCA-RMCA/ /root/MCA-RMCA
WORKDIR /root
COPY requirements.txt ./
COPY pytest.ini ./
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages
ENV PYTHONPATH "${PYTHONPATH}:/root/ai/src/"
COPY ./behavior_opt /root/ai/src/behavior_opt
COPY ./front /root/ai/src/front
COPY ./main.py /root/ai/src/
COPY ./storage /root/ai/src/storage


FROM base as production
EXPOSE 80
CMD uvicorn main:app --host 0.0.0.0 --port 80
