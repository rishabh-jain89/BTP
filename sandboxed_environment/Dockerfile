FROM alpine:3.23

RUN apk add --no-cache gcc musl-dev

# Removing the root privileges from the code by creating another user
RUN adduser -D student 

WORKDIR /app

RUN chown student:student /app

USER student