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

    // 2. Проверка корректности данных
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

    // 3. Динамическое обновление навигации
    function updateNavigation() {
        const navLinks = document.getElementById('navLinks');
        if (navLinks) {
            navLinks.innerHTML = ''; // Очищаем существующие ссылки
            const isAuthenticated = window.isAuthenticated === "true";
            if (isAuthenticated) {
                navLinks.innerHTML = `
                    <a href="${window.urls.car_list}" class="hover:text-yellow-300 transition-colors">Главная</a>
                    <a href="${window.urls.create_car}" class="hover:text-yellow-300 transition-colors">Добавить объявление</a>
                    <a href="${window.urls.profile}" class="relative hover:text-yellow-300 transition-colors">Профиль</a>
                    <a href="${window.urls.favorite_list}" class="hover:text-yellow-300 transition-colors">Избранное</a>
                    <a href="${window.urls.logout}" class="hover:text-yellow-300 transition-colors">Выйти</a>
                `;
            } else {
                navLinks.innerHTML = `
                    <a href="${window.urls.login}" class="hover:text-yellow-300 transition-colors">Войти</a>
                    <a href="${window.urls.register}" class="hover:text-yellow-300 transition-colors">Регистрация</a>
                `;
            }
        }
    }
    // 4. Обновление навигации при загрузке
    updateNavigation();
});