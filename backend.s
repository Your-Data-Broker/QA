
global process_single_pass ; Декларуємо функцію

section .text ; Секція з кодом (з цього моменту починається виконання)

process_single_pass:
    ; Поточний стан регістрів (передано з Python):
    ; RDI = вказівник на оригінальне зображення (bgr_pixels)
    ; RSI = вказівник на масив результатів (masks_out)
    ; RDX = кількість пікселів
    ; RCX = flat_lower_bounds
    ; R8 = flat_upper_bounds
    ; R9 = num_targets

    ; Зберігаємо усі значення регістрів rbp, rbx, r12-15 у стек
    push rbp
    push rbx
    push r12
    push r13
    push r14
    push r15
    
    mov rbx, rcx ; rbx = flat_lower_bounds
    mov rbp, r8 ; rbp = flat_upper_bounds

    ; Використаємо вільний регістр R10 як ліміт для нашого циклу
    mov r10, rdx       ; Копіюємо кількість пікселів в r10

    ; Готуємо індекс (наш лічильник i = 0)
    ; Використаємо вільний регістр rcx
    xor rcx, rcx ; Зануляємо rcx

.loop_start:
    ; Перевірка (якщо i == total_pixels, то вихід)
    cmp rcx, r10       ; Порівнюємо rax та r10
    jge .done          ; Jump if Greater or Equal, стрибаємо на мітку .done

    ; Тіло циклу (BGR -> HSV, створення маски тощо)
    lea rax, [rcx + rcx*2] ; Записуємо в rax потрійне значення rcx
  
    ; Записуємо значення BGR пікселя за адресою rdi в 3 регістри (r8, r9, r11)
    ; movzx (move with zero-extend) автоматично зануляє залишок
    movzx r8, byte [rdi + rax] ; B
    movzx r9, byte [rdi + rax +1] ; G
    movzx r11, byte [rdi + rax +2] ; R

    ; Знаходження найбільшого (MAX) та найменшого (MIN) значень

    ; Знаходження MIN значення та запис його у r13
    mov r13, r8 ; Робимо припущення що r8 це MIN
    cmp r13, r9 ; Порівнюємо r13 та r9
    jbe .r9_not_MIN ; Якщо r13 менший то йдемо далі
    mov r13, r9 ; Робимо припущення що r9 це MIN
    
    .r9_not_MIN:
    cmp r13, r11 ; Порівнюємо r13 та r11
    jbe .r11_not_MIN ; Якщо r13 менший то це MIN і ми все так і залишаємо
    mov r13, r11 ; Якщо r11 менший то це MIN

    .r11_not_MIN: ; Просто продовжуємо виконання

    ; Знаходження MAX значення та запис його у r12
    mov r12, r8 ; Робимо припущення що r8 це MAX
    cmp r12, r9 ; Порівнюємо r12 та r9
    jae .r9_not_MAX ; Якщо r12 більший то йдемо далі
    mov r12, r9 ; Робимо припущення що r9 це MAX

    .r9_not_MAX:
    cmp r12, r11 ; Порівнюємо r12 та r11
    jae .r11_not_MAX ; Якщо r12 більший то це MAX і ми все так і залишаємо
    mov r12, r11

    .r11_not_MAX: ; Просто продовжуємо виконання

    ; Знаходження HSV та запис в регістри (r12, r13, r15)

    ; Знаходження дельти
    mov r14, r12 ; Копіюємо MAX в r14
    sub r14, r13 ; Віднімаємо від r14 r13 (знаходимо дельту кольору)
    cmp r14, 0 ; Порівнюємо дельту з 0
    je .pixel_is_gray ; Якщо дельта 0, то і Hue і Saturation теж дорівнюють 0

    ; Знаходження Saturation
    mov rax, r14 ; Готуємо дельту в rax (ділене)
    imul rax, 255 ; Множимо rax на 255

    xor rdx, rdx ; Зануляємо rdx щоб не передавати сміття в div
    div r12 ; Ділимо rdx:rax на MAX. Результат автоматично лягає в rax

    mov r13, rax ; Зберігаємо Saturation в r13

    ; Знаходження Hue
    ; Пам'ятаємо: r11 = R, r9 = G, r8 = B, r12 = MAX, r14 = дельта
    cmp r12, r11 ; Порівнюємо MAX з червоним каналом
    je .hue_max_is_red ; Якщо дорівнює то обчислюємо Hue за першою формулою

    cmp r12, r9 ; Порівнюємо MAX з зеленим каналом
    je .hue_max_is_green ; Якщо дорівнює то обчислюємо за другою формулою

    jmp .hue_max_is_blue ; Якщо ні те ні інше то за третьою

    .hue_max_is_red: ; Перша формула
      mov rax, r9 ; Копіюємо зелений канал в rax
      sub rax, r8 ; Віднімаємо від rax синій канал (може стати від'ємним)

      imul rax, 30 ; Множемо на 30

      cqo ; Готуємо rdx для підписаного (signed) ділення
      idiv r14 ; Підписане ділення rdx:rax на r14. Результат лягає в rax
      
      cmp rax, 0 ; Порівнюємо rax з 0
      jge .red_hue_done ; Якщо Hue >= 0 то закінчуємо
      add rax, 180 ; Якщо ні, то додаємо 180

      .red_hue_done: ; Закінчення рахунку
        mov r15, rax ; Записуємо Hue в r15
        jmp .hue_done ; Пропускаємо всі інші формули

    .hue_max_is_green: ; Друга формула
      mov rax, r8 ; Копіюємо синій канал в rax
      sub rax, r11 ; Віднімаємо від rax червоний канал (може стати від'ємним)
    
      imul rax, 30 ; Множемо на 30
    
      cqo ; Готуємо rdx до підписаного (singed) ділення
      idiv r14 ; Підписане ділення rdx:rax на r14. Результат лягає в rax
      add rax, 60 ; Додаємо 60
    
      mov r15, rax ; Записуємо Hue в r15
      jmp .hue_done ; Пропускаємо інші формули

    .hue_max_is_blue: ; Третя формула
      mov rax, r11 ; Копіюємо червоний канал в rax
      sub rax, r9 ; Віднімаємо від rax зелений канал (може стати від'ємним)
    
      imul rax, 30 ; Множемо на 30
    
      cqo ; Готуємо rdx до підписаного (singed) ділення
      idiv r14 ; Підписане ділення rdx:rax на r14. Результат лягає в rax
      add rax, 120 ; Додаємо 120 
      mov r15, rax ; Записуємо Hue в r15

    .hue_done: ; Просто продовжуємо виконання

    jmp .save_pixel_to_mask ; Пропускаємо блок для сірих пікселів

    .pixel_is_gray:
      mov r15, 0 ; Hue = 0
      mov r13, 0 ; Saturation = 0
      ; Value дорівнює MAX, тож вже лежить в r12

    .save_pixel_to_mask: ; Створюємо чорно-білу маску, яку потім передамо в Python

      ; 1. Перевірка Hue
      cmp r15b, byte [rbx] ; Порівнюємо Hue (r15b) з flat_lower_bounds[0]
      jb .write_zero ; Якщо менше - колір не підходить
      cmp r15b, byte [rbp] ; Порівнюємо Hue (r15b) з flat_upper_bounds[0]
      ja .write_zero ; Якщо більше - колір не підходить

      ; 2. Перевірка Saturation
      cmp r13b, byte [rbx + 1] ; Порівнюємо Saturation (r13b) з flat_lower_bounds[1]
      jb .write_zero
      cmp r13b, byte [rbp + 1] ; Порівнюємо Saturation (r13b) з flat_upper_bounds[1]
      ja .write_zero

      ; 3. Перевірка Value
      cmp r12b, byte [rbx + 2] ; Порівнюємо Value (r12b) з flat_lower_bounds[2]
      jb .write_zero
      cmp r12b, byte [rbp + 2] ; Порівнюємо Value (r12b) з flat_upper_bounds[2]
      ja .write_zero

      .write_255: ; Якщо піксель пройшов, замальовуємо його білим
      mov byte [rsi + rcx], 255 ; Пишемо білий колір у маску ([rsi + rcx])
      jmp .end_mask_write ; Пропускаємо запис нуля

      .write_zero: ; Якщо піксель не пройшов, замальовуємо його чорним
      mov byte [rsi + rcx], 0 ; Пишемо чорний колір у маску

    .end_mask_write: ; Просто продовжуємо виконання

    ; Крок циклу
    inc rcx ; i++
    jmp .loop_start ; Повертаємось на початок циклу

.done: ; Вихід з функції
    ; Повертаємо всі значення регістрів rbp, rbx, r12-15 назад (у зворотньому порядку через LIFO)
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret ; Передеємо результат у Python
