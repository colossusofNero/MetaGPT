```javascript
// Import necessary modules
const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const dotenv = require('dotenv');

// Initialize dotenv to use environment variables
dotenv.config();

// Create the Express app
const app = express();
app.use(express.json()); // Middleware to parse JSON

// User model (usually would interface with a database)
const users = [];

// Middleware to validate token
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (token == null) {
        return res.sendStatus(401);
    }

    jwt.verify(token, process.env.ACCESS_TOKEN_SECRET, (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
};

// Controller for user authentication
const authController = {
    async register(req, res) {
        try {
            const { username, password } = req.body;
            const hashedPassword = await bcrypt.hash(password, 10);
            const newUser = { username, password: hashedPassword };
            users.push(newUser);
            res.status(201).json({ message: "User created" });
        } catch (error) {
            res.status(500).json({ message: "Server error" });
        }
    },

    async login(req, res) {
        try {
            const { username, password } = req.body;
            const user = users.find(user => user.username === username);
            if (user == null) {
                return res.status(400).json({ message: "Cannot find user" });
            }
            if (await bcrypt.compare(password, user.password)) {
                const accessToken = jwt.sign({ username: user.username }, process.env.ACCESS_TOKEN_SECRET);
                res.json({ accessToken });
            } else {
                res.status(403).json({ message: "User authentication failed" });
            }
        } catch (error) {
            res.status(500).json({ message: "Server error" });
        }
    }
};

// Routes
const authRoutes = (app) => {
    app.post('/register', authController.register);
    app.post('/login', authController.login);
};

// Register the routes
authRoutes(app);

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});

```
This code defines a basic Express.js application with user registration and login functionalities using JWT for authentication. User details are stored in an array temporarily instead of a database. It uses bcrypt for password hashing and jwt for generating tokens.