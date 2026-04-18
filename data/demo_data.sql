-- Пример SQL для ручного импорта (основной сид выполняется из Python при старте).
-- PRAGMA foreign_keys = ON;

INSERT INTO master_classes (name, category, description, price, photo_url, date_time, max_participants)
VALUES
  ('Итальянская паста', 'Кулинария', 'Паста карбонара', 3500, '/static/photos/pasta.png', '2026-06-15 18:00:00', 10),
  ('Гончарное дело', 'Керамика', 'Чашка на круге', 2500, '/static/photos/ceramic.png', '2026-06-17 14:00:00', 6),
  ('Акварель для начинающих', 'Рисование', 'Пейзаж', 2000, '/static/photos/watercolor.png', '2026-06-20 11:00:00', 8);
