```javascript
// index.js - Entry point of the application
require('dotenv').config();
const express = require('express');
const app = express();
const userRoutes = require('./routes/userRoutes');

app.use(express.json());

// User Routes
app.use('/api/users', userRoutes);

// Basic Error Handling
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send({
        success: false,
        message: 'Something broke!'
    });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

// routes/userRoutes.js
const express = require('express');
const router = express.Router();
const userController = require('../controllers/userController');

router.post('/login', userController.login);
router.post('/register', userController.register);

module.exports = router;

// controllers/userController.js
const userService = require('../services/userService');
const jwt = require('jsonwebtoken');

exports.login = async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = await userService.authenticate(email, password);
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Authentication failed.'
            });
        }

        const token = jwt.sign({ userId: user.id }, process.env.JWT_SECRET, {
            expiresIn: '1h'
        });

        res.json({
            success: true,
            message: 'Authentication successful!',
            token
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: error.message
        });
    }
};

exports.register = async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = await userService.createUser(email, password);
        res.status(201).json({
            success: true,
            message: 'User created successfully!',
            user
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            message: error.message
        });
    }
};

// services/userService.js
const bcrypt = require('bcrypt');

const users = []; // This should ideally be a database collection

exports.authenticate = async (email, password) => {
    const user = users.find(u => u.email === email);
    if (user && await bcrypt.compare(password, user.password)) {
        return user;
    }
    return null;
};

exports.createUser = async (email, password) => {
    const hashedPassword = await bcrypt.hash(password, 10);
    const newUser = {
        id: users.length + 1,
        email,
        password: hashedPassword
    };
    users.push(newUser);
    return newUser;
};
```
This code snippet is structured into an entry point `index.js`, routes in `userRoutes.js`, controllers in `userController.js`, and service logic in `userService.js`. It's essential to replace the array-based user storage with a proper database implementation for real-world applications.