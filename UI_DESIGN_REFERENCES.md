# 🎨 Примеры современных проектов и дизайнерские решения

## 📚 Содержание
1. [Вдохновляющие проекты](#вдохновляющие-проекты)
2. [Дизайнерские решения с Glow эффектами](#дизайнерские-решения-с-glow-эффектами)
3. [Glassmorphism примеры](#glassmorphism-примеры)
4. [Градиенты и размытия](#градиенты-и-размытия)
5. [Готовые CSS примеры](#готовые-css-примеры)

---

## 🌟 Вдохновляющие проекты

### AI Assistant Dashboards на Dribbble

#### 1. Prodify - AI Assistant Dashboard
- **Ссылка:** [Dribbble - Prodify](https://dribbble.com/shots/25377626-Prodify-AI-Assistant-Dashboard-Tech-UI-Design)
- **Студия:** Phenomenon Studio
- **Особенности:** Современный tech UI с градиентами, glassmorphism карточками
- **Что взять:** Структуру dashboard, компоновку карточек, цветовую палитру

#### 2. Avino AI - Smart AI Assistant
- **Ссылка:** [Dribbble - AI Assistant UI](https://dribbble.com/tags/ai-assistant-ui)
- **Особенности:** Минималистичный дизайн с акцентом на функциональность
- **Что взять:** Типографику, spacing, иконки

#### 3. LoopAI - CRM Dashboard для B2B SaaS
- **Студия:** Phenomenon Studio
- **Особенности:** Профессиональный SaaS интерфейс с аналитикой
- **Что взять:** Графики, таблицы, data visualization

#### 4. Cyclops - Influencers Marketing AI Dashboard
- **Студия:** Dipa Inhouse
- **Особенности:** Яркие акценты, современные карточки
- **Что взять:** Цветовые акценты, layout карточек

### Больше AI Dashboard примеров:
- [Dribbble - AI Dashboard Gallery (300+ дизайнов)](https://dribbble.com/tags/ai-dashboard)
- [Dribbble - Modern Dashboard (400+ дизайнов)](https://dribbble.com/tags/modern-dashboard)

### AI Assistant Projects на Behance

#### 1. NeuralHub - AI Analytics & Model Management
- **Ссылка:** [Behance - AI Dashboard Projects](https://www.behance.net/search/projects/ui%20dashboard%20design%20artificial%20intelligence)
- **Особенности:** Сложная аналитика, темная тема
- **Что взять:** Dark mode палитру, визуализацию данных

#### 2. Zenith.Pro - AI-Powered SaaS Dashboard
- **Особенности:** Clean интерфейс, focus на UX
- **Что взять:** Навигацию, структуру меню

#### 3. NeuroNest - Startup LLM AI SaaS Tool
- **Особенности:** Startup-friendly дизайн, современные тренды
- **Что взять:** Onboarding flow, welcome screens

### Calendar UI References

#### Лучшие примеры Calendar UI:
- **Ссылка:** [Calendar UI Examples - 33 Inspiring Designs](https://www.eleken.co/blog-posts/calendar-ui)
- **Ссылка:** [10 Calendar UI Examples for Scheduling](https://bricxlabs.com/blogs/calendar-ui-examples)

**Ключевые примеры:**
1. **Smart Calendar** - мягкие градиенты, скругленные углы
2. **Duolingo Calendar** - glowing cells для streak'ов
3. **Things 3** - subtle gradient для текущей даты
4. **Google Calendar** - минималистичный, функциональный

### Chat/Messenger UI

#### Glassmorphism Chat Examples:
- **Ссылка:** [Glassmorphism Chat Bubble Tutorial](https://glasp.co/youtube/p/glassmorphism-chat-bubble-illustration-tutorial-free-ui-design-tutorial)
- **Ссылка:** [12 Glassmorphism UI Features & Examples](https://uxpilot.ai/blogs/glassmorphism-ui)

---

## ✨ Дизайнерские решения с Glow эффектами

### 1. Neon Glow для кнопок и карточек

#### CSS код:
```css
/* Базовый neon glow */
.neon-button {
  position: relative;
  padding: 16px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  /* Основной glow */
  box-shadow:
    0 0 20px rgba(102, 126, 234, 0.5),
    0 0 40px rgba(102, 126, 234, 0.3),
    0 0 60px rgba(102, 126, 234, 0.2);
}

.neon-button:hover {
  transform: translateY(-2px);
  box-shadow:
    0 0 30px rgba(102, 126, 234, 0.7),
    0 0 60px rgba(102, 126, 234, 0.5),
    0 0 90px rgba(102, 126, 234, 0.3);
}

.neon-button:active {
  transform: translateY(0);
}
```

#### Применение для TRACY:
```tsx
<Button className="neon-button">
  Отправить сообщение
</Button>
```

### 2. Pulsing Glow для уведомлений

```css
@keyframes pulse-glow {
  0%, 100% {
    box-shadow:
      0 0 20px rgba(102, 126, 234, 0.4),
      0 0 40px rgba(102, 126, 234, 0.2);
  }
  50% {
    box-shadow:
      0 0 30px rgba(102, 126, 234, 0.6),
      0 0 60px rgba(102, 126, 234, 0.4);
  }
}

.notification-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 50%;
  color: white;
  font-size: 11px;
  font-weight: 700;
  animation: pulse-glow 2s ease-in-out infinite;
}
```

### 3. Border Glow эффект

```css
.glow-border-card {
  position: relative;
  padding: 24px;
  background: hsl(var(--card));
  border-radius: 24px;
  overflow: hidden;
}

.glow-border-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 24px;
  padding: 2px;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.8),
    rgba(118, 75, 162, 0.8),
    rgba(240, 147, 251, 0.8)
  );
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.glow-border-card:hover::before {
  opacity: 1;
}
```

### 4. Animated Gradient Glow

```css
@keyframes gradient-glow {
  0%, 100% {
    background-position: 0% 50%;
    box-shadow:
      0 0 30px rgba(102, 126, 234, 0.5),
      0 0 60px rgba(102, 126, 234, 0.3);
  }
  50% {
    background-position: 100% 50%;
    box-shadow:
      0 0 40px rgba(240, 147, 251, 0.6),
      0 0 80px rgba(240, 147, 251, 0.4);
  }
}

.animated-glow-card {
  background: linear-gradient(
    270deg,
    hsl(260, 85%, 65%),
    hsl(280, 75%, 60%),
    hsl(330, 85%, 70%)
  );
  background-size: 200% 200%;
  animation: gradient-glow 8s ease infinite;
  border-radius: 24px;
  padding: 32px;
}
```

### 5. Inner Glow для инпутов

```css
.glow-input {
  width: 100%;
  padding: 14px 20px;
  background: hsl(var(--card));
  border: 2px solid transparent;
  border-radius: 16px;
  font-size: 16px;
  transition: all 0.3s ease;

  /* Inner glow при focus */
  box-shadow: inset 0 0 0 rgba(102, 126, 234, 0);
}

.glow-input:focus {
  outline: none;
  border-color: hsl(var(--primary));
  box-shadow:
    inset 0 0 20px rgba(102, 126, 234, 0.1),
    0 0 20px rgba(102, 126, 234, 0.3);
}

.glow-input:focus::placeholder {
  color: transparent;
}
```

### 6. Text Glow эффект

```css
.glow-text {
  font-size: 48px;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;

  /* Text glow */
  filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.6))
          drop-shadow(0 0 40px rgba(102, 126, 234, 0.4));
}

/* Animated text glow */
@keyframes text-glow-pulse {
  0%, 100% {
    filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.6));
  }
  50% {
    filter: drop-shadow(0 0 30px rgba(102, 126, 234, 0.9));
  }
}

.animated-glow-text {
  animation: text-glow-pulse 2s ease-in-out infinite;
}
```

---

## 🔮 Glassmorphism примеры

### Источники и генераторы:
- [Glass UI Generator](https://ui.glass/generator/) - интерактивный генератор
- [10 Mind-Blowing Glassmorphism Examples](https://onyx8agency.com/blog/glassmorphism-inspiring-examples/)
- [60 CSS Glassmorphism Examples](https://freefrontend.com/css-glassmorphism/)
- [44 CSS Glassmorphism Examples You Can Use](https://wpdean.com/css-glassmorphism/)

### 1. Классический Glassmorphism

```css
.glass-card {
  /* Фон с прозрачностью */
  background: rgba(255, 255, 255, 0.1);

  /* Основное размытие фона */
  backdrop-filter: blur(10px) saturate(180%);
  -webkit-backdrop-filter: blur(10px) saturate(180%);

  /* Граница */
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;

  /* Тень для глубины */
  box-shadow:
    0 8px 32px 0 rgba(31, 38, 135, 0.15),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);

  /* Контент */
  padding: 32px;
}

/* Для темной темы */
.dark .glass-card {
  background: rgba(30, 35, 48, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 8px 32px 0 rgba(0, 0, 0, 0.3),
    inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}
```

### 2. Heavy Blur Glassmorphism (для сложных фонов)

```css
.glass-heavy {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(30px) saturate(200%);
  -webkit-backdrop-filter: blur(30px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  box-shadow:
    0 8px 32px 0 rgba(31, 38, 135, 0.2),
    0 4px 8px 0 rgba(0, 0, 0, 0.05);
}
```

### 3. Colorful Glassmorphism

```css
.glass-colorful-purple {
  background: rgba(102, 126, 234, 0.1);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  box-shadow:
    0 8px 32px 0 rgba(102, 126, 234, 0.2),
    inset 0 0 40px rgba(102, 126, 234, 0.05);
}

.glass-colorful-pink {
  background: rgba(240, 147, 251, 0.1);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(240, 147, 251, 0.2);
  border-radius: 20px;
  box-shadow:
    0 8px 32px 0 rgba(240, 147, 251, 0.2),
    inset 0 0 40px rgba(240, 147, 251, 0.05);
}
```

### 4. Glassmorphism с градиентом

```css
.glass-gradient {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.05) 100%
  );
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid transparent;
  border-image: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.3),
    rgba(255, 255, 255, 0.1)
  ) 1;
  border-radius: 24px;
  position: relative;
  overflow: hidden;
}

/* Добавляем внутренний градиент */
.glass-gradient::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    135deg,
    rgba(102, 126, 234, 0.05) 0%,
    rgba(240, 147, 251, 0.05) 100%
  );
  border-radius: 24px;
  pointer-events: none;
}
```

### 5. Layered Glassmorphism (многослойный)

```css
.glass-layered {
  position: relative;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 20px;
  padding: 32px;
}

/* Первый слой */
.glass-layered::before {
  content: '';
  position: absolute;
  inset: 4px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 16px;
  z-index: -1;
}

/* Второй слой */
.glass-layered::after {
  content: '';
  position: absolute;
  inset: 8px;
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  border-radius: 12px;
  z-index: -2;
}
```

### 6. Glassmorphism для чата (Chat bubbles)

```css
/* Сообщение пользователя */
.glass-message-user {
  background: rgba(102, 126, 234, 0.15);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 20px 20px 4px 20px;
  padding: 14px 18px;
  margin-left: auto;
  max-width: 80%;
  box-shadow:
    0 4px 16px rgba(102, 126, 234, 0.2),
    inset 0 0 20px rgba(102, 126, 234, 0.05);
}

/* Сообщение ассистента */
.glass-message-assistant {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px 20px 20px 4px;
  padding: 14px 18px;
  margin-right: auto;
  max-width: 80%;
  box-shadow:
    0 4px 16px rgba(31, 38, 135, 0.15),
    inset 0 0 20px rgba(255, 255, 255, 0.05);
}
```

---

## 🌈 Градиенты и размытия

### Современные градиентные палитры 2026

#### 1. Purple Haze (Фиолетовая дымка)
```css
.gradient-purple-haze {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
}

/* С размытием по краям */
.gradient-purple-blur {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.gradient-purple-blur::before {
  content: '';
  position: absolute;
  inset: -20px;
  background: inherit;
  filter: blur(40px);
  opacity: 0.5;
  z-index: -1;
}
```

#### 2. Ocean Breeze (Океанский бриз)
```css
.gradient-ocean {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #43e97b 100%);
}

/* Анимированный */
@keyframes ocean-wave {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.gradient-ocean-animated {
  background: linear-gradient(
    270deg,
    #4facfe,
    #00f2fe,
    #43e97b,
    #4facfe
  );
  background-size: 300% 300%;
  animation: ocean-wave 10s ease infinite;
}
```

#### 3. Sunset Glow (Закатное сияние)
```css
.gradient-sunset {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 50%, #f093fb 100%);
}

/* С радиальным размытием */
.gradient-sunset-radial {
  background:
    radial-gradient(circle at 20% 50%, rgba(250, 112, 154, 0.3) 0%, transparent 50%),
    radial-gradient(circle at 80% 50%, rgba(254, 225, 64, 0.3) 0%, transparent 50%),
    linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}
```

#### 4. Cyberpunk (Киберпанк)
```css
.gradient-cyberpunk {
  background: linear-gradient(135deg, #ff0080 0%, #7928ca 50%, #0070f3 100%);
}

/* С neon glow */
.gradient-cyberpunk-glow {
  background: linear-gradient(135deg, #ff0080 0%, #7928ca 50%, #0070f3 100%);
  box-shadow:
    0 0 40px rgba(255, 0, 128, 0.5),
    0 0 80px rgba(121, 40, 202, 0.3),
    0 0 120px rgba(0, 112, 243, 0.2);
}
```

#### 5. Aurora Borealis (Северное сияние)
```css
.gradient-aurora {
  background: linear-gradient(
    135deg,
    #00c9ff 0%,
    #92fe9d 20%,
    #00f260 40%,
    #0575e6 60%,
    #667eea 80%,
    #764ba2 100%
  );
}

/* Анимированное северное сияние */
@keyframes aurora-shift {
  0%, 100% {
    background-position: 0% 50%;
    filter: hue-rotate(0deg) saturate(100%);
  }
  50% {
    background-position: 100% 50%;
    filter: hue-rotate(30deg) saturate(120%);
  }
}

.gradient-aurora-animated {
  background: linear-gradient(
    270deg,
    #00c9ff, #92fe9d, #00f260, #0575e6, #667eea, #764ba2
  );
  background-size: 400% 400%;
  animation: aurora-shift 15s ease infinite;
}
```

### Mesh Gradients (Сеточные градиенты)

```css
.gradient-mesh-smooth {
  background:
    radial-gradient(at 0% 0%, rgba(102, 126, 234, 0.3) 0px, transparent 50%),
    radial-gradient(at 50% 0%, rgba(118, 75, 162, 0.3) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(240, 147, 251, 0.3) 0px, transparent 50%),
    radial-gradient(at 0% 50%, rgba(79, 172, 254, 0.3) 0px, transparent 50%),
    radial-gradient(at 100% 50%, rgba(0, 242, 254, 0.3) 0px, transparent 50%),
    radial-gradient(at 0% 100%, rgba(67, 233, 123, 0.3) 0px, transparent 50%),
    radial-gradient(at 50% 100%, rgba(254, 225, 64, 0.3) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(250, 112, 154, 0.3) 0px, transparent 50%),
    hsl(var(--background));
}

/* Анимированный mesh */
@keyframes mesh-float {
  0%, 100% {
    background-position:
      0% 0%, 50% 0%, 100% 0%,
      0% 50%, 100% 50%,
      0% 100%, 50% 100%, 100% 100%;
  }
  50% {
    background-position:
      5% 5%, 45% 5%, 95% 5%,
      5% 50%, 95% 50%,
      5% 95%, 55% 95%, 95% 95%;
  }
}

.gradient-mesh-animated {
  /* ... same radial gradients ... */
  animation: mesh-float 20s ease-in-out infinite;
}
```

### Gradient Blur (Градиентное размытие)

```css
.gradient-blur-background {
  position: relative;
  overflow: hidden;
  background: hsl(var(--background));
}

.gradient-blur-background::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background:
    radial-gradient(circle at 30% 40%, rgba(102, 126, 234, 0.4) 0%, transparent 40%),
    radial-gradient(circle at 70% 60%, rgba(240, 147, 251, 0.4) 0%, transparent 40%);
  filter: blur(80px);
  animation: gradient-blur-move 20s ease-in-out infinite;
  z-index: 0;
}

@keyframes gradient-blur-move {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  33% { transform: translate(10%, -10%) rotate(120deg); }
  66% { transform: translate(-10%, 10%) rotate(240deg); }
}

.gradient-blur-background > * {
  position: relative;
  z-index: 1;
}
```

---

## 💻 Готовые CSS примеры для TRACY

### 1. Карточка функции на главной странице

```css
.feature-card {
  position: relative;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 24px;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

/* Градиентная полоска сверху */
.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  opacity: 0.8;
}

/* Hover эффект */
.feature-card:hover {
  transform: translateY(-4px);
  border-color: rgba(102, 126, 234, 0.3);
  box-shadow:
    0 8px 24px rgba(102, 126, 234, 0.2),
    0 0 40px rgba(102, 126, 234, 0.1);
}

/* Градиентное свечение при hover */
.feature-card:hover::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at var(--mouse-x) var(--mouse-y),
    rgba(102, 126, 234, 0.1) 0%,
    transparent 50%
  );
  pointer-events: none;
}

/* Иконка функции */
.feature-card .icon-wrapper {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.feature-card:hover .icon-wrapper {
  transform: scale(1.1) rotate(5deg);
}

/* Свечение иконки */
.feature-card .icon-wrapper::before {
  content: '';
  position: absolute;
  inset: -4px;
  background: inherit;
  border-radius: 18px;
  filter: blur(12px);
  opacity: 0.6;
  z-index: -1;
}
```

### 2. Сообщение в чате

```css
/* Сообщение пользователя */
.chat-message-user {
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 20px 20px 4px 20px;
  padding: 14px 18px;
  margin-left: auto;
  max-width: 80%;
  color: white;
  box-shadow:
    0 4px 12px rgba(102, 126, 234, 0.3),
    0 0 20px rgba(102, 126, 234, 0.2);
  animation: message-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* Свечение вокруг сообщения */
.chat-message-user::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: inherit;
  border-radius: inherit;
  filter: blur(8px);
  opacity: 0.5;
  z-index: -1;
}

/* Сообщение ассистента - glassmorphism */
.chat-message-assistant {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px 20px 20px 4px;
  padding: 14px 18px;
  margin-right: auto;
  max-width: 80%;
  box-shadow:
    0 4px 16px rgba(31, 38, 135, 0.1),
    inset 0 0 20px rgba(255, 255, 255, 0.03);
  animation: message-slide-in 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes message-slide-in {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
```

### 3. Событие в календаре

```css
.calendar-event {
  position: relative;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-left: 4px solid var(--event-color, #667eea);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.calendar-event:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateX(4px);
  box-shadow:
    -4px 0 12px var(--event-color-alpha, rgba(102, 126, 234, 0.3)),
    0 4px 12px rgba(0, 0, 0, 0.1);
}

/* Индикатор времени с glow */
.calendar-event .time-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--event-color, #667eea);
  box-shadow:
    0 0 12px var(--event-color-alpha, rgba(102, 126, 234, 0.2)),
    inset 0 0 8px var(--event-color-alpha, rgba(102, 126, 234, 0.05));
}
```

### 4. Input с glow при focus

```css
.input-glow {
  width: 100%;
  padding: 14px 20px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  font-size: 16px;
  color: hsl(var(--foreground));
  transition: all 0.3s ease;
}

.input-glow::placeholder {
  color: hsl(var(--muted-foreground));
  transition: color 0.3s ease;
}

.input-glow:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow:
    0 0 0 4px rgba(102, 126, 234, 0.1),
    0 0 20px rgba(102, 126, 234, 0.3),
    0 0 40px rgba(102, 126, 234, 0.15),
    inset 0 0 20px rgba(102, 126, 234, 0.05);
}

.input-glow:focus::placeholder {
  color: transparent;
}
```

### 5. Animated Background для страниц

```css
.page-background-animated {
  position: fixed;
  inset: 0;
  background: hsl(var(--background));
  overflow: hidden;
  z-index: -1;
}

.page-background-animated::before,
.page-background-animated::after {
  content: '';
  position: absolute;
  width: 500px;
  height: 500px;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.15;
  animation: float-blob 20s ease-in-out infinite;
}

.page-background-animated::before {
  top: -200px;
  left: -200px;
  background: radial-gradient(circle, #667eea, transparent);
  animation-delay: 0s;
}

.page-background-animated::after {
  bottom: -200px;
  right: -200px;
  background: radial-gradient(circle, #f093fb, transparent);
  animation-delay: -10s;
}

@keyframes float-blob {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(100px, -100px) scale(1.1); }
  66% { transform: translate(-100px, 100px) scale(0.9); }
}

/* Добавляем третий blob для большей динамики */
.page-background-animated .blob-extra {
  position: absolute;
  width: 400px;
  height: 400px;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, #764ba2, transparent);
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.1;
  animation: float-blob 25s ease-in-out infinite;
  animation-delay: -5s;
}
```

---

## 📚 Дополнительные ресурсы

### Тренды дизайна 2026:
- [9 Mobile App Design Trends for 2026](https://uxpilot.ai/blogs/mobile-app-design-trends)
- [UI UX Trends 2026: 7 Game-Changing Shifts](https://ultimez.com/blog/designing/ui-ux-trends-2026-7-game-changing-shifts-with-expert-insights/)
- [12 UI/UX Design Trends That Will Dominate 2026](https://www.index.dev/blog/ui-ux-design-trends)
- [Graphic Design Trends 2026: AI Meets Human](https://reallygooddesigns.com/graphic-design-trends-2026/)

### Инструменты и генераторы:
- [Glass UI Generator](https://ui.glass/generator/) - генератор glassmorphism
- [47 Best Glowing Effects in CSS](https://www.testmu.ai/blog/glowing-effects-in-css/)
- [Eye-Catching Mobile App Interfaces with Gradient Effect](https://designmodo.com/mobile-apps-gradient-effect/)
- [Modern App Colors: Design Palettes That Work In 2026](https://webosmotic.com/blog/modern-app-colors/)

### Обучение и туториалы:
- [How to implement glassmorphism with CSS - LogRocket](https://blog.logrocket.com/implement-glassmorphism-css/)
- [Glassmorphism: Definition and Best Practices - Nielsen Norman Group](https://www.nngroup.com/articles/glassmorphism/)
- [How Glassmorphism in UX Is Reshaping Modern Interfaces](https://clay.global/blog/glassmorphism-ui)

---

## ✅ Чек-лист применения для TRACY

### Приоритет 1 (немедленно):
- [ ] Применить glassmorphism для карточек на главной странице
- [ ] Добавить glow эффекты для кнопок
- [ ] Обновить сообщения в чате с размытием фона
- [ ] Добавить анимированный фон на главной странице

### Приоритет 2 (после базовых изменений):
- [ ] Улучшить события календаря с border glow
- [ ] Добавить input glow для всех полей ввода
- [ ] Создать анимированные градиенты для заголовков
- [ ] Добавить micro-interactions с scale и glow

### Приоритет 3 (полировка):
- [ ] Mesh gradients для фонов страниц
- [ ] Layered glassmorphism для модальных окон
- [ ] Animated gradient borders для premium элементов
- [ ] Pulsing glow для уведомлений и индикаторов

---

**Автор:** Claude AI Assistant
**Дата:** 2026-01-15
**Проект:** TRACY AI BOT - UI Design References

🎨 Используйте эти примеры как вдохновение и отправную точку для создания современного, привлекательного интерфейса!
