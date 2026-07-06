use('ecommerce');

db.products.insertMany([
  {
    name: "Wireless Mouse",
    brand: "Logitech",
    price: 799,
    category: "Electronics",
    stock: 50,
    rating: 4.5
  },
  {
    name: "Mechanical Keyboard",
    brand: "Redragon",
    price: 2499,
    category: "Electronics",
    stock: 30,
    rating: 4.7
  },
  {
    name: "Gaming Headset",
    brand: "HyperX",
    price: 3999,
    category: "Electronics",
    stock: 20,
    rating: 4.6
  },
  {
    name: "USB-C Charger",
    brand: "Anker",
    price: 1499,
    category: "Accessories",
    stock: 75,
    rating: 4.4
  },
  {
    name: "External SSD",
    brand: "Samsung",
    price: 6999,
    category: "Storage",
    stock: 15,
    rating: 4.8
  },
  {
    name: "Laptop Stand",
    brand: "Portronics",
    price: 999,
    category: "Accessories",
    stock: 40,
    rating: 4.3
  },
  {
    name: "Webcam",
    brand: "Logitech",
    price: 2999,
    category: "Electronics",
    stock: 25,
    rating: 4.4
  },
  {
    name: "Power Bank",
    brand: "Mi",
    price: 1799,
    category: "Accessories",
    stock: 60,
    rating: 4.2
  }
]);