# 🔮 Glass & Liquid Glass Формы для TRACY AI BOT

## 📋 Содержание
1. [Карточки функций (Main Cards)](#карточки-функций-main-cards)
2. [Кнопки (Buttons)](#кнопки-buttons)
3. [Сообщения в чате (Chat Messages)](#сообщения-в-чате-chat-messages)
4. [Инпуты (Input Fields)](#инпуты-input-fields)
5. [Модальные окна (Modals)](#модальные-окна-modals)
6. [События календаря (Calendar Events)](#события-календаря-calendar-events)
7. [Навигация (Navigation)](#навигация-navigation)

---

## 🎴 Карточки функций (Main Cards)

### Вариант 1: "Floating Glass Card" (РЕКОМЕНДУЕТСЯ ✨)

**Визуализация:**
```
┌─────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════╗   │
│ ║ ┌─────────────────────────────────┐       ║   │ ← Gradient border (2px)
│ ║ │  ┌─────────────┐                │       ║   │
│ ║ │  │   ┌─────┐   │ ← Icon (56x56) │       ║   │
│ ║ │  │   │ 💬  │   │    gradient bg │       ║   │
│ ║ │  │   └─────┘   │    + glow      │       ║   │
│ ║ │  └─────────────┘                │       ║   │
│ ║ │                                  │       ║   │
│ ║ │  Чат с Tracy                    │       ║   │
│ ║ │  Онлайн чат с AI-ассистентом    │ ───→  ║   │
│ ║ │                                  │       ║   │
│ ║ └─────────────────────────────────┘       ║   │
│ ╚═══════════════════════════════════════════╝   │
│     ↑ Glass blur background                     │
└─────────────────────────────────────────────────┘
     ↑ Outer glow (0-40px blur)
```

**Форма:**
- **Радиус:** `24px` (очень скругленный, soft)
- **Padding:** `24px`
- **Border:** 1px solid с градиентом
- **Гlow:** Внешнее свечение 40px, opacity 0.2
- **Hover:** Поднимается на 4px вверх, glow усиливается

**CSS пример:**
```css
.floating-glass-card {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-glass-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(135deg,
    rgba(102, 126, 234, 0.6),
    rgba(118, 75, 162, 0.6)
  );
  border-radius: 26px;
  padding: 2px;
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: exclude;
  opacity: 0.6;
}

.floating-glass-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 48px rgba(102, 126, 234, 0.3);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Liquid Blob Card" (ТРЕНДОВЫЙ 🔥)

**Визуализация:**
```
    ╭─────────────────────────────────────╮
  ╱                                         ╲
 │  ┌───────────────────────────────────┐   │
 │  │  ┏━━━━━━━━━━┓                     │   │
 │  │  ┃  ┌────┐  ┃ ← Blob shape icon   │   │
 │  │  ┃  │ 📅 │  ┃    (organic)        │   │
 │  │  ┃  └────┘  ┃                     │   │
 │  │  ┗━━━━━━━━━━┛                     │   │
 │  │                                    │   │
 │  │  Календарь                        │   │
 │  │  Просмотр событий            ───→ │   │
 │  └───────────────────────────────────┘   │
 │                                           │
  ╲                                         ╱
    ╰─────────────────────────────────────╯
       ↑ Organic, flowing shape
```

**Форма:**
- **Стиль:** Органическая форма (border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%)
- **Анимация:** Морфинг формы при hover
- **Эффект:** "Жидкое стекло" с сильным размытием (30px)
- **Glow:** Цветной ореол вокруг карточки

**CSS пример:**
```css
.liquid-blob-card {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(30px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
  padding: 32px 24px;
  box-shadow:
    0 8px 32px rgba(31, 38, 135, 0.2),
    inset 0 0 40px rgba(255, 255, 255, 0.03);
  transition: all 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

.liquid-blob-card:hover {
  border-radius: 70% 30% 30% 70% / 70% 70% 30% 30%;
  box-shadow:
    0 12px 48px rgba(102, 126, 234, 0.4),
    inset 0 0 60px rgba(102, 126, 234, 0.05);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 3: "Layered Depth Card" (ПРЕМИУМ 💎)

**Визуализация:**
```
┌───────────────────────────────────────────┐ ← Layer 3 (shadow)
│ ┌───────────────────────────────────────┐ │
│ │ ┌───────────────────────────────────┐ │ │ ← Layer 2 (blur)
│ │ │ ╔═══════════════════════════════╗ │ │ │
│ │ │ ║  ◯ Icon                       ║ │ │ │ ← Layer 1 (content)
│ │ │ ║  History                      ║ │ │ │
│ │ │ ║  Все расшифровки              ║ │ │ │
│ │ │ ╚═══════════════════════════════╝ │ │ │
│ │ └───────────────────────────────────┘ │ │
│ └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
  ↑ Multiple glass layers creating depth
```

**Форма:**
- **Радиус:** `20px` на всех слоях
- **Слои:** 3 слоя с разным blur (4px, 8px, 12px)
- **Эффект:** Глубина за счет многослойности
- **Анимация:** Слои немного двигаются при hover

**CSS пример:**
```css
.layered-depth-card {
  position: relative;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 24px;
}

.layered-depth-card::before,
.layered-depth-card::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 20px;
  pointer-events: none;
}

/* Layer 2 */
.layered-depth-card::before {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  transform: translate(-4px, -4px);
  z-index: -1;
}

/* Layer 3 */
.layered-depth-card::after {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(4px);
  transform: translate(-8px, -8px);
  z-index: -2;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.layered-depth-card:hover::before {
  transform: translate(-6px, -6px);
}

.layered-depth-card:hover::after {
  transform: translate(-12px, -12px);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 🔘 Кнопки (Buttons)

### Вариант 1: "Gradient Glass Button" (ОСНОВНОЙ ✅)

**Визуализация:**
```
┌──────────────────────────────────┐
│  ╔════════════════════════════╗  │
│  ║  Отправить сообщение  →   ║  │ ← Gradient fill
│  ╚════════════════════════════╝  │
│        ↑ Inner glow               │
└──────────────────────────────────┘
      ↑ Outer glow (pulsing)
```

**Форма:**
- **Радиус:** `16px` (средний, современный)
- **Высота:** `48px` (комфортная для touch)
- **Padding:** `16px 32px`
- **Градиент:** 135deg, от primary к темнее
- **Анимация:** Scale 1.05 + увеличение glow при hover

**CSS:**
```css
.gradient-glass-button {
  position: relative;
  height: 48px;
  padding: 0 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  color: white;
  font-weight: 600;
  font-size: 16px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow:
    0 4px 16px rgba(102, 126, 234, 0.4),
    inset 0 0 20px rgba(255, 255, 255, 0.1);
}

/* Glow effect */
.gradient-glass-button::before {
  content: '';
  position: absolute;
  inset: -4px;
  background: inherit;
  border-radius: 20px;
  filter: blur(12px);
  opacity: 0.6;
  z-index: -1;
}

.gradient-glass-button:hover {
  transform: scale(1.05);
  box-shadow:
    0 8px 24px rgba(102, 126, 234, 0.6),
    inset 0 0 30px rgba(255, 255, 255, 0.15);
}

.gradient-glass-button:active {
  transform: scale(0.98);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Liquid Pill Button" (PLAYFUL 🎨)

**Визuализация:**
```
  ╭──────────────────────────╮
 ╱                            ╲
│    Создать событие    +     │ ← Capsule shape
 ╲                            ╱
  ╰──────────────────────────╯
```

**Форма:**
- **Радиус:** `9999px` (полностью круглый)
- **Высота:** `44px`
- **Padding:** `16px 28px`
- **Эффект:** Liquid glass с сильным blur
- **Hover:** Морфинг + цветовой shift

**CSS:**
```css
.liquid-pill-button {
  height: 44px;
  padding: 0 28px;
  background: rgba(102, 126, 234, 0.15);
  backdrop-filter: blur(20px) saturate(180%);
  border: 2px solid rgba(102, 126, 234, 0.3);
  border-radius: 9999px;
  color: hsl(var(--primary));
  font-weight: 600;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  box-shadow:
    0 4px 12px rgba(102, 126, 234, 0.2),
    inset 0 0 20px rgba(102, 126, 234, 0.05);
}

.liquid-pill-button:hover {
  background: rgba(102, 126, 234, 0.25);
  border-color: rgba(102, 126, 234, 0.5);
  transform: scale(1.08);
  box-shadow:
    0 8px 24px rgba(102, 126, 234, 0.4),
    inset 0 0 40px rgba(102, 126, 234, 0.1);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 3: "Neumorphic Glass Button" (SOFT 🌙)

**Визуализация:**
```
    ┌────────────────────┐
   ╱  Сохранить  ✓      ╱│ ← Soft shadows
  ╱____________________╱ │   (inset + outset)
 │                      │╱
 └──────────────────────┘
```

**Форма:**
- **Радиус:** `12px`
- **Высота:** `50px`
- **Эффект:** Soft neumorphism + glass
- **Тени:** Двойные (светлая + темная)

**CSS:**
```css
.neumorphic-glass-button {
  height: 50px;
  padding: 0 30px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: hsl(var(--foreground));
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow:
    -4px -4px 12px rgba(255, 255, 255, 0.1),
    4px 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 0 20px rgba(255, 255, 255, 0.05);
}

.neumorphic-glass-button:hover {
  box-shadow:
    -6px -6px 16px rgba(255, 255, 255, 0.15),
    6px 6px 16px rgba(0, 0, 0, 0.15),
    inset 0 0 30px rgba(255, 255, 255, 0.08);
}

.neumorphic-glass-button:active {
  box-shadow:
    inset -2px -2px 8px rgba(255, 255, 255, 0.1),
    inset 2px 2px 8px rgba(0, 0, 0, 0.1);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 💬 Сообщения в чате (Chat Messages)

### Вариант 1: "Bubble Glass" (USER MESSAGE - РЕКОМЕНДУЕТСЯ ✨)

**Визуализация:**
```
                    ┌──────────────────────────┐
                    │  Привет, Tracy!          │
                    │  Как дела?               │
                    └──────────────────────────┘◣
                      ↑ Gradient fill + glow
```

**Форма:**
- **Радиус:** `20px 20px 4px 20px` (tail справа снизу)
- **Padding:** `14px 18px`
- **Max-width:** `80%`
- **Градиент:** Primary gradient
- **Glow:** Цветное свечение вокруг

**CSS:**
```css
.bubble-glass-user {
  position: relative;
  max-width: 80%;
  padding: 14px 18px;
  margin-left: auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px 20px 4px 20px;
  color: white;
  font-size: 15px;
  line-height: 1.5;
  box-shadow:
    0 4px 16px rgba(102, 126, 234, 0.3),
    0 0 24px rgba(102, 126, 234, 0.2);
  animation: bubble-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Outer glow */
.bubble-glass-user::before {
  content: '';
  position: absolute;
  inset: -3px;
  background: inherit;
  border-radius: inherit;
  filter: blur(10px);
  opacity: 0.5;
  z-index: -1;
}

@keyframes bubble-slide-in {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Frosted Glass" (ASSISTANT MESSAGE - ТРЕНДОВЫЙ 🔥)

**Визуализация:**
```
  ◢┌──────────────────────────────────┐
   │  Привет! Чем могу помочь?        │
   │  Расскажи о своих планах 📅      │
   └──────────────────────────────────┘
     ↑ Frosted glass with heavy blur
```

**Форма:**
- **Радиус:** `20px 20px 20px 4px` (tail слева снизу)
- **Padding:** `16px 20px`
- **Blur:** `30px` (сильное размытие)
- **Border:** Subtle светлая граница

**CSS:**
```css
.frosted-glass-assistant {
  position: relative;
  max-width: 85%;
  padding: 16px 20px;
  margin-right: auto;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(30px) saturate(200%);
  -webkit-backdrop-filter: blur(30px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px 20px 20px 4px;
  color: hsl(var(--foreground));
  font-size: 15px;
  line-height: 1.6;
  box-shadow:
    0 8px 24px rgba(31, 38, 135, 0.15),
    inset 0 0 30px rgba(255, 255, 255, 0.05);
  animation: bubble-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Shimmer effect on new message */
.frosted-glass-assistant.new::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.2) 50%,
    transparent 100%
  );
  border-radius: inherit;
  animation: shimmer 1s ease-out;
}

@keyframes shimmer {
  from { transform: translateX(-100%); }
  to { transform: translateX(100%); }
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 3: "Liquid Morph Bubble" (PLAYFUL - ЭКСПЕРИМЕНТАЛЬНЫЙ 🎭)

**Визуализация:**
```
      ╭─────────────────────╮
    ╱                         ╲
   │   Давай создам          │
   │   событие!              │
    ╲                         ╱
      ╰─────────────────────╯
        ↑ Organic shape
```

**Форма:**
- **Радиус:** Органический (меняется при появлении)
- **Анимация:** Морфинг формы при входе
- **Эффект:** Жидкое стекло

**CSS:**
```css
.liquid-morph-bubble {
  max-width: 80%;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50% 50% 50% 10% / 50% 50% 10% 50%;
  color: hsl(var(--foreground));
  animation: liquid-morph 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes liquid-morph {
  0% {
    opacity: 0;
    border-radius: 50% 50% 50% 50%;
    transform: scale(0.8);
  }
  50% {
    border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
    transform: scale(1.05);
  }
  100% {
    opacity: 1;
    border-radius: 50% 50% 50% 10% / 50% 50% 10% 50%;
    transform: scale(1);
  }
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 📝 Инпуты (Input Fields)

### Вариант 1: "Focus Glow Input" (ОСНОВНОЙ ✅)

**Визуализация:**
```
Normal state:
┌──────────────────────────────────────┐
│  Введите сообщение...                │
└──────────────────────────────────────┘

Focus state:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ ← Glowing border
┃  |                                   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    ↑ Animated glow (pulsing)
```

**Форма:**
- **Радиус:** `16px`
- **Высота:** `56px` (textarea min-height)
- **Border:** 2px при focus
- **Glow:** Многослойный при focus (0-40px)

**CSS:**
```css
.focus-glow-input {
  width: 100%;
  min-height: 56px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  color: hsl(var(--foreground));
  font-size: 16px;
  font-family: inherit;
  resize: none;
  transition: all 0.3s ease;
}

.focus-glow-input::placeholder {
  color: hsl(var(--muted-foreground));
  transition: color 0.3s ease;
}

.focus-glow-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: hsl(var(--primary));
  box-shadow:
    0 0 0 4px rgba(102, 126, 234, 0.1),
    0 0 20px rgba(102, 126, 234, 0.3),
    0 0 40px rgba(102, 126, 234, 0.15),
    inset 0 0 20px rgba(102, 126, 234, 0.05);
  animation: glow-pulse 2s ease-in-out infinite;
}

.focus-glow-input:focus::placeholder {
  color: transparent;
}

@keyframes glow-pulse {
  0%, 100% {
    box-shadow:
      0 0 0 4px rgba(102, 126, 234, 0.1),
      0 0 20px rgba(102, 126, 234, 0.3),
      0 0 40px rgba(102, 126, 234, 0.15);
  }
  50% {
    box-shadow:
      0 0 0 6px rgba(102, 126, 234, 0.15),
      0 0 30px rgba(102, 126, 234, 0.4),
      0 0 60px rgba(102, 126, 234, 0.2);
  }
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Floating Label Glass Input" (PREMIUM 💎)

**Визуализация:**
```
Empty:
┌──────────────────────────────────────┐
│  Ваше сообщение                      │
└──────────────────────────────────────┘

Filled:
   Ваше сообщение ← Floating label (small)
┌──────────────────────────────────────┐
│  Привет, Tracy!                      │
└──────────────────────────────────────┘
```

**Форма:**
- **Радиус:** `18px`
- **Label:** Анимация вверх при фокусе
- **Эффект:** Liquid glass с gradient border

**CSS:**
```css
.floating-label-wrapper {
  position: relative;
}

.floating-glass-input {
  width: 100%;
  min-height: 60px;
  padding: 20px 20px 8px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(15px) saturate(180%);
  border: 2px solid transparent;
  border-radius: 18px;
  color: hsl(var(--foreground));
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.03);
}

.floating-label {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: hsl(var(--muted-foreground));
  font-size: 16px;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-glass-input:focus,
.floating-glass-input:not(:placeholder-shown) {
  background: rgba(255, 255, 255, 0.08);
  border-image: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.6),
    rgba(118, 75, 162, 0.6)
  ) 1;
  box-shadow:
    0 0 20px rgba(102, 126, 234, 0.2),
    inset 0 0 30px rgba(102, 126, 234, 0.05);
}

.floating-glass-input:focus + .floating-label,
.floating-glass-input:not(:placeholder-shown) + .floating-label {
  top: 12px;
  font-size: 12px;
  color: hsl(var(--primary));
  font-weight: 600;
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 🪟 Модальные окна (Modals)

### Вариант 1: "Centered Glass Modal" (ОСНОВНОЙ ✅)

**Визуализация:**
```
████████████████████████████████████████
████████████████████████████████████████ ← Backdrop blur
████████┌─────────────────────┐█████████
████████│  ╔═══════════════╗  │█████████
████████│  ║               ║  │█████████
████████│  ║   Событие     ║  │█████████
████████│  ║               ║  │█████████
████████│  ║   [Детали]    ║  │█████████
████████│  ║               ║  │█████████
████████│  ║   [×] Закрыть ║  │█████████
████████│  ╚═══════════════╝  │█████████
████████└─────────────────────┘█████████
████████████████████████████████████████
```

**Форма:**
- **Радиус:** `28px` (очень мягкий)
- **Max-width:** `500px`
- **Padding:** `32px`
- **Backdrop:** blur(20px)
- **Анимация:** Scale + fade in

**CSS:**
```css
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(20px) saturate(120%);
  -webkit-backdrop-filter: blur(20px) saturate(120%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
  animation: backdrop-fade-in 0.3s ease;
}

.centered-glass-modal {
  position: relative;
  width: 100%;
  max-width: 500px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 28px;
  padding: 32px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.4),
    inset 0 0 40px rgba(255, 255, 255, 0.05);
  animation: modal-scale-in 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}

@keyframes backdrop-fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes modal-scale-in {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Bottom Sheet Glass Modal" (MOBILE-FIRST 📱)

**Визуализация:**
```
████████████████████████████████████████
████████████████████████████████████████
████████████████████████████████████████
████████████████████████████████████████
╔══════════════════════════════════════╗
║  ═══  ← Handle                       ║
║                                      ║
║  Детали события                     ║
║  ────────────────                   ║
║  📅 25 января 2026                  ║
║  🕐 14:00 - 15:00                   ║
║                                      ║
╚══════════════════════════════════════╝
```

**Форма:**
- **Радиус:** `32px 32px 0 0` (только сверху)
- **Position:** Fixed bottom
- **Handle:** Centered pill (40x4px)
- **Swipe:** Жест вниз для закрытия

**CSS:**
```css
.bottom-sheet-glass {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 85vh;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-bottom: none;
  border-radius: 32px 32px 0 0;
  padding: 24px 20px;
  box-shadow:
    0 -20px 60px rgba(0, 0, 0, 0.3),
    inset 0 0 40px rgba(255, 255, 255, 0.05);
  animation: sheet-slide-up 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Handle */
.bottom-sheet-glass::before {
  content: '';
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

@keyframes sheet-slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 📅 События календаря (Calendar Events)

### Вариант 1: "Side Accent Glass Event" (РЕКОМЕНДУЕТСЯ ✨)

**Визуализация:**
```
┃ ┌──────────────────────────────────┐
┃ │  Встреча с командой              │
┃ │  14:00 - 15:00                   │
┃ └──────────────────────────────────┘
↑ Colored accent (4px gradient)
```

**Форма:**
- **Радиус:** `12px`
- **Border-left:** 4px с цветом события
- **Hover:** Сдвиг вправо + усиление glow

**CSS:**
```css
.side-accent-glass-event {
  position: relative;
  padding: 14px 16px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-left: 4px solid var(--event-color, #667eea);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.side-accent-glass-event:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateX(6px);
  box-shadow:
    -6px 0 16px var(--event-color-alpha, rgba(102, 126, 234, 0.3)),
    0 4px 16px rgba(0, 0, 0, 0.1);
}

/* Gradient на accent border при hover */
.side-accent-glass-event:hover {
  border-left-width: 4px;
  border-image: linear-gradient(
    180deg,
    var(--event-color),
    var(--event-color-light)
  ) 1;
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Pill Badge Event" (COMPACT 🎯)

**Визуализация:**
```
┌─────────────────────────────────────────┐
│  ╭───────╮                               │
│  │ 14:00 │  Встреча с командой      ───→│
│  ╰───────╯                               │
└─────────────────────────────────────────┘
   ↑ Time pill badge
```

**Форма:**
- **Радиус:** `16px`
- **Time badge:** Rounded pill с gradient
- **Compact:** Меньше padding

**CSS:**
```css
.pill-badge-event {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 6px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pill-badge-event .time-pill {
  flex-shrink: 0;
  padding: 6px 12px;
  background: linear-gradient(135deg,
    var(--event-color, #667eea),
    var(--event-color-dark, #764ba2)
  );
  border-radius: 9999px;
  font-size: 13px;
  font-weight: 600;
  color: white;
  box-shadow:
    0 0 12px var(--event-color-alpha, rgba(102, 126, 234, 0.4)),
    inset 0 0 8px rgba(255, 255, 255, 0.2);
}

.pill-badge-event:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 🧭 Навигация (Navigation)

### Вариант 1: "Glass Top Bar" (HEADER - РЕКОМЕНДУЕТСЯ ✅)

**Визуализация:**
```
╔═══════════════════════════════════════════╗
║  ←  👤 TRACY                      ⚙  ☰   ║
╚═══════════════════════════════════════════╝
    ↑ Frosted glass with backdrop blur
```

**Форма:**
- **Высота:** `64px`
- **Border-bottom:** 1px с opacity
- **Blur:** Strong (20px)
- **Sticky:** position: sticky, top: 0

**CSS:**
```css
.glass-top-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

/* Gradient underline при scroll */
.glass-top-bar.scrolled::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  opacity: 0.6;
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

### Вариант 2: "Floating Tab Bar" (MOBILE NAV - ТРЕНДОВЫЙ 🔥)

**Визуализация:**
```
     ╔═══════════════════════════════╗
     ║  📅    💬    📝    👤    ⚙   ║
     ╚═══════════════════════════════╝
       ↑ Floating glass pill navigation
```

**Форма:**
- **Радиус:** `32px` (полностью округлый)
- **Position:** Fixed bottom с margin
- **Эффект:** Floating с shadow
- **Items:** 5 равномерно распределенных

**CSS:**
```css
.floating-tab-bar {
  position: fixed;
  bottom: 20px;
  left: 20px;
  right: 20px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(30px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 32px;
  padding: 0 12px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.2),
    inset 0 0 40px rgba(255, 255, 255, 0.05);
  z-index: 100;
}

.floating-tab-bar .tab-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-tab-bar .tab-item.active {
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow:
    0 4px 16px rgba(102, 126, 234, 0.4),
    inset 0 0 20px rgba(255, 255, 255, 0.15);
}

.floating-tab-bar .tab-item:not(.active):hover {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.1);
}
```

**👍 Подтвердите этот вариант?** `[ ] ДА  [ ] НЕТ  [ ] ИЗМЕНИТЬ`

---

## 📊 Сводная таблица рекомендаций

| Элемент | Рекомендуемый вариант | Форма | Ключевые фичи |
|---------|----------------------|-------|---------------|
| **Карточки функций** | Floating Glass Card | 24px radius | Gradient border, outer glow, hover lift |
| **Кнопки основные** | Gradient Glass Button | 16px radius, 48px height | Inner+outer glow, scale hover |
| **Кнопки вторичные** | Liquid Pill Button | 9999px (capsule) | Morph effect, color shift |
| **Сообщения User** | Bubble Glass | 20/20/4/20px radius | Gradient fill, colored glow |
| **Сообщения Assistant** | Frosted Glass | 20/20/20/4px radius | Heavy blur (30px), shimmer |
| **Инпуты** | Focus Glow Input | 16px radius, 56px height | Multi-layer glow, pulse animation |
| **Модалы Desktop** | Centered Glass Modal | 28px radius | Backdrop blur, scale animation |
| **Модалы Mobile** | Bottom Sheet Glass | 32/32/0/0px radius | Swipe handle, slide-up |
| **События календаря** | Side Accent Glass Event | 12px radius | 4px colored border-left, slide hover |
| **Навигация Header** | Glass Top Bar | No radius, 64px height | Strong blur, gradient underline |
| **Навигация Mobile** | Floating Tab Bar | 32px radius (pill) | Floating, gradient active state |

---

## ✅ Форма подтверждения

**Пожалуйста, отметьте ваши предпочтения для каждого элемента:**

### Карточки функций:
- [ ] Вариант 1: Floating Glass Card ✨
- [ ] Вариант 2: Liquid Blob Card 🔥
- [ ] Вариант 3: Layered Depth Card 💎
- [ ] Свой вариант: _______________

### Кнопки:
- [ ] Вариант 1: Gradient Glass Button ✅
- [ ] Вариант 2: Liquid Pill Button 🎨
- [ ] Вариант 3: Neumorphic Glass Button 🌙
- [ ] Свой вариант: _______________

### Сообщения в чате (User):
- [ ] Вариант 1: Bubble Glass ✨
- [ ] Вариант 2: Alternative
- [ ] Свой вариант: _______________

### Сообщения в чате (Assistant):
- [ ] Вариант 1: Frosted Glass 🔥
- [ ] Вариант 2: Liquid Morph Bubble 🎭
- [ ] Свой вариант: _______________

### Инпуты:
- [ ] Вариант 1: Focus Glow Input ✅
- [ ] Вариант 2: Floating Label Glass Input 💎
- [ ] Свой вариант: _______________

### Модальные окна:
- [ ] Вариант 1: Centered Glass Modal ✅
- [ ] Вариант 2: Bottom Sheet Glass Modal 📱
- [ ] Оба варианта (разные устройства)
- [ ] Свой вариант: _______________

### События календаря:
- [ ] Вариант 1: Side Accent Glass Event ✨
- [ ] Вариант 2: Pill Badge Event 🎯
- [ ] Свой вариант: _______________

### Навигация:
- [ ] Вариант 1: Glass Top Bar ✅
- [ ] Вариант 2: Floating Tab Bar 🔥
- [ ] Оба варианта (разные устройства)
- [ ] Свой вариант: _______________

---

**После подтверждения я сразу начну внедрение выбранных вариантов в код! 🚀**
