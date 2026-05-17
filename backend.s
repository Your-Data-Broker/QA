bits 64
global process_single_pass

section .text  ; Виправили .test на .text

process_single_pass:
    ; --- ПРОЦЕСОР ПРИЗЕМЛИВСЯ ТУТ ---
    ; Поточний стан регістрів (передано з Python):
    ; RDI = вказівник на оригінальне зображення (bgr_pixels)
    ; RSI = вказівник на масив результатів (masks_out)
    ; RDX = ширина картинки (width)
    ; RCX = висота картинки (height)
    
    ; 1. Рахуємо загальну кількість пікселів (width * height)
    ; Використаємо вільний регістр R10 як ліміт нашого циклу
    mov r10, rdx       ; Копіюємо width в r10
    imul r10, rcx      ; Множимо r10 на height (тепер r10 = total_pixels)

    ; 2. Готуємо індекс (наш лічильник i = 0)
    ; Використаємо вільний регістр RAX
    mov rax, 0         

.loop_start:
    ; 3. Перевірка: чи дійшли ми до кінця? (якщо i == total_pixels, то вихід)
    cmp rax, r10       ; Порівнюємо RAX та R10
    jge .done          ; Jump if Greater or Equal -> стрибаємо на мітку .done

    ; 4. Тіло циклу: пишемо 255 у маску
    mov byte [rsi + rax], 255  ; rsi (початок) + rax (поточний зсув)

    ; 5. Крок циклу
    inc rax            ; i++
    jmp .loop_start    ; Повертаємось на початок циклу

.done:
    ; 6. Вихід
    ret                ; Тріумфально повертаємось у Python
