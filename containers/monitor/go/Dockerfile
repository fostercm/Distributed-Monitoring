FROM scratch

COPY monitor.bin .

CMD ["./monitor.bin"]

# docker build -t go_monitor .
# docker container run -v /var/run/docker.sock:/var/run/docker.sock -p 8080:8080 --name go_monitor go_monitor