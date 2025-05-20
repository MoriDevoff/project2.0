document.addEventListener('DOMContentLoaded', function () {
    // 1. Кнопка "Наверх"
    const scrollToTopBtn = document.createElement('button');
    scrollToTopBtn.innerHTML = '↑ Наверх';
    scrollToTopBtn.classList.add('scroll-to-top', 'hidden');
    document.body.appendChild(scrollToTopBtn);

    window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
            scrollToTopBtn.classList.remove('hidden');
        } else {
            scrollToTopBtn.classList.add('hidden');
        }
    });

    scrollToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // 2. Модальное окно (уже есть в edit_car.html, стили добавлены в style.css)

    // 3. Стикеры
    function showSticker(message, type = 'info', duration = 3000) {
        const sticker = document.createElement('div');
        sticker.classList.add('sticker', type);
        sticker.innerHTML = message + '<button class="sticker-close">×</button>';
        document.body.appendChild(sticker);

        setTimeout(() => {
            sticker.classList.add('fade-out');
            setTimeout(() => sticker.remove(), 300);
        }, duration);

        sticker.querySelector('.sticker-close').addEventListener('click', () => {
            sticker.classList.add('fade-out');
            setTimeout(() => sticker.remove(), 300);
        });
    }

    // 4. Выдвигающаяся панель (для обычных пользователей)
    console.log('isAuthenticated:', window.isAuthenticated); // Для отладки
    if (window.isAuthenticated === 'true') { // Сравниваем как строку
        const sidebar = document.createElement('div');
        sidebar.classList.add('sidebar');
        sidebar.innerHTML = `
            <div class="sidebar-tab">☰ Панель</div>
            <div class="sidebar-content">
                <h3>Быстрые действия</h3>
                <ul>
                    <li><a href="${window.urls.car_list}">Список автомобилей</a></li>
                    <li><a href="${window.urls.profile}">Профиль</a></li>
                    <li><a href="${window.urls.create_car}">Добавить автомобиль</a></li>
                    <li><a href="${window.urls.favorite_list}">Избранное</a></li>
                </ul>
            </div>
        `;
        document.body.appendChild(sidebar);

        const sidebarTab = sidebar.querySelector('.sidebar-tab');
        sidebarTab.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // 6. Проверка корректности данных
    function validateInput(input, regex, errorMessage) {
        input.addEventListener('input', () => {
            if (!regex.test(input.value) && input.value !== '') {
                showSticker(errorMessage, 'error', 5000);
                input.classList.add('invalid');
            } else {
                input.classList.remove('invalid');
            }
        });
    }

    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;

    document.querySelectorAll('input[type="tel"]').forEach(input => {
        validateInput(input, phoneRegex, 'Некорректный номер телефона! Пример: +79991234567');
    });

    document.querySelectorAll('input[type="email"]').forEach(input => {
        validateInput(input, emailRegex, 'Некорректный email! Пример: user@example.com');
    });

    document.querySelectorAll('input[type="password"]').forEach(input => {
        validateInput(input, passwordRegex, 'Пароль должен содержать минимум 8 символов, включая буквы и цифры!');
    });
});