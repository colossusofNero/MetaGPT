Below is a structured example of a Node.js backend using Express.js designed to handle user authentication with JWT.

### File structure:
```
- /config
  - config.js
- /controllers
  - authController.js
- /routes
  - authRoutes.js
- /services
  - authService.js
- .env
- app.js
```

### Installation of necessary modules:
```bash
npm install express jsonwebtoken bcryptjs dotenv
```

### app.js
```javascript
const express = require('express');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Import routes
const authRoutes = require('./routes/authRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
```

### /config/config.js
```javascript
require('dotenv').config();

module.exports = {
  jwtSecret: process.env.JWT_SECRET || 'default_secret',
  jwtExpiration: '24h'
};
```

### /controllers/authController.js
```javascript
const authService = require('../services/authService');

exports.register = async (req, res) => {
  try {
    const { email, password } = req.body;
    const user = await authService.register(email, password);
    res.status(201).json({
      message: 'User registered successfully',
      user
    });
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
};

exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;
    const token = await authService.login(email, password);
    res.status(200).json({
      message: 'User logged in successfully',
      token
    });
  } catch (error) {
    res.status(401).json({ message: error.message });
  }
};
```

### /routes/authRoutes.js
```javascript
const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

router.post('/register', authController.register);
router.post('/login', authController.login);

module.exports = router;
```

### /services/authService.js
```javascript
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const config = require('../config/config');

// Simulated user database
const users = [];

exports.register = async (email, password) => {
  if (users.find(u => u.email === email)) {
    throw new Error('User already exists');
  }
  const hashedPassword = await bcrypt.hash(password, 10);
  const newUser = { email, password: hashedPassword };
  users.push(newUser);
  return newUser;
};

exports.login = async (email, password) => {
  const user = users.find(u => u.email === email);
  if (!user) {
    throw new Error('User does not exist');
  }
  const isMatch = await bcrypt.compare(password, user.password);
  if (!isMatch) {
    throw new Error('Incorrect password');
  }
  const token = jwt.sign({ email: user.email }, config.jwtSecret, { expiresIn: config.jwtExpiration });
  return token;
};
```

This codebase demonstrates how to structure an Express.js application for user authentication, using JWT for token management. Adjustments might be necessary depending on additional requirements or specific environmental constraints.