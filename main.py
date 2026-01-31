from app import create_app

# Создаем приложение, указывая папки ресурсов
app = create_app()

if __name__ == '__main__':
    # Запуск сервера
    app.run(host='0.0.0.0', port=5000, debug=True)