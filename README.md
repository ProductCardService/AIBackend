# AIBackend

## Развертывание
Создание Docker-образа
```bash
docker build -t product-card-service/ai:latest .
```
Запуск контейнера на основе Docker-образа
```bash
docker run --rm -p 8080:8080 product-card-service/ai:latest
```

## Разработка
Переменные окружения
```env
API_KEY=<API_KEY>
FOLDER_ID=<FOLDER_ID>
GIGACHAT_CREDENTIALS=<GIGACHAT_CREDENTIALS>
KANDINSKY_API_KEY=<KANDINSKY_API_KEY>
KANDINSKY_SECRET_KEY=<KANDINSKY_SECRET_KEY>
```