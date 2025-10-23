// tables.data.js
// Проценты считаются от контейнера-карты (absolute inset-0), чтобы масштабировалось.
window.HIKARI_TABLES = [
  // ЛЕВЫЙ НИЗ (ряд у окна/стены, горизонтальные 2-местные)
  { id: 1,  name: "L-B-1",  type: "2_horiz", capacity: 2, x: 25,  y: 94 },
  { id: 2,  name: "L-B-2",  type: "2_horiz", capacity: 2, x: 34,  y: 94 },
  { id: 3,  name: "L-B-3",  type: "2_horiz", capacity: 2, x: 43,  y: 94 },

  // ЛЕВАЯ СЕРЕДИНА (две колонны вертикальных 2-местных + 4-местные)
  { id: 3,  name: "L-2-1", type: "2_vert", capacity: 2, x: 15, y: 42 },

  // ЛЕВАЯ КОЛОННА 4-местных (красные прямоугольники)
  { id: 5, name: "L-4-1", type: "4", capacity: 4, x: 32, y: 78 },
  { id: 6, name: "L-4-2", type: "4", capacity: 4, x: 32, y: 62 },
  { id: 7, name: "L-4-2", type: "4", capacity: 4, x: 32, y: 46 },
  { id: 8, name: "L-4-1", type: "4", capacity: 4, x: 45, y: 78 },
  { id: 9, name: "L-4-2", type: "4", capacity: 4, x: 45, y: 62 },
  { id: 10, name: "L-4-2", type: "4", capacity: 4, x: 45, y: 46 },

  // ЦЕНТР — два длинных 6-местных (горизонтальные)
  { id: 11, name: "C-6-1", type: "6", capacity: 6, x: 60, y: 55 },
  { id: 12, name: "C-6-2", type: "6", capacity: 6, x: 72, y: 55 },
  { id: 13, name: "C-6-3", type: "6", capacity: 6, x: 60, y: 35 },

  // ПРАВЫЙ ВЕРХ — две группы 2-местных
  { id: 14, name: "R-2-1", type: "2_horiz", capacity: 2, x: 55, y: 15 },
  { id: 15, name: "R-2-2", type: "2_horiz", capacity: 2, x: 65, y: 15 },

  // РЯД БАРНЫХ СТУЛЬЕВ (низ справа)
  { id: 18, name: "BAR-1", type: "1", capacity: 1, x: 63, y: 68 },
  { id: 19, name: "BAR-2", type: "1", capacity: 1, x: 67, y: 68 },
  { id: 20, name: "BAR-3", type: "1", capacity: 1, x: 71, y: 68 },
  { id: 21, name: "BAR-4", type: "1", capacity: 1, x: 75, y: 68 },

  { id: 18, name: "BAR-1", type: "1", capacity: 1, x: 57, y: 75 },
  { id: 19, name: "BAR-2", type: "1", capacity: 1, x: 57, y: 82 },
  { id: 20, name: "BAR-3", type: "1", capacity: 1, x: 57, y: 89 },
  { id: 21, name: "BAR-4", type: "1", capacity: 1, x: 57, y: 96 },
];
