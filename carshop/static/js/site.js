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
});