Below is a structured implementation for a Node.js backend using Express.js and JWT for user authentication. Here, we'll handle user signup and login functionality.

**File Structure:**
```
project_name/
│
├── node_modules/
│
├── src/
│   ├── controllers/
│   │   └── authController.js
│   ├── routes/
│   │   └── authRoutes.js
│   ├── services/
│   │   └── authService.js
│   ├── utils/
│   │   └── jwtHelper.js
│   └── app.js
│
├── .env
├── package.json
└── package-lock.json
```

### _1. Environment Setup (`dotenv` configuration)_

`.env`
```plaintext
PORT=3000
JWT_SECRET=your_jwt_secret_key
```

### _2. app.js_

```javascript
require('dotenv').config();
const express = require('express');
const authRoutes = require('./routes/authRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
```

### _3. authController.js_

```javascript
const authService = require('../services/authService');
const jwtHelper = require('../utils/jwtHelper');

// Sign up a new user
exports.signUp = async (req, res) => {
    try {
        const { username, password } = req.body;
        const user = await authService.createUser(username, password);
        res.status(201).json({ message: 'User created', user });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};

// Log in a user
exports.logIn = async (req, res) => {
    try {
        const { username, password } = req.body;
        const user = await authService.verifyUser(username, password);
        if (!user) {
            return res.status(401).json({ message: 'Authentication failed' });
        }
        const token = jwtHelper.generateToken(user.id);
        res.status(200).json({ message: 'Logged in successfully', token });
    } catch (error) {
        res.status(500).json({ message: error.message });
    }
};
```

### _4. authRoutes.js_

```javascript
const express = require('express');
const router = express.Router();
const authController = require('../controllers/authController');

router.post('/signup', authController.signUp);
router.post('/login', authController.logIn);

module.exports = router;
```

### _5. authService.js_

```javascript
// This is a dummy service to demonstrate the idea.
// In reality, you should integrate with a database.

const users = [];

exports.createUser = async (username, password) => {
    // Here you would save the user to a database and hash the password
    const user = { id: users.length + 1, username, password };
    users.push(user);
    return user;
};

exports.verifyUser = async (username, password) => {
    // Here you would look up the user in your database
    const user = users.find(u => u.username === username && u.password === password);
    return user;
};
```

### _6. jwtHelper.js_

```javascript
const jwt = require('jsonwebtoken');

exports.generateToken = (userId) => {
    return jwt.sign({ id: userId }, process.env.JWT_SECRET, { expiresIn: '2h' });
};
```

Remember to install the necessary npm modules (`express`, `jsonwebtoken`, `dotenv`) by running `npm install express jsonwebtoken dotenv`. Also, secure handling of passwords (e.g., hashing passwords with `bcryptjs`) should be implemented in a real-world application.