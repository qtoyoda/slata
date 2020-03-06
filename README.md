Slata
===

How to Build with Docker
---
Make sure docker is running `docker service start`

```
cd service
docker build -t slata .
docker run -p 5000:5000 slata:latest
```

Sanity Check
```
curl http://localhost:5000/v1/status
```

How to Run Front-end
---
```
cd slata-fe
npm start
```
