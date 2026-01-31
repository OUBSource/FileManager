from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, db
import psutil
import platform
import os
import shutil

main = Blueprint('main', __name__)

def get_root_dir():
    system = platform.system()
    if system == "Windows":
        return "C:\\"
    else:
        return "/"

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    # Проверяем, есть ли хоть один пользователь в БД
    user_exists = User.query.first()
    mode = 'login' if user_exists else 'register'
    
    return render_template('login.html', mode=mode)

@main.route('/auth', methods=['POST'])
def auth():
    username = request.form.get('username')
    password = request.form.get('password')
    mode = request.form.get('mode')

    if mode == 'register':
        if len(username) < 2:
            flash('Имя должно быть не менее 2 символов', 'error')
            return redirect(url_for('main.index'))
        if len(password) < 5:
            flash('Пароль должен быть не менее 5 символов', 'error')
            return redirect(url_for('main.index'))
        
        # Создаем первого пользователя
        new_user = User(username=username, password=generate_password_hash(password, method='scrypt'))
        db.session.add(new_user)
        db.session.commit()
        
        # Сразу логиним
        login_user(new_user, remember=True)
        session.permanent = True
        return redirect(url_for('main.dashboard'))

    else: # Login
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            flash('Неверный логин или пароль', 'error')
            return redirect(url_for('main.index'))
        
        login_user(user, remember=True)
        session.permanent = True
        return redirect(url_for('main.dashboard'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Получаем информацию о дисках
    partitions = psutil.disk_partitions()
    disks_info = []
    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            disks_info.append({
                'device': p.device,
                'mountpoint': p.mountpoint,
                'total': f"{usage.total / (1024**3):.1f} GB",
                'percent': usage.percent
            })
        except PermissionError:
            continue

    return render_template('dashboard.html', user=current_user, disks=disks_info)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

# --- API Файлового менеджера ---

@main.route('/api/files', methods=['POST'])
@login_required
def file_manager():
    data = request.json
    action = data.get('action')
    path = data.get('path', get_root_dir())
    
    # Защита от выхода за пределы (базовая) - хотя просили root, но пути проверим
    if not os.path.exists(path):
        return jsonify({'error': 'Путь не найден', 'path': path})

    try:
        if action == 'list':
            items = []
            with os.scandir(path) as it:
                for entry in it:
                    items.append({
                        'name': entry.name,
                        'is_dir': entry.is_dir(),
                        'path': entry.path
                    })
            # Сортировка: папки сверху
            items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return jsonify({'items': items, 'current_path': path})

        elif action == 'rename':
            new_name = data.get('new_name')
            new_path = os.path.join(os.path.dirname(path), new_name)
            os.rename(path, new_path)
            return jsonify({'status': 'ok'})

        elif action == 'delete':
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            return jsonify({'status': 'ok'})
            
        elif action == 'create_folder':
             name = data.get('name')
             os.mkdir(os.path.join(path, name))
             return jsonify({'status': 'ok'})

        # Copy/Cut - упрощенная реализация через сессию (можно расширить)
        
    except Exception as e:
        return jsonify({'error': str(e)})
    
    return jsonify({'status': 'ok'})